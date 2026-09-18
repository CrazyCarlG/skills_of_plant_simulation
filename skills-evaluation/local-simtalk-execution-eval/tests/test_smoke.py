#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Smoke test for the local-simtalk-execution evaluation framework.

Exercises every public module without needing a live Plant Simulation server.
Run from the eval directory:
    python3 tests/test_smoke.py

Exits 0 on success, 1 on first failure.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

# Make the eval package importable.
_HERE = Path(__file__).resolve()
_EVAL_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_EVAL_ROOT))

from eval.grader import (  # noqa: E402
    BUCKET_COMPILE_ERROR,
    BUCKET_RUNTIME_ERROR,
    BUCKET_TIMEOUT,
    ObservedRun,
    grade,
)
from eval.reporter import (  # noqa: E402
    aggregate,
    diff_snapshots,
    write_reports,
)
from eval.runner import TaskRunResult  # noqa: E402


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        print(f"FAIL: {msg}", file=sys.stderr)
        sys.exit(1)


def _check(condition: bool, label: str) -> None:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {label}")
    if not condition:
        sys.exit(1)


# --- Test 1: every task JSON file loads ---------------------------------------

def test_task_loading() -> None:
    print("Test 1 — task JSON loading")
    from eval.task import load_all_suites

    suite_dir = _EVAL_ROOT / "tasks"
    suites = load_all_suites(suite_dir)
    n_total = sum(s.n_tasks for s in suites)
    _check(n_total >= 30, f"loaded {n_total} tasks across {len(suites)} files (>=30)")

    # Spot-check: conn-001-ping must exist and be type=ping.
    all_tasks = [t for s in suites for t in s.tasks]
    conn001 = next((t for t in all_tasks if t.id == "conn-001-ping"), None)
    _check(conn001 is not None, "conn-001-ping exists")
    _check(conn001 is not None and conn001.type == "ping", "conn-001-ping is type=ping")
    _check(
        conn001 is not None and conn001.expected.exit_code == 0,
        "conn-001-ping expected exit_code=0",
    )

    # Spot-check: quirk-013 must be raw_socket mode (off-whitelist).
    q13 = next((t for t in all_tasks if t.id == "quirk-013-unknown-type-hangs"), None)
    _check(q13 is not None, "quirk-013-unknown-type-hangs exists")
    _check(
        q13 is not None and q13.mode == "raw_socket",
        "quirk-013 uses raw_socket mode",
    )

    # Spot-check: modal traps tagged expected_timeout.
    modal = [t for t in all_tasks if "modal-trap" in t.tags]
    _check(len(modal) >= 4, f">=4 modal-trap tasks ({len(modal)} found)")


# --- Test 2: grader classifies known good / known bad cases -------------------

def test_grader_classifies() -> None:
    print("\nTest 2 — grader classification")

    # Load tasks.
    from eval.task import load_all_suites
    suites = load_all_suites(_EVAL_ROOT / "tasks")
    tasks = {t.id: t for s in suites for t in s.tasks}

    # Case A: ping success → pass
    obs_ok = ObservedRun(
        task_id="conn-001-ping",
        iteration=1,
        exit_code=0,
        stdout='{"type":"ping","result":"success"}',
        wall_time_ms=120,
        parsed_json={"type": "ping", "result": "success"},
    )
    g = grade(tasks["conn-001-ping"], obs_ok)
    _check(g.verdict == "pass", f"ping success → pass (got {g.verdict})")
    _check(g.bucket == "pass", f"ping success bucket=pass (got {g.bucket})")

    # Case B: Quirk #7 — exit 11 with code execute failed log
    obs_q7 = ObservedRun(
        task_id="run-003-quirk7-runtime-unknown-identifier",
        iteration=1,
        exit_code=11,
        stdout=(
            '{"type":"action_result","action_id":"x","result":"success",'
            '"log":"code execute failed. error msg:Unknown identifier \'Foo\'"}'
        ),
        wall_time_ms=200,
        parsed_json={
            "type": "action_result",
            "action_id": "x",
            "result": "success",
            "log": "code execute failed. error msg:Unknown identifier 'Foo'",
        },
    )
    g = grade(tasks["run-003-quirk7-runtime-unknown-identifier"], obs_q7)
    _check(g.verdict == "pass", f"Quirk #7 detection → pass (got {g.verdict})")
    _check(g.bucket == BUCKET_RUNTIME_ERROR, f"Quirk #7 bucket=runtime_error (got {g.bucket})")

    # Case C: compile error (Q-001) — exit 10 with hasError log
    obs_q001 = ObservedRun(
        task_id="run-004-compile-error-division-by-zero",
        iteration=1,
        exit_code=10,
        stdout=(
            '{"type":"action_result","action_id":"y","result":"failed",'
            '"log":" hasError : division by zero (literal)"}'
        ),
        wall_time_ms=150,
        parsed_json={
            "type": "action_result",
            "action_id": "y",
            "result": "failed",
            "log": " hasError : division by zero (literal)",
        },
    )
    g = grade(tasks["run-004-compile-error-division-by-zero"], obs_q001)
    _check(g.verdict == "pass", f"Q-001 compile error → pass (got {g.verdict})")
    _check(g.bucket == BUCKET_COMPILE_ERROR, f"Q-001 bucket=compile_error (got {g.bucket})")

    # Case D: timeout (modal trap) — exit 1
    obs_t = ObservedRun(
        task_id="modal-001-prompt",
        iteration=1,
        exit_code=1,
        stdout="",
        stderr="TIMEOUT after 8000ms",
        wall_time_ms=8000,
    )
    g = grade(tasks["modal-001-prompt"], obs_t)
    _check(g.verdict == "pass", f"modal trap → pass (got {g.verdict})")
    _check(g.bucket == BUCKET_TIMEOUT, f"modal trap bucket=timeout (got {g.bucket})")

    # Case E: negation — happy syntax fails when response has hasError
    obs_neg = ObservedRun(
        task_id="syntax-001-valid-var",
        iteration=1,
        exit_code=0,
        stdout='{"type":"action_result","action_id":"z","result":" hasError : oops"}',
        wall_time_ms=100,
        parsed_json={"type": "action_result", "action_id": "z", "result": " hasError : oops"},
    )
    g = grade(tasks["syntax-001-valid-var"], obs_neg)
    _check(g.verdict == "fail", f"expected fail, got {g.verdict}")
    _check(len(g.failed_predicates) >= 1, f"failed_predicates populated (got {g.failed_predicates})")


