"""Task dataclass + JSON loader for the golden task suite.

A Task describes one testable behavior of the local-simtalk-execution skill.
Schema lives in METHODOLOGY.md §3.2.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# Whitelist mirror of lifelines.md §3 (Quirk #13).
VALID_TYPES = {"ping", "simtalk_syntax", "simtalk_run", "readlog"}


@dataclass
class Expected:
    """Predicate set the runner must satisfy.

    All predicates combine with AND. Each attribute is optional; absent == "don't
    care about this dimension". See METHODOLOGY.md §3.3 for full vocabulary.
    """

    exit_code: int | None = None
    exit_code_in: list[int] | None = None
    result_includes: list[str] | None = None
    result_excludes: list[str] | None = None
    log_starts_with: str | None = None
    log_not_starts_with: str | None = None
    raw_contains: list[str] | None = None
    raw_excludes: list[str] | None = None
    json_field: dict[str, Any] | None = None
    wall_time_max_ms: int | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> "Expected":
        if d is None:
            return cls()
        return cls(
            exit_code=d.get("exit_code"),
            exit_code_in=d.get("exit_code_in"),
            result_includes=d.get("result_includes"),
            result_excludes=d.get("result_excludes"),
            log_starts_with=d.get("log_starts_with"),
            log_not_starts_with=d.get("log_not_starts_with"),
            raw_contains=d.get("raw_contains"),
            raw_excludes=d.get("raw_excludes"),
            json_field=d.get("json_field"),
            wall_time_max_ms=d.get("wall_time_max_ms"),
        )

    def is_empty(self) -> bool:
        """True if no predicate set (a degenerate task — flag in CI)."""
        for v in self.__dict__.values():
            if v is not None and v != [] and v != {}:
                return False
        return True


@dataclass
class Task:
    """One golden test case.

    Attributes:
        id:             unique slug like "syntax-001-valid-var"
        category:       bucket for reporting (e.g., "syntax", "quirks")
        name:           human-readable
        type:           ping / simtalk_syntax / simtalk_run / readlog
        code:           SimTalk to send (None for ping/readlog)
        context_path:   optional --context-path for simtalk_run
        timeout:        seconds; floor at 2× type's expected median
        weight:         used for weighted pass rate
        expected:       predicate set
        tags:           for filtering (smoke / regression / quirk-N)
        fixture:        mock-mode response (only used when --mock)
        mode:           "high_level" (default, uses simtalk_send.py) or
                        "raw_socket" (uses socket_client.py directly — needed
                        to test Quirk #13 unknown-type hangs).
        raw_data:       when mode="raw_socket", the literal --data payload
                        (must already end in ||END||).
        raw_resp_mode:  for raw mode: eof / line / fixed / delimiter (default delimiter).
        raw_resp_arg:   extra arg for the response mode (e.g., delimiter string
                        or fixed byte count).
    """

    id: str
    category: str
    name: str
    type: str
    expected: Expected
    code: str | None = None
    context_path: str | None = None
    timeout: int = 10
    weight: float = 1.0
    tags: list[str] = field(default_factory=list)
    fixture: dict[str, Any] | None = None
    mode: str = "high_level"
    raw_data: str | None = None
    raw_resp_mode: str | None = None
    raw_resp_arg: str | None = None

    def __post_init__(self) -> None:
        if self.mode not in ("high_level", "raw_socket"):
            raise ValueError(
                f"Task {self.id!r}: mode must be high_level or raw_socket"
            )
        # Whitelist check is bypassed for raw_socket mode (Quirk #13 needs an
        # off-whitelist type). high_level mode still validates.
        if self.mode == "high_level":
            if self.type not in VALID_TYPES:
                raise ValueError(
                    f"Task {self.id!r}: type {self.type!r} not in whitelist {VALID_TYPES}"
                )
            if self.type in ("simtalk_syntax", "simtalk_run") and not self.code:
                raise ValueError(
                    f"Task {self.id!r}: type {self.type!r} requires 'code' field"
                )
        else:
            if not self.raw_data:
                raise ValueError(
                    f"Task {self.id!r}: raw_socket mode requires 'raw_data'"
                )
        if self.expected.is_empty():
            raise ValueError(
                f"Task {self.id!r}: 'expected' must declare at least one predicate"
            )
        if self.timeout < 1:
            raise ValueError(f"Task {self.id!r}: timeout must be >= 1s")

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Task":
        return cls(
            id=d["id"],
            category=d["category"],
            name=d["name"],
            type=d["type"],
            expected=Expected.from_dict(d.get("expected")),
            code=d.get("code"),
            context_path=d.get("context_path"),
            timeout=d.get("timeout", 10),
            weight=d.get("weight", 1.0),
            tags=d.get("tags", []),
            fixture=d.get("fixture"),
            mode=d.get("mode", "high_level"),
            raw_data=d.get("raw_data"),
            raw_resp_mode=d.get("raw_resp_mode"),
            raw_resp_arg=d.get("raw_resp_arg"),
        )


@dataclass
class TaskSuite:
    """A loaded suite = (file_path, [Task, ...])."""

    file_path: Path
    tasks: list[Task]

    @property
    def n_tasks(self) -> int:
        return len(self.tasks)


def load_suite(path: Path) -> TaskSuite:
    """Load one JSON suite file. Schema: top-level task entry with 'tasks' list."""
    if not path.exists():
        raise FileNotFoundError(f"Suite not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        raw = json.load(fh)
    if "tasks" not in raw or not isinstance(raw["tasks"], list):
        raise ValueError(
            f"{path}: top-level must have 'tasks' list (got keys: {list(raw.keys())})"
        )
    tasks = [Task.from_dict(t) for t in raw["tasks"]]
    return TaskSuite(file_path=path, tasks=tasks)


def load_all_suites(suite_dir: Path) -> list[TaskSuite]:
    """Load all *.json files under suite_dir, sorted by filename."""
    if not suite_dir.exists():
        raise FileNotFoundError(f"Suite directory not found: {suite_dir}")
    files = sorted(suite_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No .json suite files in {suite_dir}")
    return [load_suite(f) for f in files]


def filter_suites(
    suites: list[TaskSuite],
    tag: str | None = None,
    task_id_substr: str | None = None,
) -> list[Task]:
    """Flatten + filter tasks across suites."""
    out: list[Task] = []
    for s in suites:
        for t in s.tasks:
            if tag and tag not in t.tags:
                continue
            if task_id_substr and task_id_substr not in t.id:
                continue
            out.append(t)
    return out