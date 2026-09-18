"""Variance / pass-rate stats.

Small, dependency-free statistics: mean, stddev, CI95, IQR. Enough for a
skill-eval report; not a stats library.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class TaskStats:
    task_id: str
    n: int
    n_pass: int
    pass_rate: float
    median_wall_ms: int
    mean_wall_ms: float
    stddev_wall_ms: float
    ci95_lo: float
    ci95_hi: float
    is_flaky: bool          # pass_rate < 0.80
    is_slow: bool           # median > 2× the type's expected median
    budget_ms: int | None = None   # task-declared wall-time budget (METHODOLOGY.md §2.3 / §3.3)
    is_over_budget: bool = False   # info-only flag: median > budget_ms

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "n": self.n,
            "n_pass": self.n_pass,
            "pass_rate": round(self.pass_rate, 4),
            "median_wall_ms": self.median_wall_ms,
            "mean_wall_ms": round(self.mean_wall_ms, 1),
            "stddev_wall_ms": round(self.stddev_wall_ms, 1),
            "ci95_lo": round(self.ci95_lo, 4),
            "ci95_hi": round(self.ci95_hi, 4),
            "is_flaky": self.is_flaky,
            "is_slow": self.is_slow,
            "budget_ms": self.budget_ms,
            "is_over_budget": self.is_over_budget,
        }


def _mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else 0.0


def _stddev(xs: list[float], ddof: int = 1) -> float:
    if len(xs) < 2:
        return 0.0
    m = _mean(xs)
    var = sum((x - m) ** 2 for x in xs) / (len(xs) - ddof)
    return math.sqrt(var)


def _median(xs: list[float]) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    n = len(s)
    mid = n // 2
    return s[mid] if n % 2 == 1 else (s[mid - 1] + s[mid]) / 2


def _iqr(xs: list[float]) -> float:
    """Interquartile range (Q3 - Q1)."""
    if not xs:
        return 0.0
    s = sorted(xs)
    n = len(s)
    q1 = s[n // 4] if n >= 4 else s[0]
    q3 = s[(3 * n) // 4] if n >= 4 else s[-1]
    return q3 - q1


def wilson_ci(p: float, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for binomial proportion. n>=1, p in [0,1].

    More robust than normal approximation when n is small or p is near 0/1.
    """
    if n == 0:
        return 0.0, 0.0
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, center - half), min(1.0, center + half)


# Type-expected wall-time medians (METHODOLOGY.md §2.3 budget defaults).
TYPE_MEDIAN_BUDGET_MS: dict[str, int] = {
    "ping": 500,
    "simtalk_syntax": 1000,
    "simtalk_run": 30000,
    "readlog": 2000,
}


def compute_task_stats(
    task_id: str,
    verdicts: list[str],
    wall_times_ms: list[int],
    task_type: str,
    flaky_threshold: float = 0.80,
    task_budget_ms: int | None = None,
) -> TaskStats:
    """Aggregate per-task stats over N iterations.

    Args:
        verdicts: list of "pass" / "fail" / "inconclusive" per iteration.
        wall_times_ms: wall time per iteration (0 if unavailable).
        task_type: used to apply type-specific wall-time budget.
        flaky_threshold: pass rate below this -> flaky.
        task_budget_ms: task-declared wall-time budget (from
            `expected.wall_time_max_ms`). When set, the report surfaces
            the per-task "Over" flag (median > budget). When None, the
            task is treated as having no declared budget (e.g., a task
            that doesn't measure wall time). `is_slow` continues to use
            the type's TYPE_MEDIAN_BUDGET_MS × 2 — the slow flag is a
            type-level signal independent of the per-task budget.
    """
    n = len(verdicts)
    n_pass = sum(1 for v in verdicts if v == "pass")
    pass_rate = n_pass / n if n else 0.0
    ci_lo, ci_hi = wilson_ci(pass_rate, n)

    times = [float(t) for t in wall_times_ms if t > 0]
    med = _median(times)
    mean = _mean(times)
    std = _stddev(times)

    type_budget = TYPE_MEDIAN_BUDGET_MS.get(task_type, 5000)
    is_slow = med > 2 * type_budget

    # Per-task over-budget flag (info-only). Only flag if the task
    # declared a budget and we have observations (med > 0).
    is_over_budget = (
        task_budget_ms is not None and times and med > task_budget_ms
    )

    return TaskStats(
        task_id=task_id,
        n=n,
        n_pass=n_pass,
        pass_rate=pass_rate,
        median_wall_ms=int(med),
        mean_wall_ms=mean,
        stddev_wall_ms=std,
        ci95_lo=ci_lo,
        ci95_hi=ci_hi,
        is_flaky=pass_rate < flaky_threshold,
        is_slow=is_slow,
        budget_ms=task_budget_ms,
        is_over_budget=is_over_budget,
    )


def bucket_histogram(buckets: list[str]) -> dict[str, int]:
    """Tally failure buckets for the summary report."""
    out: dict[str, int] = {}
    for b in buckets:
        out[b] = out.get(b, 0) + 1
    return out


def weighted_pass_rate(
    per_task_pass: list[tuple[float, float]],
) -> float:
    """Weighted average pass rate. Input: [(weight, pass_rate), ...]."""
    if not per_task_pass:
        return 0.0
    num = sum(w * p for w, p in per_task_pass)
    den = sum(w for w, _ in per_task_pass)
    return num / den if den else 0.0