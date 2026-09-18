"""Predicate-based auto-grader for the subprocess wrapper.

The grader evaluates an ObservedRun against a Task's Expected predicates.
All predicates combine with AND. Failed predicates are reported individually
so the report can show actionable feedback.

Predicate vocabulary: see METHODOLOGY.md §3.3.

Failure-bucket taxonomy: see METHODOLOGY.md §5.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .task import Expected, Task


@dataclass
class ObservedRun:
    """What the runner captured for one execution of one task."""

    task_id: str
    iteration: int
    exit_code: int | None = None  # None if subprocess didn't start
    stdout: str = ""
    stderr: str = ""
    wall_time_ms: int = 0
    raw_error: str | None = None  # runner-level error (e.g., subprocess timeout)
    command: list[str] = field(default_factory=list)
    mock_calls: list[str] = field(default_factory=list)  # method names the mock saw
    mock_setup_error: str | None = None  # set if mock shim import failed

    @property
    def captured(self) -> bool:
        return self.exit_code is not None


# Failure attribution buckets (METHODOLOGY.md §5).
BUCKET_WRONG_EXIT_CODE = "wrong_exit_code"
BUCKET_STDERR_MISSING_REQUIRED = "stderr_missing_required"
BUCKET_STDERR_HAS_UNEXPECTED = "stderr_has_unexpected"
BUCKET_STDOUT_DISCIPLINE = "stdout_discipline"
BUCKET_MOCK_CALL_MISMATCH = "mock_call_mismatch"
BUCKET_WAIT_READY_UNEXPECTED = "wait_ready_unexpected"
BUCKET_COM_ERROR_HINT_WRONG = "com_error_hint_wrong"
BUCKET_MOCK_SETUP_FAILED = "mock_setup_failed"
BUCKET_SUBPROCESS_DID_NOT_START = "subprocess_did_not_start"
BUCKET_TIMEOUT = "timeout"
BUCKET_UNKNOWN = "unknown"


# Mapping from raw subprocess timeout to bucket.
_TIMEOUT_BUCKET = BUCKET_TIMEOUT
_SUBPROCESS_MISSING_BUCKET = BUCKET_SUBPROCESS_DID_NOT_START


def _bucket_for(expected: Expected, observed: ObservedRun) -> str:
    """Pick a failure bucket. Must be called *after* verdict != 'inconclusive'."""
    if observed.exit_code is None:
        return BUCKET_UNKNOWN
    # Subprocess-level timeout from the runner.
    if observed.raw_error == "subprocess_timeout":
        return _TIMEOUT_BUCKET
    # Exit-code compliance first.
    if (
        expected.exit_code is not None
        and observed.exit_code != expected.exit_code
    ):
        return BUCKET_WRONG_EXIT_CODE
    if (
        expected.exit_code_in is not None
        and observed.exit_code not in expected.exit_code_in
    ):
        return BUCKET_WRONG_EXIT_CODE
    # stderr/stdout shape next.
    if expected.stderr_includes:
        for needle in expected.stderr_includes:
            if needle not in observed.stderr:
                return BUCKET_STDERR_MISSING_REQUIRED
    if expected.stderr_excludes:
        for needle in expected.stderr_excludes:
            if needle in observed.stderr:
                return BUCKET_STDERR_HAS_UNEXPECTED
    if expected.stdout_includes or expected.stdout_excludes or (
        expected.stdout_empty is not None
    ):
        return BUCKET_STDOUT_DISCIPLINE
    # mock call sequence mismatch.
    if expected.mock_call_sequence or expected.mock_call_sequence_includes:
        return BUCKET_MOCK_CALL_MISMATCH
    return BUCKET_UNKNOWN


def grade(task: Task, observed: ObservedRun) -> "GraderResult":
    """Evaluate one ObservedRun against one Task's Expected predicates.

    Returns:
        GraderResult with verdict, bucket, and any failed_predicates listed.
    """
    # Mock shim didn't load — inconclusive only if the subprocess also
    # didn't capture any output. Some tasks intentionally disable the shim
    # (e.g. lifeline-L6 uses EVAL_MOCK_DISABLE=1 to simulate a host with
    # no pywin32); the subprocess still runs and we should grade against
    # its real output.
    if observed.mock_setup_error and not observed.captured:
        return GraderResult(
            task_id=task.id,
            iteration=observed.iteration,
            verdict="inconclusive",
            bucket=BUCKET_MOCK_SETUP_FAILED,
            observed=observed,
            notes=f"mock shim failed to load: {observed.mock_setup_error}",
        )

    # Runner-level error (subprocess didn't start, etc.).
    if not observed.captured:
        bucket = (
            _SUBPROCESS_MISSING_BUCKET
            if observed.raw_error and observed.raw_error.startswith("file_not_found")
            else BUCKET_UNKNOWN
        )
        return GraderResult(
            task_id=task.id,
            iteration=observed.iteration,
            verdict="inconclusive",
            bucket=bucket,
            observed=observed,
            notes=f"runner-level error: {observed.raw_error or '(none)'}",
        )

    # Runner-level timeout (the task's --wait-ready was longer than our subprocess timeout).
    if observed.raw_error == "subprocess_timeout":
        return GraderResult(
            task_id=task.id,
            iteration=observed.iteration,
            verdict="fail",
            bucket=_TIMEOUT_BUCKET,
            observed=observed,
            notes="subprocess exceeded runner timeout (was --wait-ready too long?)",
        )

    exp = task.expected
    failed: list[str] = []

    # exit_code
    if exp.exit_code is not None and observed.exit_code != exp.exit_code:
        failed.append(
            f"exit_code: expected {exp.exit_code}, got {observed.exit_code}"
        )
    if exp.exit_code_in is not None and observed.exit_code not in exp.exit_code_in:
        failed.append(
            f"exit_code_in: expected one of {exp.exit_code_in}, got {observed.exit_code}"
        )

    # stderr
    if exp.stderr_includes:
        for needle in exp.stderr_includes:
            if needle not in observed.stderr:
                failed.append(
                    f"stderr_includes: missing {needle!r} in stderr (stderr: "
                    f"{observed.stderr[:120]!r})"
                )
    if exp.stderr_excludes:
        for needle in exp.stderr_excludes:
            if needle in observed.stderr:
                failed.append(f"stderr_excludes: unexpected {needle!r} in stderr")
    if exp.stderr_empty is True and observed.stderr != "":
        failed.append(
            f"stderr_empty: expected empty, got {observed.stderr[:120]!r}"
        )
    if exp.stderr_empty is False and observed.stderr == "":
        failed.append("stderr_empty: expected non-empty, got empty")

    # stdout
    if exp.stdout_includes:
        for needle in exp.stdout_includes:
            if needle not in observed.stdout:
                failed.append(
                    f"stdout_includes: missing {needle!r} in stdout (stdout: "
                    f"{observed.stdout[:120]!r})"
                )
    if exp.stdout_excludes:
        for needle in exp.stdout_excludes:
            if needle in observed.stdout:
                failed.append(f"stdout_excludes: unexpected {needle!r} in stdout")
    if exp.stdout_empty is True and observed.stdout != "":
        failed.append(
            f"stdout_empty: expected empty, got {observed.stdout[:120]!r}"
        )
    if exp.stdout_empty is False and observed.stdout == "":
        failed.append("stdout_empty: expected non-empty, got empty")

    # mock_call_sequence
    if exp.mock_call_sequence is not None:
        if observed.mock_calls != exp.mock_call_sequence:
            failed.append(
                f"mock_call_sequence: expected {exp.mock_call_sequence}, "
                f"got {observed.mock_calls}"
            )
    if exp.mock_call_sequence_includes is not None:
        for needle in exp.mock_call_sequence_includes:
            if needle not in observed.mock_calls:
                failed.append(
                    f"mock_call_sequence_includes: {needle!r} not in observed "
                    f"{observed.mock_calls}"
                )

    # wall_time_max_ms
    if (
        exp.wall_time_max_ms is not None
        and observed.wall_time_ms > exp.wall_time_max_ms
    ):
        failed.append(
            f"wall_time_max_ms: {observed.wall_time_ms}ms > "
            f"{exp.wall_time_max_ms}ms budget"
        )

    verdict = "pass" if not failed else "fail"
    bucket = _bucket_for(exp, observed) if failed else "pass"
    notes = ""
    if verdict == "fail" and bucket == BUCKET_UNKNOWN and observed.stderr:
        notes = f"stderr: {observed.stderr[:200]!r}"

    return GraderResult(
        task_id=task.id,
        iteration=observed.iteration,
        verdict=verdict,
        bucket=bucket,
        failed_predicates=failed,
        observed=observed,
        notes=notes,
    )


@dataclass
class GraderResult:
    """One grading verdict."""

    task_id: str
    iteration: int
    verdict: str  # "pass" | "fail" | "inconclusive"
    bucket: str   # see METHODOLOGY.md §5 for taxonomy
    failed_predicates: list[str] = field(default_factory=list)
    observed: ObservedRun | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "iteration": self.iteration,
            "verdict": self.verdict,
            "bucket": self.bucket,
            "failed_predicates": list(self.failed_predicates),
            "notes": self.notes,
            "exit_code": self.observed.exit_code if self.observed else None,
            "wall_time_ms": self.observed.wall_time_ms if self.observed else 0,
        }
