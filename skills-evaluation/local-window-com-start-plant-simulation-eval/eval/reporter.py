"""Report writers: Markdown + JSON aggregate reports + snapshot for diff.

All writers are pure (take results, return strings or write to files).
This keeps them easy to test and easy to extend (e.g., HTML, JUnit XML).

See METHODOLOGY.md §5 / §6 for the report contents and CI gate logic.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .grader import GraderResult
from .runner import TaskRunResult
from .stats import (
    TaskStats,
    bucket_histogram,
    compute_task_stats,
    weighted_pass_rate,
)


# Exit-code thresholds for CI gate (METHODOLOGY.md §6.3 / README.md CI section).
DEFAULT_GATE_PASS_RATE = 0.95
DEFAULT_GATE_FLAKY_TOLERANCE = 0


@dataclass
class AggregateReport:
    """Top-level summary across all tasks."""

    timestamp: str
    iterations: int
    per_task: list[TaskStats]
    per_task_results: list[TaskRunResult]
    bucket_hist: dict[str, int]
    weighted_pass_rate: float
    overall_n: int
    overall_n_pass: int
    n_flaky: int
    n_slow: int
    n_over_budget: int           # tasks where median_wall_ms > task budget (info-only)
    n_hard_gate_regressions: int  # pass_rate < 1.0 for any task with a hard-gate tag
    exit_gate_code: int           # 0 = all gates pass
    pass_rate_threshold: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "iterations": self.iterations,
            "weighted_pass_rate": round(self.weighted_pass_rate, 4),
            "pass_rate_threshold": self.pass_rate_threshold,
            "overall_n": self.overall_n,
            "overall_n_pass": self.overall_n_pass,
            "n_flaky": self.n_flaky,
            "n_slow": self.n_slow,
            "n_over_budget": self.n_over_budget,
            "n_hard_gate_regressions": self.n_hard_gate_regressions,
            "bucket_histogram": self.bucket_hist,
            "exit_gate_code": self.exit_gate_code,
            "tasks": [ts.to_dict() for ts in self.per_task],
        }


def aggregate(
    per_task_results: list[TaskRunResult],
    iterations: int,
    pass_rate_threshold: float = DEFAULT_GATE_PASS_RATE,
    hard_gate_tags: list[str] | None = None,
) -> AggregateReport:
    """Compute aggregate stats across all task results."""
    hard_gate_tags = hard_gate_tags or []
    ts_list: list[TaskStats] = []
    bucket_total: list[str] = []
    overall_n = 0
    overall_n_pass = 0
    n_hard_gate_regressions = 0
    pairs: list[tuple[float, float]] = []

    for r in per_task_results:
        verdicts = [g.verdict for g in r.grade_results]
        walls = [o.wall_time_ms for o in r.observations]
        stats = compute_task_stats(
            task_id=r.task.id,
            verdicts=verdicts,
            wall_times_ms=walls,
            task_category=r.task.category,
            task_budget_ms=r.task.expected.wall_time_max_ms,
        )
        ts_list.append(stats)
        bucket_total.extend(g.bucket for g in r.grade_results if g.verdict == "fail")
        overall_n += stats.n
        overall_n_pass += stats.n_pass
        pairs.append((r.task.weight, stats.pass_rate))
        # Hard-gate tag check (Lifeline compliance + exit-code matrix are
        # non-negotiable).
        if any(t in hard_gate_tags for t in r.task.tags):
            if stats.pass_rate < 1.0:
                n_hard_gate_regressions += 1

    wpr = weighted_pass_rate(pairs)
    n_flaky = sum(1 for ts in ts_list if ts.is_flaky)
    n_slow = sum(1 for ts in ts_list if ts.is_slow)
    n_over_budget = sum(1 for ts in ts_list if ts.is_over_budget)

    # Compute exit gate code (METHODOLOGY.md §6.3).
    # Priority: hard-gate (3) > below-threshold (1) > newly-flaky (2).
    # A below-threshold result is already a serious regression — flaky
    # status is secondary info, not a worse failure.
    gate = 0
    if wpr < pass_rate_threshold:
        gate = 1
    if n_hard_gate_regressions > 0:
        gate = 3
    elif n_flaky > DEFAULT_GATE_FLAKY_TOLERANCE and gate == 0:
        gate = 2

    return AggregateReport(
        timestamp=datetime.utcnow().isoformat(timespec="seconds") + "Z",
        iterations=iterations,
        per_task=ts_list,
        per_task_results=per_task_results,
        bucket_hist=bucket_histogram(bucket_total),
        weighted_pass_rate=wpr,
        overall_n=overall_n,
        overall_n_pass=overall_n_pass,
        n_flaky=n_flaky,
        n_slow=n_slow,
        n_over_budget=n_over_budget,
        n_hard_gate_regressions=n_hard_gate_regressions,
        exit_gate_code=gate,
        pass_rate_threshold=pass_rate_threshold,
    )


# --- Markdown rendering -------------------------------------------------------


def _truncate(s: str, n: int = 120) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def render_summary_md(report: AggregateReport) -> str:
    """Top-level human-readable summary."""
    results_by_task_id: dict[str, TaskRunResult] = {
        r.task.id: r for r in report.per_task_results
    }
    lines: list[str] = [
        "# local-window-com-start-plant-simulation — Evaluation Summary",
        "",
        f"- **Timestamp**: `{report.timestamp}`",
        f"- **Iterations per task**: {report.iterations}",
        f"- **Overall weighted pass rate**: **{report.weighted_pass_rate * 100:.1f}%** "
        f"({report.overall_n_pass}/{report.overall_n}) "
        f"(threshold {report.pass_rate_threshold * 100:.0f}%)",
        f"- **Flaky tasks**: {report.n_flaky}",
        f"- **Slow tasks**: {report.n_slow}",
        f"- **Over-budget tasks** (median > per-task wall_time_max_ms, info-only): {report.n_over_budget}",
        f"- **Hard-gate regressions** (lifeline / exit-code): {report.n_hard_gate_regressions}",
        f"- **CI gate**: exit code **{report.exit_gate_code}** "
        f"({'PASS' if report.exit_gate_code == 0 else 'FAIL'})",
        "",
        "## Failure bucket histogram",
        "",
        "| Bucket | Count |",
        "|---|---:|",
    ]
    if report.bucket_hist:
        for b, n in sorted(report.bucket_hist.items(), key=lambda x: -x[1]):
            lines.append(f"| `{b}` | {n} |")
    else:
        lines.append("| _(no failures)_ | 0 |")
    lines += ["", "## Per-task pass rates", ""]
    lines += [
        "| Task ID | Category | N | Pass | Pass rate | Median ms | Budget ms | Over | CI95 | Flag |",
        "|---|---|--:|--:|--:|--:|--:|:-:|---|---|",
    ]
    for ts in report.per_task:
        flag = []
        if ts.is_flaky:
            flag.append("flaky")
        if ts.is_slow:
            flag.append("slow")
        if ts.is_over_budget:
            flag.append("over")
        flag_s = ",".join(flag) if flag else "—"
        ci = f"[{ts.ci95_lo * 100:.0f}%, {ts.ci95_hi * 100:.0f}%]"
        cat = results_by_task_id[ts.task_id].task.category
        budget_s = "—" if ts.budget_ms is None else f"{ts.budget_ms}"
        over_s = "—" if ts.budget_ms is None else ("⚠ yes" if ts.is_over_budget else "no")
        lines.append(
            f"| `{ts.task_id}` | {cat} | "
            f"{ts.n} | {ts.n_pass} | {ts.pass_rate * 100:.0f}% | "
            f"{ts.median_wall_ms} | {budget_s} | {over_s} | {ci} | {flag_s} |"
        )
    lines += [
        "",
        "## Per-task details",
        "",
        "See `per-task/<task-id>.md` for raw runs and verdict reasoning.",
        "",
    ]
    return "\n".join(lines)


def render_per_task_md(result: TaskRunResult) -> str:
    """One markdown file per task with raw runs and verdict reasoning."""
    r = result
    lines = [
        f"# `{r.task.id}` — {r.task.name}",
        "",
        f"- **Category**: {r.task.category}",
        f"- **Mock mode**: {r.task.mock}",
        f"- **Tags**: {', '.join(r.task.tags) if r.task.tags else '—'}",
        f"- **Timeout**: {r.task.timeout}s",
        f"- **Wall-time budget**: "
        f"{r.task.expected.wall_time_max_ms if r.task.expected.wall_time_max_ms is not None else '—'}ms "
        f"(info-only; not a CI gate)",
        f"- **Iterations**: {r.n_iterations}",
        "",
        "## Args",
        "",
        "```",
        " ".join(repr(a) for a in r.task.args),
        "```",
        "",
        "## Expected",
        "",
        "```json",
        json.dumps(
            {k: v for k, v in r.task.expected.__dict__.items() if v is not None},
            indent=2,
        ),
        "```",
        "",
        "## Raw runs",
        "",
        "| # | Exit | Wall ms | Mock calls | Verdict | Bucket | Failed predicates | Notes |",
        "|---:|---:|--:|---|---|---|---|---|",
    ]
    for o, g in zip(r.observations, r.grade_results):
        calls = _truncate(",".join(o.mock_calls), 40) if o.mock_calls else "—"
        lines.append(
            "| {i} | {e} | {w} | {c} | {v} | `{b}` | {f} | {n} |".format(
                i=o.iteration,
                e=o.exit_code if o.exit_code is not None else "—",
                w=o.wall_time_ms,
                c=calls,
                v=g.verdict,
                b=g.bucket,
                f=_truncate("; ".join(g.failed_predicates), 80) or "—",
                n=_truncate(g.notes, 80) or "—",
            )
        )
    lines += ["", "## Last raw stdout/stderr", ""]
    if r.observations:
        last = r.observations[-1]
        lines += [
            "**stdout** (first 500 chars):",
            "",
            "```",
            _truncate(last.stdout, 500),
            "```",
            "",
            "**stderr** (first 500 chars):",
            "",
            "```",
            _truncate(last.stderr, 500),
            "```",
            "",
        ]
    return "\n".join(lines)


# --- File writers -------------------------------------------------------------


def write_reports(
    out_dir: Path,
    report: AggregateReport,
    per_task_results: list[TaskRunResult],
) -> dict[str, Path]:
    """Write summary.md, summary.json, per-task/*.md, snapshot.json.

    Returns a dict of {kind: path} for downstream tooling.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}

    p = out_dir / "summary.md"
    p.write_text(render_summary_md(report), encoding="utf-8")
    paths["summary_md"] = p

    p = out_dir / "summary.json"
    p.write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    paths["summary_json"] = p

    per_dir = out_dir / "per-task"
    per_dir.mkdir(exist_ok=True)
    for r in per_task_results:
        p = per_dir / f"{r.task.id}.md"
        p.write_text(render_per_task_md(r), encoding="utf-8")
    paths["per_task_dir"] = per_dir

    # snapshot-<ts>.json — full detail for cross-version diff.
    snap = {
        "timestamp": report.timestamp,
        "iterations": report.iterations,
        "tasks": [
            {
                "id": r.task.id,
                "category": r.task.category,
                "tags": r.task.tags,
                "weight": r.task.weight,
                "observations": [
                    {
                        "iteration": o.iteration,
                        "exit_code": o.exit_code,
                        "wall_time_ms": o.wall_time_ms,
                        "stdout_head": o.stdout[:200],
                        "stderr_head": o.stderr[:200],
                        "mock_calls": o.mock_calls,
                    }
                    for o in r.observations
                ],
                "grade_results": [g.to_dict() for g in r.grade_results],
            }
            for r in per_task_results
        ],
    }
    ts_slug = report.timestamp.replace(":", "").replace("-", "").replace("Z", "")
    p = out_dir / f"snapshot-{ts_slug}.json"
    p.write_text(json.dumps(snap, indent=2, ensure_ascii=False), encoding="utf-8")
    paths["snapshot"] = p

    return paths


# --- Cross-version diff -------------------------------------------------------


def diff_snapshots(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    """Compare two snapshot JSONs.

    Returns:
        {
          "newly_passing": [...task_ids],
          "newly_failing": [...task_ids],
          "pass_rate_drops": [{task_id, old, new, delta}],
          "new_flaky":      [...task_ids],
        }
    """
    def by_task(snap: dict[str, Any]) -> dict[str, dict[str, Any]]:
        return {t["id"]: t for t in snap.get("tasks", [])}

    def pass_rate(t: dict[str, Any]) -> float:
        gs = t.get("grade_results", [])
        if not gs:
            return 0.0
        n = sum(1 for g in gs if g.get("verdict") == "pass")
        return n / len(gs)

    old_t = by_task(old)
    new_t = by_task(new)

    newly_passing: list[str] = []
    newly_failing: list[str] = []
    drops: list[dict[str, Any]] = []
    new_flaky: list[str] = []

    for tid, new_task in new_t.items():
        old_pr = pass_rate(old_t[tid]) if tid in old_t else None
        new_pr = pass_rate(new_task)
        if old_pr is not None:
            if old_pr < 1.0 and new_pr == 1.0:
                newly_passing.append(tid)
            if old_pr == 1.0 and new_pr < 1.0:
                newly_failing.append(tid)
            if old_pr - new_pr > 0.20:
                drops.append(
                    {
                        "task_id": tid,
                        "old": round(old_pr, 3),
                        "new": round(new_pr, 3),
                        "delta": round(new_pr - old_pr, 3),
                    }
                )
        if new_pr < 0.80:
            new_flaky.append(tid)

    return {
        "newly_passing": newly_passing,
        "newly_failing": newly_failing,
        "pass_rate_drops": drops,
        "new_flaky": new_flaky,
    }
