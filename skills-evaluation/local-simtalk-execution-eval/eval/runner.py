"""Runner: executes each task N times, captures observed runs.

Two modes:
    - real (default)   subprocess.run() against skills/local-simtalk-execution/scripts/simtalk_send.py
    - mock             uses task.fixture to synthesize a response (for offline dev / CI without PS)

The runner is deliberately simple — it does NOT grade. It returns raw
observations; eval.grader.grade() does the grading. This separation keeps the
runner easy to swap out (e.g., point at a different socket_client).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .grader import ObservedRun
from .task import Task


# Default path to the skill under test (relative to repo root).
DEFAULT_SIMTALK_SEND = Path(
    "skills/local-simtalk-execution/scripts/simtalk_send.py"
).as_posix()


@dataclass
class RunConfig:
    """How to invoke the runner."""

    simtalk_send_path: Path
    host: str = "host.docker.internal"
    port: int = 50007
    iterations: int = 5
    mock: bool = False
    extra_timeout_buffer_s: float = 5.0
    # If set, force this Python interpreter (else use sys.executable).
    python: str | None = None

    @classmethod
    def from_yaml(cls, d: dict[str, Any]) -> "RunConfig":
        return cls(
            simtalk_send_path=Path(
                d.get("simtalk_send_path", DEFAULT_SIMTALK_SEND)
            ).resolve(),
            host=d.get("host", "host.docker.internal"),
            port=int(d.get("port", 50007)),
            iterations=int(d.get("iterations", 5)),
            mock=bool(d.get("mock", False)),
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


# Path to the low-level socket client (Quirk #13 needs this).
DEFAULT_SOCKET_CLIENT = Path(
    "skills/local-simtalk-execution/scripts/socket_client.py"
).as_posix()


def _build_command(
    cfg: RunConfig,
    task: Task,
) -> list[str]:
    """Build the subprocess command for one task.

    Dispatches on task.mode:
        "high_level" (default): simtalk_send.py with the matching subcommand.
        "raw_socket":          socket_client.py with the raw --data payload
                               (used for Quirk #13 / off-whitelist type testing).
    """
    py = cfg.python or sys.executable
    if task.mode == "raw_socket":
        # socket_client.py lives next to simtalk_send.py.
        client_path = cfg.simtalk_send_path.parent / "socket_client.py"
        cmd = [
            py,
            str(client_path),
            "--host", cfg.host,
            "--port", str(cfg.port),
            "--timeout", str(task.timeout),
            "--data", task.raw_data or "",
        ]
        # Optional response-mode overrides (default: delimiter ||END||).
        resp_mode = task.raw_resp_mode or "delimiter"
        cmd.extend(["--resp-mode", resp_mode])
        if resp_mode == "delimiter" and task.raw_resp_arg:
            cmd.extend(["--resp-delimiter", task.raw_resp_arg])
        elif resp_mode == "delimiter":
            cmd.extend(["--resp-delimiter", "||END||"])
        elif resp_mode == "fixed" and task.raw_resp_arg:
            cmd.extend(["--resp-fixed", task.raw_resp_arg])
        return cmd

    # High-level mode (default).
    cmd = [
        py,
        str(cfg.simtalk_send_path),
        "--host", cfg.host,
        "--port", str(cfg.port),
        "--timeout", str(task.timeout),
    ]
    # Subcommand per type.
    if task.type == "ping":
        cmd.append("ping")
    elif task.type == "simtalk_syntax":
        cmd.append("syntax")
        cmd.append(task.code or "")
        if task.context_path:
            cmd.extend(["--target-path", task.context_path])
    elif task.type == "simtalk_run":
        cmd.append("run")
        cmd.append(task.code or "")
        if task.context_path:
            cmd.extend(["--context-path", task.context_path])
    elif task.type == "readlog":
        cmd.append("readlog")
    return cmd


def _try_parse_json(stdout: str) -> dict[str, Any] | None:
    """Tolerant JSON parse; simtalk_send prints the raw reply line."""
    if not stdout:
        return None
    # Strip trailing whitespace/newlines.
    s = stdout.strip()
    if not s or not s.startswith("{"):
        return None
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None


def _run_real(cfg: RunConfig, task: Task, iteration: int) -> ObservedRun:
    """One real subprocess call against simtalk_send.py."""
    cmd = _build_command(cfg, task)
    wall_start = time.monotonic()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=task.timeout + cfg.extra_timeout_buffer_s,
        )
        wall_ms = int((time.monotonic() - wall_start) * 1000)
        return ObservedRun(
            task_id=task.id,
            iteration=iteration,
            exit_code=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            wall_time_ms=wall_ms,
            parsed_json=_try_parse_json(proc.stdout or ""),
            command=cmd,
        )
    except subprocess.TimeoutExpired:
        wall_ms = int((time.monotonic() - wall_start) * 1000)
        return ObservedRun(
            task_id=task.id,
            iteration=iteration,
            exit_code=1,  # subprocess timeout -> exit 1 per socket_client.py §9
            stdout="",
            stderr=f"TIMEOUT after {wall_ms}ms",
            wall_time_ms=wall_ms,
            parsed_json=None,
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
    except Exception as e:  # noqa: BLE001 — surface any other runner error
        return ObservedRun(
            task_id=task.id,
            iteration=iteration,
            exit_code=None,
            raw_error=f"runner_exception: {type(e).__name__}: {e}",
            command=cmd,
        )


def _run_mock(cfg: RunConfig, task: Task, iteration: int) -> ObservedRun:
    """Synthesize a response from task.fixture for offline testing.

    The fixture schema mirrors the observed subprocess output:
        {
          "exit_code": 0,
          "stdout": "...",         # gets parsed as JSON if it parses
          "stderr": "...",
          "wall_time_ms": 42
        }
    """
    fix = task.fixture or {}
    stdout = fix.get("stdout", "")
    stderr = fix.get("stderr", "")
    exit_code = int(fix.get("exit_code", 0))
    wall_ms = int(fix.get("wall_time_ms", 5))
    return ObservedRun(
        task_id=task.id,
        iteration=iteration,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        wall_time_ms=wall_ms,
        parsed_json=_try_parse_json(stdout),
        command=["<mock>"],
    )


def run_task(cfg: RunConfig, task: Task) -> TaskRunResult:
    """Execute one task cfg.iterations times, return observations."""
    runner = _run_mock if cfg.mock else _run_real
    out = TaskRunResult(task=task)
    for i in range(1, cfg.iterations + 1):
        out.observations.append(runner(cfg, task, i))
    return out


def run_all(
    cfg: RunConfig,
    tasks: list[Task],
    on_progress=None,
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


# --- Pretty config loading ----------------------------------------------------

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


def resolve_simtalk_send_path(repo_root_path: Path | None = None) -> Path:
    """Resolve the default simtalk_send.py path under repo_root."""
    rr = repo_root_path or repo_root()
    return rr / "skills" / "local-simtalk-execution" / "scripts" / "simtalk_send.py"


def config_from_yaml(path: Path) -> RunConfig:
    """Tiny YAML reader — only flat key:value with strings/ints/booleans.

    We deliberately don't pull in PyYAML to keep this framework dependency-free.
    """
    raw = path.read_text(encoding="utf-8")
    out: dict[str, Any] = {}
    for ln in raw.splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        if ":" not in s:
            continue
        k, v = s.split(":", 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        if v.lower() in ("true", "false"):
            out[k] = v.lower() == "true"
        elif v.isdigit():
            out[k] = int(v)
        else:
            try:
                out[k] = float(v)
            except ValueError:
                out[k] = v
    if "simtalk_send_path" in out:
        out["simtalk_send_path"] = Path(out["simtalk_send_path"])
    return RunConfig.from_yaml(out)