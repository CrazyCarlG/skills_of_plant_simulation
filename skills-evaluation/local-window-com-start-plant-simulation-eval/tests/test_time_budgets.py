#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for per-task wall-time budgets (METHODOLOGY.md §2 / §3).

The eval has a `wall_time_max_ms` predicate on each task's `expected`
block. This test suite enforces:

    budget-001  Every task JSON file declares `wall_time_max_ms` on each
                task's expected block.
    budget-002  Every declared budget is a positive integer (>= 100ms,
                <= 10 minutes — a sanity range; the budgets are meant
                to flag *catastrophic* regressions, not microsecond
                jitter).
    budget-003  Hermetic (mock=true) tasks have a budget that is
                consistent with their category's CATEGORY_MEDIAN_BUDGET_MS
                in eval/stats.py — i.e., a task budget is no more than
                10× the category median (rules out typos like a stray
                zero). For real-COM tasks (mock=false) we only require
                the budget be reasonable; the category median is for
                hermetic work, real-COM PS launch can legitimately be
                much slower.
    budget-004  The eval.reporter.AggregateReport dataclass exposes a
                `n_over_budget` field and the JSON summary contains it
                (no KeyError on the field).
    budget-005  The eval.stats.TaskStats dataclass exposes
                `budget_ms` + `is_over_budget` fields.

The budgets are info-only — they do NOT contribute to the CI gate
(METHODOLOGY.md §6.3 / §7). These tests therefore only assert schema
and reasonableness, never that all budgets are met. A future check that
the mock eval gate's n_over_budget stays 0 lives in
`test_mock_eval_gate.py` (which performs a real eval run).
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve()
_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_ROOT))

from eval.stats import CATEGORY_MEDIAN_BUDGET_MS, TaskStats, compute_task_stats  # noqa: E402
from eval.reporter import AggregateReport  # noqa: E402


TASKS_DIR = _ROOT / "tasks"
MIN_BUDGET_MS = 100         # below this is unrealistic for any task
MAX_BUDGET_MS = 10 * 60_000  # 10 minutes — beyond this is a typo


def _all_task_files() -> list[Path]:
    return sorted(TASKS_DIR.glob("*.json"))


def _all_tasks() -> list[dict]:
    out: list[dict] = []
    for p in _all_task_files():
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

    def test_budget_003_hermetic_budgets_consistent_with_category(self):
        """Hermetic (mock=true) task budgets should not exceed 10× the
        category's CATEGORY_MEDIAN_BUDGET_MS in eval/stats.py. Real-COM
        tasks (mock=false) get a separate, looser ceiling."""
        bad: list[tuple[str, str, int, int]] = []
        # Real-COM ceiling: 5× the maximum category median (currently
        # model-load = 60s), so a real PS launch can be up to 5 minutes.
        REAL_COM_CEILING_MS = 5 * max(CATEGORY_MEDIAN_BUDGET_MS.values())
        for t in _all_tasks():
            category = t.get("category")
            mock = bool(t.get("mock"))
            expected = t.get("expected") or {}
            b = expected.get("wall_time_max_ms")
            if b is None:
                continue
            if not mock:
                if b > REAL_COM_CEILING_MS:
                    bad.append((
                        t.get("id"),
                        f"real-com budget > {REAL_COM_CEILING_MS}ms",
                        b,
                        REAL_COM_CEILING_MS,
                    ))
                continue
            cat_median = CATEGORY_MEDIAN_BUDGET_MS.get(category)
            if cat_median is None:
                # Unknown category — not our problem here; caught by
                # task dataclass validation upstream.
                continue
            ceiling = 10 * cat_median
            if b > ceiling:
                bad.append((
                    t.get("id"),
                    f"hermetic budget > 10× category median ({cat_median})",
                    b,
                    ceiling,
                ))
        self.assertEqual(
            bad,
            [],
            f"{len(bad)} task(s) have budgets inconsistent with their category. "
            f"First few: {bad[:5]}",
        )

    def test_budget_004_aggregate_report_has_n_over_budget(self):
        """Schema smoke test: AggregateReport must carry n_over_budget
        so the JSON summary + markdown report can surface it."""
        # Round-trip a minimal report to dict.
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
            n_over_budget=0,
            n_hard_gate_regressions=0,
            exit_gate_code=0,
            pass_rate_threshold=0.95,
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
            task_category="cli-validation",
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
            task_category="cli-validation",
            task_budget_ms=500,
        )
        self.assertEqual(ts2.budget_ms, 500)
        self.assertFalse(ts2.is_over_budget)

        # 3. Budget set + median > budget → over budget (info-only flag).
        ts3 = compute_task_stats(
            task_id="t3",
            verdicts=["pass"],
            wall_times_ms=[9000, 9100, 9200],
            task_category="cli-validation",
            task_budget_ms=1000,
        )
        self.assertEqual(ts3.budget_ms, 1000)
        self.assertTrue(ts3.is_over_budget)
        self.assertIn("is_over_budget", ts3.to_dict())


class TestReporterBudgetColumns(unittest.TestCase):
    """The markdown summary must surface budget + over columns."""

    def test_budget_006_render_summary_md_has_budget_columns(self):
        from eval.reporter import render_summary_md
        # Construct a fake report with one task that has a budget.
        from eval.stats import TaskStats
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

        # Minimal stub for the per-task table — render_summary_md only
        # needs .task.category on each result.
        from dataclasses import dataclass

        @dataclass
        class _StubObs:
            iteration: int = 1
            exit_code: int = 0
            stdout: str = ""
            stderr: str = ""
            wall_time_ms: int = 400
            mock_calls: list[str] = None  # type: ignore[assignment]
            raw_error: str | None = None
            mock_setup_error: str | None = None

        @dataclass
        class _StubGrade:
            verdict: str = "pass"
            bucket: str = "ok"
            failed_predicates: list[str] = None  # type: ignore[assignment]
            notes: str = ""

        @dataclass
        class _StubTask:
            id: str = "probe-task"
            category: str = "cli-validation"
            name: str = "probe"
            args: list = None  # type: ignore[assignment]
            mock: bool = True
            timeout: int = 5
            weight: float = 1.0
            tags: list = None  # type: ignore[assignment]
            env: dict = None  # type: ignore[assignment]
            cwd: str | None = None
            mock_setup: dict | None = None
            fill_defaults: bool = True
            extra_mock_paths: list = None  # type: ignore[assignment]

            def __post_init__(self):
                if self.args is None:
                    self.args = []
                if self.tags is None:
                    self.tags = []
                if self.env is None:
                    self.env = {}
                if self.extra_mock_paths is None:
                    self.extra_mock_paths = []

        from eval.task import Expected

        task = _StubTask()
        task.expected = Expected(wall_time_max_ms=3000)

        @dataclass
        class _StubResult:
            observations: list = None
            grade_results: list = None

            def __post_init__(self):
                if self.observations is None:
                    self.observations = [_StubObs()]
                if self.grade_results is None:
                    self.grade_results = [_StubGrade()]

        result = _StubResult()
        result.task = task

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
            n_over_budget=0,
            n_hard_gate_regressions=0,
            exit_gate_code=0,
            pass_rate_threshold=0.95,
        )

        md = render_summary_md(rep)
        # Header columns include Budget + Over.
        self.assertRegex(md, r"\|\s*Budget ms\s*\|")
        self.assertRegex(md, r"\|\s*Over\s*\|")
        # Summary line mentions over-budget count.
        self.assertIn("Over-budget tasks", md)
        # Per-task row carries the budget value.
        self.assertIn("3000", md)


if __name__ == "__main__":
    unittest.main(verbosity=2)
