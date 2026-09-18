"""Variance / pass-rate stats.

Small, dependency-free statistics: mean, stddev, CI95. Enough for a
skill-eval report; not a stats library.

Wall-time budgets are per-category (not per-CLI-subcommand like the
simtalk-execution eval), because the script's wall time depends on what
COM call it makes, not on the task category.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


# Wall-time budgets per task category (METHODOLOGY.md §2 / §3).
# These are median expectations, not strict limits. A task that runs
# 2x the budget is flagged as "slow" in the report.
CATEGORY_MEDIAN_BUDGET_MS: dict[str, int] = {
    "cli-validation": 3_000,
    "com-errors": 5_000,
    "model-load": 60_000,
    "injection": 30_000,
    "port-change": 30_000,
    "wait-ready": 30_000,
    "print-pid": 30_000,
    "lifelines": 10_000,
    "exit-codes": 10_000,
}


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
    is_slow: bool           # median > 2× the category's expected median
    # Per-task wall-time budget (from task.expected.wall_time_max_ms).
    # None means the task did not declare a budget — over-budget check is
    # skipped for that task. Budgets are info-only, NOT a CI gate.
    budget_ms: int | None = None
    is_over_budget: bool = False  # median_wall_ms > budget_ms (when budget is set)

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


def compute_task_stats(
    task_id: str,
    verdicts: list[str],
    wall_times_ms: list[int],
    task_category: str,
    flaky_threshold: float = 0.80,
    task_budget_ms: int | None = None,
) -> TaskStats:
    """Aggregate per-task stats over N iterations.

    Args:
        verdicts: list of "pass" / "fail" / "inconclusive" per iteration.
        wall_times_ms: wall time per iteration (0 if unavailable).
        task_category: used to apply category-specific wall-time budget.
        flaky_threshold: pass rate below this -> flaky.
        task_budget_ms: per-task wall-time budget (from
            task.expected.wall_time_max_ms). When set, median > budget
            flips is_over_budget=True (info-only flag; never a CI gate).
    """
    n = len(verdicts)
    n_pass = sum(1 for v in verdicts if v == "pass")
    pass_rate = n_pass / n if n else 0.0
    ci_lo, ci_hi = wilson_ci(pass_rate, n)

    times = [float(t) for t in wall_times_ms if t > 0]
    med = _median(times)
    mean = _mean(times)
    std = _stddev(times)

    budget = CATEGORY_MEDIAN_BUDGET_MS.get(task_category, 10_000)
    is_slow = med > 2 * budget

    is_over_budget = bool(task_budget_ms) and med > task_budget_ms

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