# --- Test 3: aggregate + reporter end-to-end ----------------------------------

def test_aggregate_and_reporter() -> None:
    print("\nTest 3 — aggregate + reporter")
    from eval.task import load_all_suites
    suites = load_all_suites(_EVAL_ROOT / "tasks")
    all_tasks = [t for s in suites for t in s.tasks]

    # Build a synthetic TaskRunResult for each task with N=2 iterations.
    per_task: list[TaskRunResult] = []
    for t in all_tasks:
        result = TaskRunResult(task=t)
        for i in range(1, 3):
            obs = ObservedRun(
                task_id=t.id,
                iteration=i,
                exit_code=0,
                stdout="",
                wall_time_ms=100 + i,
            )
            result.observations.append(obs)
            result.grade_results.append(grade(t, obs))
        per_task.append(result)

    report = aggregate(per_task, iterations=2)
    _check(report.overall_n == len(all_tasks) * 2, f"overall_n = {report.overall_n}")
    _check(0.0 <= report.weighted_pass_rate <= 1.0, "pass rate in [0, 1]")

    # Write reports to a tempdir.
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        paths = write_reports(out, report, per_task)
        _check((out / "summary.md").exists(), "summary.md written")
        _check((out / "summary.json").exists(), "summary.json written")
        _check((out / "per-task").is_dir(), "per-task/ dir written")
        # snapshot file is the most recent snapshot-*.json
        snaps = list(out.glob("snapshot-*.json"))
        _check(len(snaps) == 1, f"snapshot file written (found {len(snaps)})")
        snap = json.loads(snaps[0].read_text(encoding="utf-8"))
        _check("tasks" in snap and len(snap["tasks"]) == len(all_tasks), "snapshot has all tasks")

        # Diff a snapshot against itself → no diff.
        diff = diff_snapshots(snap, snap)
        _check(diff["newly_passing"] == [], "diff against self: no newly passing")
        _check(diff["newly_failing"] == [], "diff against self: no newly failing")


# --- Test 4: stats sanity ----------------------------------------------------

def test_stats() -> None:
    print("\nTest 4 — stats")
    from eval.stats import compute_task_stats, weighted_pass_rate, wilson_ci

    # All pass.
    s = compute_task_stats("x", ["pass"] * 5, [100] * 5, "ping")
    _check(s.pass_rate == 1.0, "all-pass → 1.0")
    _check(s.is_flaky is False, "all-pass → not flaky")

    # Half pass.
    s = compute_task_stats("x", ["pass", "fail"] * 5, [100] * 10, "ping")
    _check(abs(s.pass_rate - 0.5) < 0.001, f"half-pass → 0.5 (got {s.pass_rate})")
    _check(s.is_flaky is True, "half-pass → flaky")

    # Wilson CI sanity.
    lo, hi = wilson_ci(0.5, 10)
    _check(0 < lo < 0.5 < hi < 1, f"Wilson CI sane: [{lo}, {hi}]")

    # Weighted rate.
    w = weighted_pass_rate([(1.0, 1.0), (1.0, 0.0)])
    _check(w == 0.5, f"weighted average = 0.5 (got {w})")


# --- Driver ------------------------------------------------------------------

def main() -> int:
    print(f"=== local-simtalk-execution-eval smoke test ===")
    print(f"eval root: {_EVAL_ROOT}\n")
    test_task_loading()
    test_grader_classifies()
    test_aggregate_and_reporter()
    test_stats()
    print("\nAll smoke tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())