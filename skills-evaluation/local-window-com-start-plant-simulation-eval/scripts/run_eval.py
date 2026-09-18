#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI entry for the local-window-com-start-plant-simulation evaluation
framework.

Usage:
    python3 scripts/run_eval.py [options]

Options:
    --suite PATH         Path to tasks/ directory (default: ./tasks)
    --config PATH        Path to .eval-config.yaml (default: ./.eval-config.yaml)
    --out PATH           Output directory for reports (default: ./reports)
    --tag TAG            Filter tasks by tag (e.g. smoke / lifeline-L1)
    --task-id SUBSTR     Filter tasks by id substring
    --iterations N       Override iterations per task (default from config)
    --mock               Use the fake win32com shim (no real PS needed)
    --compare OLD NEW    Diff two snapshot JSONs; produce regression report
    --verbose            Per-iteration progress output

Exit codes (see METHODOLOGY.md §6.3 / reporter.py):
    0  all CI gates pass
    1  overall weighted pass rate < 0.95
    2  one or more new flaky tasks
    3  hard-gate (lifeline / exit-code) regression
    4  CLI / task / config error
    5  unexpected exception
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Make the eval package importable when run as a script.
_HERE = Path(__file__).resolve()
_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_ROOT))

from eval.grader import grade  # noqa: E402
from eval.reporter import (  # noqa: E402
    aggregate,
    diff_snapshots,
    write_reports,
)
from eval.runner import (  # noqa: E402
    TaskRunResult,
    config_from_yaml,
    repo_root,
    resolve_script_path,
    run_all,
)
from eval.task import filter_suites, load_all_suites, load_suite  # noqa: E402


DEFAULT_CONFIG_PATH = _ROOT / ".eval-config.yaml"
DEFAULT_SUITE_PATH = _ROOT / "tasks"
DEFAULT_OUT_PATH = _ROOT / "reports"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="run_eval",
        description=(
            "Evaluate the local-window-com-start-plant-simulation skill."
        ),
    )
    p.add_argument("--suite", type=Path, default=DEFAULT_SUITE_PATH,
                   help=f"Tasks directory (default: {DEFAULT_SUITE_PATH})")
    p.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH,
                   help=f"Config YAML (default: {DEFAULT_CONFIG_PATH})")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT_PATH,
                   help=f"Report output directory (default: {DEFAULT_OUT_PATH})")
    p.add_argument("--tag", default=None,
                   help="Filter tasks by tag (e.g. smoke, lifeline-L1)")
    p.add_argument("--task-id", dest="task_id_substr", default=None,
                   help="Filter tasks by id substring")
    p.add_argument("--iterations", type=int, default=None,
                   help="Override iterations per task")
    p.add_argument("--mock", action="store_true",
                   help="Use the fake win32com shim (hermetic tasks only)")
    p.add_argument("--compare", nargs=2, type=Path, default=None, metavar=("OLD", "NEW"),
                   help="Diff two snapshot JSON files")
    p.add_argument("--verbose", action="store_true",
                   help="Per-iteration progress output")
    return p.parse_args(argv)


def cmd_compare(old: Path, new: Path) -> int:
    """Print regression diff between two snapshots."""
    if not old.exists() or not new.exists():
        print(f"ERR: missing snapshot file(s): old={old} new={new}", file=sys.stderr)
        return 4
    o = json.loads(old.read_text(encoding="utf-8"))
    n = json.loads(new.read_text(encoding="utf-8"))
    diff = diff_snapshots(o, n)
    print(json.dumps(diff, indent=2))
    if diff["newly_failing"] or diff["pass_rate_drops"]:
        return 3
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    """Load config + tasks, run, grade, write reports."""
    cfg_path: Path = args.config
    if not cfg_path.exists():
        print(f"ERR: config not found: {cfg_path}", file=sys.stderr)
        return 4
    cfg = config_from_yaml(cfg_path)
    if args.iterations is not None:
        cfg.iterations = args.iterations
    if args.mock:
        cfg.mock = True
    # Resolve script path against the eval dir's repo root if not absolute.
    if not cfg.script_path.is_absolute():
        cfg.script_path = (repo_root() / cfg.script_path).resolve()
    if not cfg.script_path.exists():
        print(f"ERR: skill script not found: {cfg.script_path}", file=sys.stderr)
        return 4
    print(f"[config] script={cfg.script_path}")
    print(f"[config] iterations={cfg.iterations} mock={cfg.mock}")
    print(f"[config] default_model={cfg.default_model!r}")
    print(f"[config] default_simtalkclaudefile={cfg.default_simtalkclaudefile!r}")
    print(f"[config] hard_gates={cfg.hard_gate_tags}")
    print(f"[config] pass_rate_threshold={cfg.pass_rate_threshold}")

    suite_dir: Path = args.suite
    if not suite_dir.exists():
        print(f"ERR: suite not found: {suite_dir}", file=sys.stderr)
        return 4
    if suite_dir.is_file():
        suites = [load_suite(suite_dir)]
    else:
        suites = load_all_suites(suite_dir)
    tasks = filter_suites(suites, tag=args.tag, task_id_substr=args.task_id_substr)
    # In mock mode, skip integration tasks (mock=False) — they need a real
    # Plant Simulation process and will always fail without one.
    if args.mock:
        before = len(tasks)
        tasks = [t for t in tasks if t.mock]
        skipped = before - len(tasks)
        if skipped:
            print(f"[tasks] {skipped} integration task(s) skipped in mock mode")
    if not tasks:
        print("ERR: no tasks matched the filter", file=sys.stderr)
        return 4
    print(f"[tasks] {len(tasks)} selected from {len(suites)} suite file(s)")

    def on_progress(task_id: str, done: int, total: int) -> None:
        if args.verbose or done in (0, total):
            print(f"[run] {done}/{total} {task_id}")

    per_task = run_all(cfg, tasks, on_progress=on_progress)

    # Grade.
    for r in per_task:
        assert isinstance(r, TaskRunResult)
        r.grade_results = [grade(r.task, o) for o in r.observations]

    # Aggregate + report.
    report = aggregate(
        per_task,
        cfg.iterations,
        pass_rate_threshold=cfg.pass_rate_threshold,
        hard_gate_tags=cfg.hard_gate_tags,
    )
    out_dir: Path = args.out
    paths = write_reports(out_dir, report, per_task)
    print("\n[reports]")
    for k, p in paths.items():
        print(f"  {k}: {p}")

    print(f"\n[gate] exit code {report.exit_gate_code}")
    print(
        f"  weighted_pass_rate={report.weighted_pass_rate:.4f} "
        f"(threshold {report.pass_rate_threshold:.2f})"
    )
    print(f"  n_flaky={report.n_flaky}")
    print(f"  n_hard_gate_regressions={report.n_hard_gate_regressions}")
    return report.exit_gate_code


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.compare is not None:
            return cmd_compare(args.compare[0], args.compare[1])
        return cmd_run(args)
    except Exception as e:  # noqa: BLE001
        import traceback
        print(f"ERR: unhandled exception: {type(e).__name__}: {e}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 5


if __name__ == "__main__":
    sys.exit(main())
