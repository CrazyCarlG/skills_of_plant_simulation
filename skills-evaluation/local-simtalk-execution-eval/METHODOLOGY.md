# Evaluation Methodology — `local-simtalk-execution`

> The evaluation framework for the `local-simtalk-execution` skill. Defines what
> "good" means, how it's measured, and how the results should be interpreted.

---

## 1. Scope

`local-simtalk-execution` is a TCP client wrapper around Plant Simulation's
`SimtalkClaude` socket server. It has three observable behaviors we can test:

| Behavior | Surface |
|---|---|
| **Connectivity** | can the client reach the server, frame packets, terminate cleanly |
| **Syntax check** | does the server report parse errors via the documented field contract |
| **Run** | does the server execute code and report success/failure via the documented field contract |
| **Edge cases** | modal traps, list API quirks, namespace protection, readlog v15+ behavior |

Everything that can be tested without stateful setup belongs here. Stateful
operations (writing methods, editing objects, exploring the folder tree) are
covered by *other* skills' evaluation suites and out of scope for this one.

---

## 2. The Seven Evaluation Dimensions

| # | Dimension | What it measures | Why it matters |
|---|---|---|---|
| 1 | **Trigger Precision** | did the right `type`/`subcommand` get used for the task | wrong type → silent hang (Quirk #13) |
| 2 | **Semantic Completion** | did the call return the expected `result`/`log` per `lifelines.md` §6 | exit code 0 ≠ semantic success |
| 3 | **Efficiency** | wall time, subprocess startup, JSON parse overhead | long sims + tight timeouts = bad |
| 4 | **Robustness** | does the skill survive bad inputs (bad JSON, missing fields, wrong types) | server-side exception throwing verification |
| 5 | **Variance Stability** | does the same task produce the same verdict across N runs | flaky graders are useless |
| 6 | **Quirk Protocol Compliance** | does the skill handle Quirk #5/#6/#7/#13 correctly | protocol bugs here = silent hang in production |
| 7 | **Failure Attribution** | are failures bucketed into actionable categories | without buckets, you can't fix |

### 2.1 Trigger Precision

Each task declares which `type`/`subcommand` *should* be invoked. The grader
checks the runner actually used the right one. Wrong-type cases (e.g., using
`simtalk_run` for what should be `simtalk_syntax`) are counted as **precision
errors**.

**Why it's separate from completion**: a skill can use the right `type` and
still fail (e.g., bad code), or use the wrong `type` and still get a reply
(e.g., by accident). They measure different bugs.

### 2.2 Semantic Completion

For each `type`, the documented success criterion (from `lifelines.md` §6):

| `type` | Success |
|---|---|
| `ping` | `type == "ping" AND result == "success"` |
| `simtalk_syntax` | `"hasError" not in result` |
| `simtalk_run` | `result == "success" AND not log.startswith("code execute failed")` |
| `readlog` | `result == "success"` (exit 20 with non-empty stdout also OK per Q-002) |

Tasks declare the **expected exit code** (0/1/2/3/10/11/12/20) and the
**expected response shape** (result substring, log prefix, etc.).

### 2.3 Efficiency

Wall time per call (milliseconds). Subdivided into:
- **subprocess startup**: Python + argparse + import overhead
- **socket connect**: TCP handshake + first byte
- **server round-trip**: from `data` sent to first byte received
- **total wall time**: end-to-end including JSON parse

`simtalk_syntax` and `ping` should be sub-second; `simtalk_run` of a
non-trivial model can be 30s+. The grader flags a task as **slow** if its
median exceeds the declared budget (default 3× the type's expected median).

### 2.4 Robustness

Three classes of input are tested:

1. **Bad JSON**: `{"type": "ping", broken syntax`
2. **Missing required field**: `{"type": "simtalk_run"}` (no `simtalk_code`)
3. **Wrong type field**: `{"type": "execute_code"}` (unknown, triggers Quirk #13)

Expected behavior: server returns a non-JSON string error (for bad JSON /
missing field) or hangs to timeout (for unknown type). The grader checks the
runner surfaces these correctly (non-zero exit, parsed error string, or
TIMEOUT respectively).

### 2.5 Variance Stability

Each task is run `N` times (default N=5). The grader computes:
- **Pass rate**: % of N runs with the expected verdict
- **Variance σ**: stddev of total wall time
- **CI95**: confidence interval on pass rate

Pass rate < 80% → flag as **flaky**. σ/mean > 0.5 → flag as **noisy timing**.

### 2.6 Quirk Protocol Compliance

Specific tests for each quirk:

| Quirk | Test | Expected |
|---|---|---|
| #5 | ignore `retsult` field | runner must not gate on `retsult` |
| #6 | ignore `data` field (always empty on `simtalk_run`) | runner must not gate on `data` |
| #7 | soft failure detection (`result=success` + `log=code execute failed...`) | runner must return 11, not 0 |
| #13 | unknown `type` → silent hang → timeout | runner must return TIMEOUT, not 0 |

A skill update that breaks any of these → auto-fail the suite.

### 2.7 Failure Attribution

Each failed run is bucketed:

| Bucket | Trigger |
|---|---|
| `connect_refused` | exit 2 |
| `timeout` | exit 1 |
| `connection_broken` | exit 3 |
| `compile_error` | exit 10 + `result=failed` |
| `runtime_error` | exit 11 + `result=success` + log starts `code execute failed` |
| `syntax_error` | exit 12 |
| `readlog_unreliable` | exit 20 |
| `protocol_violation` | unexpected shape (missing field, wrong type, malformed JSON) |
| `unexpected_success` | task expected failure but got exit 0 |
| `unknown` | anything else |

The report prints a **bucket histogram** so a regression is immediately
actionable ("12 more `runtime_error` failures this week → Quirk #7 handler
broke").

---

## 3. Task Suite Design

### 3.1 Categories

7 files in `tasks/`, one per category:

| File | Tasks | What it covers |
|---|---:|---|
| `01-connection.json` | 4 | ping, wrong host, wrong port, framing mode mismatch |
| `02-syntax.json` | 6 | valid var/control-flow/params, invalid `byval`, invalid `byref :=` |
| `03-run.json` | 6 | happy path, runtime exception (Quirk #7), compile error, param variants |
| `04-quirks.json` | 5 | `data`/`retsult` ignored, Quirk #7 detection, Quirk #13 hang |
| `05-modal-traps.json` | 4 | `prompt`, `infoBox`, undeclared attr, `promptList1` |
| `06-list-api.json` | 3 | `.dim` vs `.length`, list literal assign, `print l.dim` |
| `07-framing-and-namespace.json` | 4 | `eof` mode timeout, missing `||END||`, `.SimtalkClaude.*` write |

Total: **32 tasks**. Each runs N=5 by default → 160 raw observations per
suite.

### 3.2 Task Schema

```json
{
  "id": "syntax-001-valid-var",
  "category": "syntax",
  "name": "valid var declaration with init",
  "type": "simtalk_syntax",
  "code": "var x: integer := 42",
  "context_path": null,
  "timeout": 10,
  "weight": 1,
  "expected": {
    "exit_code": 0,
    "result_excludes": ["hasError"],
    "result_includes": ["has no Error"]
  },
  "tags": ["happy-path", "smoke"]
}
```

| Field | Required | Meaning |
|---|---|---|
| `id` | ✓ | unique slug |
| `category` | ✓ | bucket for reporting |
| `name` | ✓ | human-readable |
| `type` | ✓ | `ping` / `simtalk_syntax` / `simtalk_run` / `readlog` |
| `code` | optional | SimTalk source (required for syntax/run) |
| `context_path` | optional | `simtalk_run` context |
| `timeout` | ✓ | seconds; floor at 2× the type's expected median |
| `weight` | optional | default 1; used to compute weighted pass rate |
| `expected` | ✓ | grader predicates (see §4) |
| `tags` | optional | for filtering (`smoke`, `regression`, `quirk-N`) |

### 3.3 Expected Verdict Vocabulary

Predicates the grader supports:

| Predicate | Meaning |
|---|---|
| `exit_code: int` | exact match |
| `exit_code_in: [int, ...]` | one-of |
| `result_includes: [str, ...]` | all substrings present in `result` |
| `result_excludes: [str, ...]` | no substring present in `result` |
| `log_starts_with: str` | prefix match |
| `log_not_starts_with: str` | prefix mismatch |
| `raw_contains: [str, ...]` | substrings in raw stdout (for non-JSON responses) |
| `json_field: {path: value}` | dotted path into parsed JSON (e.g., `data.result`) |
| `wall_time_max_ms: int` | upper bound on wall time |

Multiple predicates combine with **AND**.

---

## 4. Grader Design

```
observed_run  ─┐
                ├─► Grader.grade(task, observed_run) → GraderResult
task.expected ──┘
```

`GraderResult` records:

- `verdict`: `pass` | `fail` | `inconclusive`
- `bucket`: failure attribution (per §2.7)
- `failed_predicates`: which predicates failed (for actionable feedback)
- `observed`: raw exit code, stdout, stderr, wall time

A task is `inconclusive` when the runner itself errored out before grading
(e.g., subprocess didn't start). These are reported separately and excluded
from pass-rate calculations.

---

## 5. Variance & Regression Protocol

### 5.1 Per-run pass rate

For each task, run N times. Pass rate = (number of runs where verdict=pass) / N.

A task is **flaky** if pass rate < 80%. Flaky tasks are reported but don't
auto-fail the suite (they're flagged for investigation).

### 5.2 Cross-version regression

The runner writes a JSON snapshot of all per-task verdicts to
`reports/snapshot-<timestamp>.json`. To compare versions:

```bash
python3 scripts/run_eval.py --compare reports/snapshot-old.json reports/snapshot-new.json
```

This produces a **diff report** showing:
- Tasks that newly pass
- Tasks that newly fail
- Tasks whose pass rate dropped > 20%
- New flaky tasks

### 5.3 CI gate suggestion

Recommended CI invariant (in `reports/summary.md`):

- ≥ 95% overall weighted pass rate
- 0 new flaky tasks
- 0 regression in `04-quirks.json` (Quirk compliance is non-negotiable)

---

## 6. Limitations

1. **Live server only**. This suite tests against a real Plant Simulation
   server. Mock mode exists for offline development but doesn't catch server
   regressions.
2. **No model state isolation**. Some `simtalk_run` cases mutate model state
   (`var x := 3` then `x := 5`). The runner does not snapshot/restore — tasks
   are designed to be idempotent where possible. Cross-test contamination is
   possible if a task leaves side effects; flag and avoid in `tags: ["side-effect"]`.
3. **v15+ readlog behavior is documented as unreliable**. Tasks in
   `04-quirks.json` only verify the *runner* correctly surfaces this, not the
   server-side capture correctness.
4. **Modal trap tasks are expected to hang**. They validate that the runner
   has a timeout, not that the server should answer. The runner must NOT mark
   them as failures — they're tagged `expected_timeout` and verified by
   timeout-bucket attribution.

---

## 7. Extending the Suite

To add a task:

1. Pick the right category file (or create a new one if it's a new dimension).
2. Write the JSON task per §3.2 schema.
3. Pick predicates per §3.3 — be **specific**. `result_excludes: ["hasError"]`
   is more useful than `exit_code: 0` alone because it survives schema drift.
4. Add at least one Quirk-complying variant for every new `type` you test.
5. Document the source in the task `tags` (e.g., `lifelines-§6`, `v9-R5`).
6. Re-run the suite and confirm pass rate is ≥ 95%.

See `CONTRIBUTING.md` for the full review checklist.