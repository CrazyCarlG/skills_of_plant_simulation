#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for per-task wall-time budgets (METHODOLOGY.md §2.3 / §3.3).

The eval already has a `wall_time_max_ms` predicate on each task's
`expected` block (enforced by the grader) and TYPE_MEDIAN_BUDGET_MS in
eval/stats.py for the per-type `is_slow` flag. This test suite enforces
the per-task budget feature:

    budget-001  Every task JSON file declares `wall_time_max_ms` on
                each task's expected block.
    budget-002  Every declared budget is a positive integer (>= 100ms,
                <= 10 minutes — a sanity range; the budgets are meant
                to flag *catastrophic* regressions, not microsecond
                jitter).
    budget-003  Budgets are consistent with their task's `type` — i.e.,
                a budget is no more than 10× the type's
                TYPE_MEDIAN_BUDGET_MS in eval/stats.py. For
                expected-timeout tasks the budget can exceed this since
                the runner is *designed* to wait for timeout; we use a
                60s ceiling to accommodate any task.
    budget-004  The eval.reporter.AggregateReport dataclass exposes a
                `n_over_budget` field and the JSON summary contains it.
    budget-005  The eval.stats.TaskStats dataclass exposes
                `budget_ms` + `is_over_budget` fields, and
                `compute_task_stats` threads `task_budget_ms` through.
    budget-006  The reporter's render_summary_md surfaces both a
                "Budget ms" and an "Over" column, plus an
                "Over-budget tasks" summary line.
    budget-007  The reporter's render_per_task_md surfaces the
                "Wall-time budget" line (info-only).

The budgets are info-only — they do NOT contribute to the CI gate
(METHODOLOGY.md §5.3). These tests therefore only assert schema
and reasonableness, never that all budgets are met. A future check that
the mock eval gate's n_over_budget stays 0 lives in test_mock_eval_gate.py
(or runs the eval end-to-end).
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve()
_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_ROOT))

from eval.stats import TYPE_MEDIAN_BUDGET_MS, TaskStats, compute_task_stats  # noqa: E402
from eval.reporter import AggregateReport, render_per_task_md, render_summary_md  # noqa: E402
from eval.task import load_all_suites  # noqa: E402


TASKS_DIR = _ROOT / "tasks"
MIN_BUDGET_MS = 100           # below this is unrealistic for any task
MAX_BUDGET_MS = 10 * 60_000   # 10 minutes — beyond this is a typo


def _all_tasks() -> list:
    """Flat list of (suite_file, task_dict) tuples — raw, not yet typed."""
    out: list = []
    for p in sorted(TASKS_DIR.glob("*.json")):
        raw = json.loads(p.read_text(encoding="utf-8"))
        for t in raw.get("tasks", []):
            t["_suite_file"] = p.name
            out.append(t)
    return out


