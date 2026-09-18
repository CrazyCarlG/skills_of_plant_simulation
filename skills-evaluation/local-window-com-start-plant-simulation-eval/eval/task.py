"""Task dataclass + JSON loader for the golden task suite.

A Task describes one testable behavior of the
local-window-com-start-plant-simulation skill. Schema lives in
METHODOLOGY.md §3.2.

Notable differences from the simtalk-execution eval:
- The "type" field is the CLI's command family (cli-validation, com-errors,
  etc.) — NOT a SimTalk subcommand. We use `category` for that.
- Each task carries `args` (the literal argv to pass) and `mock` (bool).
- Mock mode injects a fake `win32com.client` via PYTHONPATH; the task can
  declare an expected `mock_call_sequence`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# Whitelist of valid task categories (METHODOLOGY.md §3.1).
VALID_CATEGORIES = {
    "cli-validation",
    "com-errors",
    "model-load",
    "injection",
    "port-change",
    "wait-ready",
    "print-pid",
    "lifelines",
    "exit-codes",
}


@dataclass
class Expected:
    """Predicate set the runner must satisfy.

    All predicates combine with AND. Each attribute is optional; absent ==
    "don't care about this dimension". See METHODOLOGY.md §3.3 for the
    full vocabulary.
    """

    exit_code: int | None = None
    exit_code_in: list[int] | None = None
    stderr_includes: list[str] | None = None
    stderr_excludes: list[str] | None = None
    stdout_includes: list[str] | None = None
    stdout_excludes: list[str] | None = None
    stdout_empty: bool | None = None
    stderr_empty: bool | None = None
    wall_time_max_ms: int | None = None
    mock_call_sequence: list[str] | None = None
    mock_call_sequence_includes: list[str] | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any] | None) -> "Expected":
        if d is None:
            return cls()
        return cls(
            exit_code=d.get("exit_code"),
            exit_code_in=d.get("exit_code_in"),
            stderr_includes=d.get("stderr_includes"),
            stderr_excludes=d.get("stderr_excludes"),
            stdout_includes=d.get("stdout_includes"),
            stdout_excludes=d.get("stdout_excludes"),
            stdout_empty=d.get("stdout_empty"),
            stderr_empty=d.get("stderr_empty"),
            wall_time_max_ms=d.get("wall_time_max_ms"),
            mock_call_sequence=d.get("mock_call_sequence"),
            mock_call_sequence_includes=d.get("mock_call_sequence_includes"),
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
        id:             unique slug like "cli-001-missing-model"
        category:       one of VALID_CATEGORIES (bucket for reporting)
        name:           human-readable
        args:           list of CLI args passed verbatim to the script
        mock:           True = use the fake win32com shim; False = real COM
        timeout:        seconds; runner enforces via subprocess timeout
        weight:         used for weighted pass rate (default 1.0)
        expected:       predicate set
        tags:           for filtering (smoke / regression / lifeline-L1 / ...)
        env:            optional env-var overrides for the subprocess
        cwd:            optional working-directory override
    """

    id: str
    category: str
    name: str
    args: list[str]
    mock: bool
    expected: Expected
    timeout: int = 30
    weight: float = 1.0
    tags: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    cwd: str | None = None
    # Optional mock fault config (passed to the shim as JSON). See
    # eval/_mock_win32com/__init__.py for the schema. The runner writes
    # this to a temp file and sets EVAL_MOCK_FAULTS in the subprocess env.
    mock_setup: dict[str, Any] | None = None
    # If False, the runner will NOT inject cfg.default_model / cfg.default_simtalkclaudefile.
    # Set this on tasks that intentionally exercise a missing-arg dimension
    # (e.g. cli-001, exit-code-2-bad-args). Default True (fill).
    fill_defaults: bool = True
    # Optional list of extra path substrings the mock isfile stub should
    # treat as existing. Use for edge-case tasks (e.g. inject-003 with a
    # path containing a quote) where the file path itself is part of the
    # test, not a real file on disk.
    extra_mock_paths: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.category not in VALID_CATEGORIES:
            raise ValueError(
                f"Task {self.id!r}: category {self.category!r} not in "
                f"whitelist {VALID_CATEGORIES}"
            )
        if not isinstance(self.args, list) or not all(
            isinstance(a, str) for a in self.args
        ):
            raise ValueError(
                f"Task {self.id!r}: 'args' must be a list of strings"
            )
        if self.expected.is_empty():
            raise ValueError(
                f"Task {self.id!r}: 'expected' must declare at least one predicate"
            )
        if self.timeout < 1:
            raise ValueError(f"Task {self.id!r}: timeout must be >= 1s")
        if self.weight < 0:
            raise ValueError(f"Task {self.id!r}: weight must be non-negative")

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Task":
        if "args" not in d:
            raise ValueError(f"Task missing 'args': {d.get('id', '?')}")
        raw_args = d["args"]
        if not isinstance(raw_args, list):
            raise ValueError(
                f"Task {d.get('id', '?')!r}: 'args' must be a list, "
                f"got {type(raw_args).__name__}"
            )
        if "mock" not in d:
            raise ValueError(
                f"Task {d.get('id', '?')!r}: 'mock' field is required "
                "(True for hermetic, False for integration)"
            )
        return cls(
            id=d["id"],
            category=d["category"],
            name=d["name"],
            args=list(raw_args),
            mock=bool(d["mock"]),
            expected=Expected.from_dict(d.get("expected")),
            timeout=d.get("timeout", 30),
            weight=d.get("weight", 1.0),
            tags=d.get("tags", []),
            env=d.get("env", {}),
            cwd=d.get("cwd"),
            mock_setup=d.get("mock_setup"),
            fill_defaults=d.get("fill_defaults", True),
            extra_mock_paths=d.get("extra_mock_paths", []),
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
    """Load one JSON suite file. Schema: top-level entry with 'tasks' list."""
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
