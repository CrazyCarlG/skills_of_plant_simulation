"""Predicate-based auto-grader.

The grader evaluates an ObservedRun against a Task's Expected predicates.
All predicates combine with AND. Failed predicates are reported individually
so the report can show actionable feedback.

Predicate vocabulary: see METHODOLOGY.md §3.3.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from .task import Expected, Task


@dataclass
class ObservedRun:
    """What the runner captured for one execution of one task."""

    task_id: str
    iteration: int
    exit_code: int | None         # None if subprocess didn't start
    stdout: str = ""
    stderr: str = ""
    wall_time_ms: int = 0
    parsed_json: dict[str, Any] | None = None  # stdout parsed as JSON, if possible
    raw_error: str | None = None              # runner-level error (e.g., subprocess timeout)
    command: list[str] = field(default_factory=list)

    @property
    def result_str(self) -> str:
        """The `result` field from the response, or '' if not JSON."""
        if self.parsed_json and isinstance(self.parsed_json.get("result"), str):
            return self.parsed_json["result"]
        return ""

    @property
    def log_str(self) -> str:
        if self.parsed_json and isinstance(self.parsed_json.get("log"), str):
            return self.parsed_json["log"]
        return ""


@dataclass
class GraderResult:
    """One grading verdict."""

    task_id: str
    iteration: int
    verdict: str  # "pass" | "fail" | "inconclusive"
    bucket: str   # see METHODOLOGY.md §2.7 for taxonomy
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


# Failure attribution buckets (METHODOLOGY.md §2.7).
BUCKET_TIMEOUT = "timeout"
BUCKET_CONNECT_REFUSED = "connect_refused"
BUCKET_CONNECTION_BROKEN = "connection_broken"
BUCKET_COMPILE_ERROR = "compile_error"
BUCKET_RUNTIME_ERROR = "runtime_error"
BUCKET_SYNTAX_ERROR = "syntax_error"
BUCKET_READLOG_UNRELIABLE = "readlog_unreliable"
BUCKET_PROTOCOL_VIOLATION = "protocol_violation"
BUCKET_UNEXPECTED_SUCCESS = "unexpected_success"
BUCKET_WRONG_TYPE = "wrong_type"
BUCKET_UNKNOWN = "unknown"


# Module-level sentinel for "key missing from JSON path lookup".
_MISSING = object()


def _get_dotted(d: dict[str, Any] | None, path: str) -> Any:
    """Lookup by dotted path. Returns _MISSING sentinel on miss."""
    if not d or not isinstance(d, dict):
        return _MISSING
    cur: Any = d
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return _MISSING
    return cur


def _bucket_for(expected: Expected, observed: ObservedRun) -> str:
    """Pick a failure bucket. Must be called *after* verdict != 'inconclusive'."""
    if observed.exit_code is None:
        return BUCKET_UNKNOWN
    if observed.exit_code == 1:
        return BUCKET_TIMEOUT
    if observed.exit_code == 2:
        return BUCKET_CONNECT_REFUSED
    if observed.exit_code == 3:
        return BUCKET_CONNECTION_BROKEN
    if observed.exit_code == 10:
        # result == 'failed' is compile; Quirk #7 also returns 10? No — Quirk #7 is 11.
        # See lifelines.md §9 + §6.
        return BUCKET_COMPILE_ERROR
    if observed.exit_code == 11:
        return BUCKET_RUNTIME_ERROR
    if observed.exit_code == 12:
        return BUCKET_SYNTAX_ERROR
    if observed.exit_code == 20:
        return BUCKET_READLOG_UNRELIABLE
    # exit_code == 0 but failed predicates:
    # - 'unexpected_success' if expected was a failure (exit_code_in non-zero)
    # - 'wrong_type' if expected type didn't match observed type
    # - 'protocol_violation' otherwise
    if expected.exit_code is not None and expected.exit_code != 0:
        return BUCKET_UNEXPECTED_SUCCESS
    if expected.exit_code_in and all(c != 0 for c in expected.exit_code_in):
        return BUCKET_UNEXPECTED_SUCCESS
    # If we expected a different `type` than observed, call it wrong_type.
    # The runner passes the observed `type` via command args; we infer from
    # parsed_json.type vs expected. But Expected doesn't carry type. Caller
    # can set this via the task's `type` attribute — handled below.
    return BUCKET_PROTOCOL_VIOLATION


def grade(task: Task, observed: ObservedRun) -> GraderResult:
    """Evaluate one ObservedRun against one Task's Expected predicates.

    Returns:
        GraderResult with verdict, bucket, and any failed_predicates listed.
    """
    # Inconclusive: runner itself errored (no exit code captured).
    if observed.exit_code is None:
        return GraderResult(
            task_id=task.id,
            iteration=observed.iteration,
            verdict="inconclusive",
            bucket=BUCKET_UNKNOWN,
            observed=observed,
            notes=f"runner-level error: {observed.raw_error or '(none)'}",
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

    # result_includes / result_excludes
    res = observed.result_str
    if exp.result_includes:
        for needle in exp.result_includes:
            if needle not in res:
                failed.append(f"result_includes: missing {needle!r} in result {res!r}")
    if exp.result_excludes:
        for needle in exp.result_excludes:
            if needle in res:
                failed.append(f"result_excludes: unexpected {needle!r} in result {res!r}")

    # log_starts_with / log_not_starts_with
    log = observed.log_str
    if exp.log_starts_with is not None and not log.startswith(exp.log_starts_with):
        failed.append(
            f"log_starts_with: expected prefix {exp.log_starts_with!r}, got {log[:40]!r}..."
        )
    if exp.log_not_starts_with is not None and log.startswith(exp.log_not_starts_with):
        failed.append(
            f"log_not_starts_with: prefix {exp.log_not_starts_with!r} present in log"
        )

    # raw_contains / raw_excludes (on raw stdout, for non-JSON fallbacks)
    if exp.raw_contains:
        for needle in exp.raw_contains:
            if needle not in observed.stdout:
                failed.append(f"raw_contains: missing {needle!r} in stdout")
    if exp.raw_excludes:
        for needle in exp.raw_excludes:
            if needle in observed.stdout:
                failed.append(f"raw_excludes: unexpected {needle!r} in stdout")

    # json_field dotted-path
    if exp.json_field is not None:
        for path, want in exp.json_field.items():
            got = _get_dotted(observed.parsed_json, path)
            if got is _MISSING:
                failed.append(f"json_field: {path!r} missing from parsed JSON")
            elif got != want:
                failed.append(
                    f"json_field: {path!r} expected {want!r}, got {got!r}"
                )

    # wall_time_max_ms
    if (
        exp.wall_time_max_ms is not None
        and observed.wall_time_ms > exp.wall_time_max_ms
    ):
        failed.append(
            f"wall_time_max_ms: {observed.wall_time_ms}ms > {exp.wall_time_max_ms}ms budget"
        )

    verdict = "pass" if not failed else "fail"
    bucket = _bucket_for(exp, observed) if failed else "pass"

    # Special case: if the task expected a non-zero exit and got zero, that's
    # unexpected_success; otherwise bucket_protocol_violation covers it.
    notes = ""
    if verdict == "fail" and bucket == BUCKET_PROTOCOL_VIOLATION:
        # If a parsed JSON exists but fields don't match expectations, leave as-is.
        if observed.parsed_json is None and observed.stdout:
            notes = "response was not valid JSON (possible server-side error string)"
        elif observed.parsed_json is not None:
            notes = f"observed parsed: {json.dumps(observed.parsed_json)[:200]}"

    return GraderResult(
        task_id=task.id,
        iteration=observed.iteration,
        verdict=verdict,
        bucket=bucket,
        failed_predicates=failed,
        observed=observed,
        notes=notes,
    )