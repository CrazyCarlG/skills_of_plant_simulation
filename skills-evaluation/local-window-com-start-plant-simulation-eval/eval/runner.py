"""Runner: executes each task N times, captures observed runs.

Two execution modes:
    - real  (default)   subprocess.run() against the start_plant_simulation.py
                         script with the real `win32com.client` COM wire.
    - mock              injects a fake `win32com.client` (and `pywintypes`)
                         shim via PYTHONPATH; the script runs end-to-end
                         through argparse + validation + exit-code dispatch
                         without ever touching real COM.

Mock mode is the workhorse for hermetic tasks (CLI validation, exit code
matrix, COM error hints, lifelines L1/L3/L4/L6). It is NOT a real COM
replay — see METHODOLOGY.md §3.4.

The runner is deliberately simple — it does NOT grade. It returns raw
observations; eval.grader.grade() does the grading. This separation keeps
the runner easy to swap out (e.g., point at a different script).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .grader import ObservedRun
from .task import Task


# Default path to the skill under test (relative to repo root).
DEFAULT_SCRIPT_PATH = Path(
    "skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py"
).as_posix()


# Path to the mock shim (sibling of this module). The runner puts this
# directory on PYTHONPATH when task.mock is True.
# The shim is a directory whose top-level contains `win32com/` (a
# package with __init__.py + client.py) and `pywintypes.py` (a
# top-level module).
MOCK_SHIM_DIRNAME = "_shims"


@dataclass
class RunConfig:
    """How to invoke the runner."""

    script_path: Path
    iterations: int = 3
    mock: bool = False
    extra_timeout_buffer_s: float = 5.0
    default_model: str = ""        # used to fill --model if a task omits it
    default_simtalkclaudefile: str = ""  # used to fill --simtalkclaudefile
    pass_rate_threshold: float = 0.95
    # If set, force this Python interpreter (else use sys.executable).
    python: str | None = None
    # Tags for tasks that must hit 100% pass rate (lifelines + exit codes).
    hard_gate_tags: list[str] = field(default_factory=list)

    @classmethod
    def from_yaml(cls, d: dict[str, Any]) -> "RunConfig":
        return cls(
            script_path=Path(d.get("script_path", DEFAULT_SCRIPT_PATH)),
            iterations=int(d.get("iterations", 3)),
            mock=bool(d.get("mock", False)),
            default_model=d.get("default_model", ""),
            default_simtalkclaudefile=d.get("default_simtalkclaudefile", ""),
            pass_rate_threshold=float(d.get("pass_rate_threshold", 0.95)),
            hard_gate_tags=list(d.get("hard_gates", [])),
        )


@dataclass
class TaskRunResult:
    """All observed runs + verdicts for one task across N iterations."""

    task: Task
    observations: list[ObservedRun] = field(default_factory=list)
    grade_results: list = field(default_factory=list)  # list[GraderResult]

    @property
    def n_iterations(self) -> int:
        return len(self.observations)


# --- Command construction ----------------------------------------------------


def _fill_defaults(cfg: RunConfig, task: Task) -> list[str]:
    """Inject default --model / --simtalkclaudefile if a task omitted them.

    Many hermetic tasks deliberately omit one or both (e.g., to test
    "missing --simtalkclaudefile"). We only fill when the arg is not
    already present and not part of the test.

    For cli-validation tasks, we still fill the *other* required arg so
    the script can reach the dimension under test. E.g., a task that
    tests "model file not found" must still have --simtalkclaudefile
    present, or argparse will reject the args before the file check runs.
    """
    args = list(task.args)
    if not getattr(task, "fill_defaults", True):
        # Task explicitly opts out of default injection (e.g. to test
        # argparse-level "missing required arg" behavior).
        return args
    has_m = "-m" in args or "--model" in args
    has_s = "-s" in args or "--simtalkclaudefile" in args
    if task.category == "cli-validation":
        # Fill whichever of -m / -s is missing, so the script can reach
        # the dimension under test.
        if cfg.default_model and not has_m:
            args = ["-m", cfg.default_model, *args]
            has_m = True
        if cfg.default_simtalkclaudefile and not has_s:
            args = ["-s", cfg.default_simtalkclaudefile, *args]
            has_s = True
    else:
        if cfg.default_model and not has_m:
            args = ["-m", cfg.default_model, *args]
        if cfg.default_simtalkclaudefile and not has_s:
            args = ["-s", cfg.default_simtalkclaudefile, *args]
    return args


def _build_command(cfg: RunConfig, task: Task) -> list[str]:
    """Build the subprocess command for one task."""
    py = cfg.python or sys.executable
    cmd = [py, str(cfg.script_path), *_fill_defaults(cfg, task)]
    return cmd


# --- Mock shim discovery -----------------------------------------------------


def _mock_shim_dir() -> Path:
    """Path to the bundled _mock_win32com shim (sibling of this module)."""
    return Path(__file__).resolve().parent / MOCK_SHIM_DIRNAME


def _ensure_mock_shim() -> Path:
    """Verify the mock shim is on disk; raise if missing.

    The shim is a directory containing `win32com/` and `pywintypes.py`.
    The runner puts this directory on the subprocess's PYTHONPATH so
    that `import win32com.client` and `import pywintypes` resolve to
    the shims.
    """
    p = _mock_shim_dir()
    if not p.is_dir():
        raise FileNotFoundError(
            f"Mock shim not found at {p}. Expected eval/{MOCK_SHIM_DIRNAME}/"
        )
    if not (p / "win32com" / "__init__.py").exists():
        raise FileNotFoundError(
            f"Mock shim incomplete: {p}/win32com/__init__.py missing"
        )
    if not (p / "pywintypes.py").exists():
        raise FileNotFoundError(
            f"Mock shim incomplete: {p}/pywintypes.py missing"
        )
    return p


# --- Real run ----------------------------------------------------------------


def _read_mock_log(mock_log_path: Path) -> tuple[list[str], str | None]:
    """Read the recorded mock call sequence + any shim error from the
    JSON file the shim writes to MOCK_LOG_PATH.

    Returns:
        (call_sequence, setup_error)
    """
    if not mock_log_path.exists():
        return [], "mock log file not written"
    try:
        raw = json.loads(mock_log_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return [], f"mock log read failed: {e}"
    if not isinstance(raw, dict):
        return [], f"mock log shape invalid: {type(raw).__name__}"
    setup_error = raw.get("setup_error")
    calls = raw.get("calls", [])
    if not isinstance(calls, list):
        return [], f"mock calls shape invalid: {type(calls).__name__}"
    return [str(c) for c in calls], setup_error


def _run_real(cfg: RunConfig, task: Task, iteration: int) -> ObservedRun:
    """One real subprocess call against start_plant_simulation.py."""
    cmd = _build_command(cfg, task)
    env = dict(os.environ)
    env.update(task.env)
    cwd = task.cwd

    # If mock mode, point PYTHONPATH at the shim and tell the shim where to
    # write the call log.
    mock_log: Path | None = None
    mock_faults_file: Path | None = None
    if task.mock:
        try:
            shim_dir = _ensure_mock_shim()
        except FileNotFoundError as e:
            return ObservedRun(
                task_id=task.id,
                iteration=iteration,
                exit_code=None,
                raw_error=str(e),
                command=cmd,
            )
        mock_log = Path(tempfile_for_iteration(task.id, iteration))
        env["PYTHONPATH"] = str(shim_dir) + os.pathsep + env.get("PYTHONPATH", "")
        env["EVAL_MOCK_LOG"] = str(mock_log)

        # Tell the shim to treat the configured default paths as existing
        # (so hermetic tasks don't need real .spp / .pslib on disk).
        # Tasks can opt in to additional stub-accepted paths via
        # `extra_mock_paths` (e.g. inject-003 with a path containing a
        # quote that shouldn't be treated as "missing").
        substrs: list[str] = []
        if cfg.default_model:
            substrs.extend([cfg.default_model, str(Path(cfg.default_model)), Path(cfg.default_model).name])
        if cfg.default_simtalkclaudefile:
            substrs.extend([cfg.default_simtalkclaudefile, str(Path(cfg.default_simtalkclaudefile)), Path(cfg.default_simtalkclaudefile).name])
        for p in getattr(task, "extra_mock_paths", []) or []:
            substrs.extend([p, str(Path(p)), Path(p).name])
        if substrs:
            # Dedup while preserving order.
            seen: set[str] = set()
            deduped: list[str] = []
            for s in substrs:
                if s and s not in seen:
                    seen.add(s)
                    deduped.append(s)
            env["EVAL_MOCK_PATHS_AS_EXISTING"] = ";".join(deduped)

        # If the task declares mock_setup, write it to a temp file and
        # point the shim at it via EVAL_MOCK_FAULTS.
        if task.mock_setup:
            import tempfile
            fd, path = tempfile.mkstemp(
                prefix=f"faults_{task.id}_{iteration}_", suffix=".json"
            )
            os.close(fd)
            Path(path).write_text(
                json.dumps(task.mock_setup, indent=2), encoding="utf-8"
            )
            mock_faults_file = Path(path)
            env["EVAL_MOCK_FAULTS"] = str(mock_faults_file)

    wall_start = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=task.timeout + cfg.extra_timeout_buffer_s,
            env=env,
            cwd=cwd,
        )
        wall_ms = int((time.monotonic() - wall_start) * 1000)
        obs = ObservedRun(
            task_id=task.id,
            iteration=iteration,
            exit_code=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            wall_time_ms=wall_ms,
            command=cmd,
        )
    except subprocess.TimeoutExpired:
        wall_ms = int((time.monotonic() - wall_start) * 1000)
        obs = ObservedRun(
            task_id=task.id,
            iteration=iteration,
            exit_code=None,
            stdout="",
            stderr=f"TIMEOUT after {wall_ms}ms (subprocess timeout)",
            wall_time_ms=wall_ms,
            raw_error="subprocess_timeout",
            command=cmd,
        )
    except FileNotFoundError as e:
        return ObservedRun(
            task_id=task.id,
            iteration=iteration,
            exit_code=None,
            raw_error=f"file_not_found: {e}",
            command=cmd,
        )
    except Exception as e:  # noqa: BLE001
        return ObservedRun(
            task_id=task.id,
            iteration=iteration,
            exit_code=None,
            raw_error=f"runner_exception: {type(e).__name__}: {e}",
            command=cmd,
        )

    # Attach mock metadata if applicable.
    if mock_log is not None:
        calls, setup_err = _read_mock_log(mock_log)
        obs.mock_calls = calls
        obs.mock_setup_error = setup_err
        # Best-effort cleanup of the per-iteration log.
        try:
            mock_log.unlink()
        except OSError:
            pass
    if mock_faults_file is not None:
        try:
            mock_faults_file.unlink()
        except OSError:
            pass

    return obs


# --- Mock run (synthesized) --------------------------------------------------


def _run_mock(cfg: RunConfig, task: Task, iteration: int) -> ObservedRun:
    """Synthesize an ObservedRun from task.fixture for offline testing.

    Used only when the runner is invoked with --mock AND a task declares
    `mock: true` AND supplies a `fixture` dict. Without a fixture, even
    mock-flagged tasks go through _run_real (which loads the shim).
    """
    fix = task.fixture if isinstance(task, dict) else None
    # NOTE: `task` here is the dataclass; fixtures are normally not used
    # in this skill's eval — the shim covers everything. Kept for symmetry
    # with the simtalk-execution eval.
    return ObservedRun(
        task_id=task.id,
        iteration=iteration,
        exit_code=0,
        stdout="",
        stderr="",
        wall_time_ms=5,
        command=["<fixture>"],
    )


def tempfile_for_iteration(task_id: str, iteration: int) -> str:
    """Path to the per-iteration mock log file (in the OS temp dir)."""
    import tempfile
    fd, path = tempfile.mkstemp(prefix=f"eval_{task_id}_{iteration}_", suffix=".json")
    os.close(fd)
    return path


# --- Driver ------------------------------------------------------------------


def run_task(cfg: RunConfig, task: Task) -> TaskRunResult:
    """Execute one task cfg.iterations times, return observations."""
    out = TaskRunResult(task=task)
    for i in range(1, cfg.iterations + 1):
        out.observations.append(_run_real(cfg, task, i))
    return out


def run_all(
    cfg: RunConfig,
    tasks: list[Task],
    on_progress: Callable[[str, int, int], None] | None = None,
) -> list[TaskRunResult]:
    """Run every task in sequence; optional on_progress(task_id, done, total)."""
    results: list[TaskRunResult] = []
    total = len(tasks)
    for idx, task in enumerate(tasks, start=1):
        if on_progress:
            on_progress(task.id, idx - 1, total)
        results.append(run_task(cfg, task))
    if on_progress:
        on_progress("<done>", total, total)
    return results


# --- Config loading helpers --------------------------------------------------


def _find_repo_root(start: Path) -> Path | None:
    """Walk up looking for a git repo root."""
    cur = start.resolve()
    for p in [cur, *cur.parents]:
        if (p / ".git").exists() or (p / "pyproject.toml").exists():
            return p
    return None


def repo_root() -> Path:
    """Best-effort repo root resolution; falls back to cwd."""
    here = Path(__file__).resolve()
    found = _find_repo_root(here)
    return found if found else Path.cwd()


def resolve_script_path(repo_root_path: Path | None = None) -> Path:
    """Resolve the default start_plant_simulation.py path under repo_root."""
    rr = repo_root_path or repo_root()
    return rr / "skills" / "local-window-com-start-plant-simulation" / "scripts" / "start_plant_simulation.py"


def config_from_yaml(path: Path) -> RunConfig:
    """Tiny YAML reader — only flat key:value with strings/ints/booleans.

    We deliberately don't pull in PyYAML to keep this framework
    dependency-free. List values (e.g., hard_gates) are parsed as
    bracketed `[a, b, c]` lines.
    """
    raw = path.read_text(encoding="utf-8")
    out: dict[str, Any] = {}
    list_key: str | None = None
    for ln in raw.splitlines():
        s = ln.rstrip()
        stripped = s.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if list_key is not None:
            # Inside a list block.
            if s.startswith("  - ") or s.startswith("- "):
                item = s.lstrip("- ").strip().strip('"').strip("'")
                out.setdefault(list_key, []).append(item)
                continue
            else:
                list_key = None
        if ":" not in s:
            continue
        k, v = s.split(":", 1)
        k = k.strip()
        v = v.strip()
        if not v:
            # Could be start of a list block.
            list_key = k
            out.setdefault(k, [])
            continue
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1]
            items = [x.strip().strip('"').strip("'") for x in inner.split(",") if x.strip()]
            out[k] = items
            continue
        v = v.strip('"').strip("'")
        if v.lower() in ("true", "false"):
            out[k] = v.lower() == "true"
        elif v.lstrip("-").isdigit():
            out[k] = int(v)
        else:
            try:
                out[k] = float(v)
            except ValueError:
                out[k] = v
    if "script_path" in out:
        out["script_path"] = Path(out["script_path"])
    return RunConfig.from_yaml(out)