class TestTimeBudgets(unittest.TestCase):
    """Every golden task must declare a wall-time budget."""

    def test_budget_001_every_task_has_budget(self):
        missing: list[str] = []
        for t in _all_tasks():
            expected = t.get("expected") or {}
            if "wall_time_max_ms" not in expected:
                missing.append(f"{t.get('id')} ({t.get('_suite_file')})")
        self.assertEqual(
            missing,
            [],
            f"{len(missing)} task(s) missing expected.wall_time_max_ms. "
            "Add a budget so the report's 'Over' column has a value. "
            f"Missing: {missing[:5]}...",
        )

    def test_budget_002_budgets_are_positive_ints_in_range(self):
        bad: list[tuple[str, object]] = []
        for t in _all_tasks():
            expected = t.get("expected") or {}
            b = expected.get("wall_time_max_ms")
            if not isinstance(b, int) or isinstance(b, bool):
                bad.append((t.get("id"), f"not int: {b!r}"))
                continue
            if b < MIN_BUDGET_MS or b > MAX_BUDGET_MS:
                bad.append((t.get("id"), f"out of range [{MIN_BUDGET_MS},{MAX_BUDGET_MS}]: {b}"))
        self.assertEqual(
            bad,
            [],
            f"{len(bad)} task(s) have unrealistic budgets: {bad[:5]}...",
        )

    def test_budget_003_budgets_consistent_with_type(self):
        """A task's budget must be no more than 10× the type's
        TYPE_MEDIAN_BUDGET_MS in eval/stats.py. Expected-timeout tasks
        (timeout <= 10s) and getFilesOfFolder-driven tasks are exempt:
        their wall_time_ms equals task.timeout (the runner is designed to
        wait it out), so the budget legitimately exceeds the type median
        by more than 10×."""
        # Types exempt from the 10× rule: ping (overhead-bound), and
        # simtalk_run/simtalk_syntax when tagged 'expected_timeout' (the
        # runner is designed to hit the timeout) or 'list-api'
        # (getFilesOfFolder can be slow on large dirs).
        EXEMPT_TAGS = {"expected_timeout", "list-api"}
        bad: list[tuple[str, str, int, int]] = []
        for t in _all_tasks():
            expected = t.get("expected") or {}
            b = expected.get("wall_time_max_ms")
            if b is None:
                continue
            tags = set(t.get("tags") or [])
            task_type = t.get("type", "")
            if task_type == "ping" or (tags & EXEMPT_TAGS):
                continue  # budget is timeout-driven, not type-driven
            type_median = TYPE_MEDIAN_BUDGET_MS.get(task_type)
            if type_median is None:
                continue
            ceiling = 10 * type_median
            if b > ceiling:
                bad.append((
                    t.get("id"),
                    f"budget > 10× type median ({type_median})",
                    b,
                    ceiling,
                ))
        self.assertEqual(
            bad,
            [],
            f"{len(bad)} task(s) have budgets inconsistent with their type. "
            f"First few: {bad[:5]}",
        )

    def test_budget_004_aggregate_report_has_n_over_budget(self):
        """Schema smoke test: AggregateReport must carry n_over_budget
        so the JSON summary + markdown report can surface it."""
        rep = AggregateReport(
            timestamp="2026-09-18T00:00:00Z",
            iterations=1,
            per_task=[],
            per_task_results=[],
            bucket_hist={},
            weighted_pass_rate=1.0,
            overall_n=0,
            overall_n_pass=0,
            n_flaky=0,
            n_slow=0,
            n_quirk_regressions=0,
            n_over_budget=0,
            exit_gate_code=0,
        )
        d = rep.to_dict()
        self.assertIn("n_over_budget", d)
        self.assertEqual(d["n_over_budget"], 0)

    def test_budget_005_task_stats_has_budget_fields(self):
        """compute_task_stats must thread task_budget_ms through to
        TaskStats.budget_ms + is_over_budget."""
        # 1. No budget → budget_ms is None, is_over_budget is False.
        ts = compute_task_stats(
            task_id="t1",
            verdicts=["pass"],
            wall_times_ms=[100],
            task_type="ping",
        )
        self.assertIsNone(ts.budget_ms)
        self.assertFalse(ts.is_over_budget)
        d = ts.to_dict()
        self.assertIn("budget_ms", d)
        self.assertIn("is_over_budget", d)

        # 2. Budget set + median <= budget → not over budget.
        ts2 = compute_task_stats(
            task_id="t2",
            verdicts=["pass"],
            wall_times_ms=[100, 110, 120],
            task_type="ping",
            task_budget_ms=500,
        )
        self.assertEqual(ts2.budget_ms, 500)
        self.assertFalse(ts2.is_over_budget)

        # 3. Budget set + median > budget → over budget (info-only flag).
        ts3 = compute_task_stats(
            task_id="t3",
            verdicts=["pass"],
            wall_times_ms=[9000, 9100, 9200],
            task_type="simtalk_run",
            task_budget_ms=1000,
        )
        self.assertEqual(ts3.budget_ms, 1000)
        self.assertTrue(ts3.is_over_budget)
        self.assertIn("is_over_budget", ts3.to_dict())

        # 4. is_slow is unaffected by task_budget_ms — it's type-driven.
        ts4 = compute_task_stats(
            task_id="t4",
            verdicts=["pass"],
            wall_times_ms=[60_000, 60_100, 60_200],
            task_type="simtalk_run",
            task_budget_ms=70_000,  # would not be over budget
        )
        # TYPE_MEDIAN_BUDGET_MS["simtalk_run"] = 30_000; is_slow is med > 2*30_000
        self.assertTrue(ts4.is_slow)
        self.assertFalse(ts4.is_over_budget)  # 60_100 < 70_000

    def test_budget_006_render_summary_md_has_budget_columns(self):
        """render_summary_md must surface Budget + Over columns + an
        'Over-budget tasks' summary line."""
        ts = TaskStats(
            task_id="probe-task",
            n=3,
            n_pass=3,
            pass_rate=1.0,
            median_wall_ms=400,
            mean_wall_ms=400.0,
            stddev_wall_ms=10.0,
            ci95_lo=1.0,
            ci95_hi=1.0,
            is_flaky=False,
            is_slow=False,
            budget_ms=3000,
            is_over_budget=False,
        )

        # Minimal stub for per_task_results (only .task.type is read).
        from dataclasses import dataclass, field
        from eval.task import Expected

        @dataclass
        class _StubObs:
            iteration: int = 1
            exit_code: int = 0
            stdout: str = ""
            stderr: str = ""
            wall_time_ms: int = 400
            raw_error: str | None = None

        @dataclass
        class _StubGrade:
            verdict: str = "pass"
            bucket: str = "pass"
            failed_predicates: list = field(default_factory=list)
            notes: str = ""

        @dataclass
        class _StubTask:
            id: str = "probe-task"
            category: str = "syntax"
            name: str = "probe"
            type: str = "ping"
            timeout: int = 5
            weight: float = 1.0
            tags: list = field(default_factory=list)
            code: str | None = None
            context_path: str | None = None
            fixture: dict | None = None
            mode: str = "high_level"
            raw_data: str | None = None
            raw_resp_mode: str | None = None
            raw_resp_arg: str | None = None

        task = _StubTask()
        task.expected = Expected(wall_time_max_ms=3000)

        @dataclass
        class _StubResult:
            task: object = None
            observations: list = field(default_factory=list)
            grade_results: list = field(default_factory=list)

        result = _StubResult(
            task=task,
            observations=[_StubObs()],
            grade_results=[_StubGrade()],
        )

        rep = AggregateReport(
            timestamp="2026-09-18T00:00:00Z",
            iterations=3,
            per_task=[ts],
            per_task_results=[result],
            bucket_hist={},
            weighted_pass_rate=1.0,
            overall_n=3,
            overall_n_pass=3,
            n_flaky=0,
            n_slow=0,
            n_quirk_regressions=0,
            n_over_budget=0,
            exit_gate_code=0,
        )

        md = render_summary_md(rep)
        # Header columns include Budget + Over.
        self.assertRegex(md, r"\|\s*Budget ms\s*\|")
        self.assertRegex(md, r"\|\s*Over\s*\|")
        # Summary line mentions over-budget count.
        self.assertIn("Over-budget tasks", md)
        # Per-task row carries the budget value.
        self.assertIn("3000", md)

    def test_budget_007_render_per_task_md_surfaces_budget_line(self):
        """render_per_task_md must surface the 'Wall-time budget' line."""
        from dataclasses import dataclass, field
        from eval.task import Expected

        @dataclass
        class _StubObs:
            iteration: int = 1
            exit_code: int = 0
            stdout: str = ""
            stderr: str = ""
            wall_time_ms: int = 50
            raw_error: str | None = None

        @dataclass
        class _StubGrade:
            verdict: str = "pass"
            bucket: str = "pass"
            failed_predicates: list = field(default_factory=list)
            notes: str = ""

        @dataclass
        class _StubTask:
            id: str = "probe-task"
            category: str = "syntax"
            name: str = "probe"
            type: str = "ping"
            timeout: int = 5
            weight: float = 1.0
            tags: list = field(default_factory=list)
            code: str | None = None
            context_path: str | None = None
            fixture: dict | None = None
            mode: str = "high_level"
            raw_data: str | None = None
            raw_resp_mode: str | None = None
            raw_resp_arg: str | None = None

        task = _StubTask()
        task.expected = Expected(wall_time_max_ms=2500)

        @dataclass
        class _StubResult:
            task: object = None
            n_iterations: int = 1
            observations: list = field(default_factory=list)
            grade_results: list = field(default_factory=list)

        result = _StubResult(
            task=task,
            n_iterations=1,
            observations=[_StubObs()],
            grade_results=[_StubGrade()],
        )

        md = render_per_task_md(result)
        self.assertIn("Wall-time budget", md)
        self.assertIn("2500", md)
        self.assertIn("info-only", md)

        # Also check the "not declared" branch.
        task_no_budget = _StubTask()
        task_no_budget.expected = Expected(wall_time_max_ms=None)
        result_no_budget = _StubResult(
            task=task_no_budget,
            n_iterations=1,
            observations=[_StubObs()],
            grade_results=[_StubGrade()],
        )
        md2 = render_per_task_md(result_no_budget)
        self.assertIn("not declared", md2)

    def test_budget_008_load_all_real_tasks_have_budgets(self):
        """Round-trip: every task loaded by load_all_suites has a
        Expected.wall_time_max_ms set."""
        suites = load_all_suites(TASKS_DIR)
        missing: list[str] = []
        for s in suites:
            for t in s.tasks:
                if t.expected.wall_time_max_ms is None:
                    missing.append(f"{t.id} ({s.file_path.name})")
        self.assertEqual(
            missing,
            [],
            f"{len(missing)} loaded task(s) have None budget — schema drifted. "
            f"Missing: {missing[:5]}",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)