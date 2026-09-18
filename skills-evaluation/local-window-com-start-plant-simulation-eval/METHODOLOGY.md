# Evaluation Methodology — `local-window-com-start-plant-simulation`

> The evaluation framework for the `local-window-com-start-plant-simulation`
> skill. Defines what "good" means, how it's measured, and how the results
> should be interpreted.

---

## 1. Scope

`local-window-com-start-plant-simulation` is a **subprocess wrapper** around
`win32com.client.Dispatch("Tecnomatix.PlantSimulation.RemoteControl.26.6")`.
It has these observable behaviors we can test:

| Behavior | Surface | Hermetic? |
|---|---|---|
| **CLI validation** | exit 2 (bad args) / 4 (file not found) + stderr message | yes (no COM touched) |
| **Exit code matrix** | all 5 documented codes (0/2/3/4/5) reachable from documented triggers | yes for 2/4/5; 3 needs COM or wait-ready |
| **COM error handling** | known HRESULTs → right hint + exit 3 | needs real PS *or* `--mock` |
| **Path normalization** | `os.path.abspath` applied, error msg shows abs path | yes |
| **stdout/stderr discipline** | success lines on stdout, progress + errors on stderr | yes |
| **`--wait-ready` polling** | TCP poll loop, ConnectionRefusedError tolerated, timeout → exit 3 | yes (any TCP port) |
| **`--print-pid` tasklist parse** | stdout lists PIDs when --print-pid set | yes (no PIDs → warning to stderr) |
| **Lifelines L1–L6 compliance** | hard rules in `references/lifelines.md` | mixed (L1/L4/L6 = yes; L2/L3/L5 = needs PS) |

Integration tasks (the happy path: load a real `.spp`, inject a real
`.pslib`, change port, wait for socket) require a real
`Plant Simulation.exe` and a real model. **All other tasks are hermetic.**

This is materially different from `local-simtalk-execution-eval` (which tests
an in-process TCP client) because:

- **Out-of-process** — we test the wrapper, not a library. Mock mode
  replaces `win32com.client.Dispatch` with a recorder.
- **Side effects** — a real integration run launches a GUI process that
  persists after the script exits.
- **COM singleton** — only one `Plant Simulation.exe` at a time. Tasks are
  serialized.
- **Different "success" predicate** — exit code + stderr/stdout shape, not
  TCP round-trip.

---

## 2. The Seven Evaluation Dimensions

| # | Dimension | What it measures | Why it matters |
|---|---|---|---|
| 1 | **CLI Validation Precision** | did the right exit code (2 or 4) + the right error string come out for bad args | wrong exit code = downstream agent loops incorrectly |
| 2 | **Exit Code Compliance** | does every documented trigger produce the documented exit code | the calling agent's if/elif chain depends on these codes |
| 3 | **COM Error Hint Fidelity** | do known HRESULTs (0x80040154, 0x80080005, 0x80020009) print the right hint | operator is told the right next step |
| 4 | **Path Normalization** | does the script abspath-ify paths and show the abspath in error msgs | CI workers with weird cwds need this to debug |
| 5 | **stdout/stderr Discipline** | success lines → stdout; progress + errors → stderr | CI pipelines pipe stdout for status, stderr for alerts |
| 6 | **`--wait-ready` Protocol** | does it poll, tolerate ConnectionRefusedError, time out cleanly with exit 3 | the only "self-testable" integration prep step |
| 7 | **Lifelines L1–L6 Compliance** | does the skill enforce every hard rule in `lifelines.md` | lifelines are non-negotiable; a regression = silent production failure |

### 2.1 CLI Validation Precision

Each task declares which CLI args to pass. The grader checks:

- **exit code** matches the documented code for the trigger (e.g., missing
  `--simtalkclaudefile` → argparse error → exit 2)
- **stderr** contains the expected error substring (e.g., `"Port must be in 1..65535"`,
  `"Model file not found"`, `"SimtalkClaude library not found"`)

Wrong exit code cases (e.g., port-out-of-range returning 5 instead of 2) are
counted as **precision errors**.

**Why it's separate from exit-code compliance**: a skill can exit 2 with a
vague message (still a precision bug), or exit 5 instead of 2 (a compliance
bug). They measure different things.

### 2.2 Exit Code Compliance

For each documented exit code, the suite must show the trigger is reachable:

| Code | Trigger | Hermetic? |
|---|---|---|
| **0** | success — COM dispatch + LoadModel + inject + changeport all OK (integration task) | needs real PS |
| **2** | bad CLI args (missing required, port out of range, non-int port) | yes |
| **3** | COM error *or* `--wait-ready` timeout *or* socket OSError | `--wait-ready` yes; COM no |
| **4** | `--model` or `--simtalkclaudefile` path doesn't exist | yes |
| **5** | uncaught exception (the catch-all) | yes (via injected fault) |

The suite tests **every cell** of this matrix. If a code becomes unreachable
(e.g., a refactor accidentally catches `ValueError` and returns 5), the
suite flags it.

### 2.3 COM Error Hint Fidelity

`references/lifelines.md` documents three known HRESULTs and the hints the
script should print for each:

| HRESULT | Meaning | Required hint substring |
|---|---|---|
| `0x80040154` | class not registered (PS not installed / COM not registered) | `class not registered` + `regsvr32` |
| `0x80080005` | COM server launch failed (singleton held by another PS) | `taskkill` + `Plant Simulation.exe` |
| `0x80020009` | `DISP_E_EXCEPTION` — SimTalk execution failure (e.g., bad inject) | `lifelines.md` *or* `--allow-message-box` |

A regression that strips the hint = the operator gets a raw hex code and
no actionable next step. Quirk-tagged.

### 2.4 Path Normalization

Two properties to verify:

1. **Relative path in → absolute path in error msg.** If the caller passes
   `--model foo.spp` and `foo.spp` doesn't exist, the error must show the
   *abspath the script computed*, not the relative one. This is what
   `os.path.abspath(model_path)` is for.
2. **Whitespace / non-canonical paths** — the script must call `os.path.abspath`
   before `os.path.isfile`, not the other way around. The grader checks
   this by passing a relative path that exists when joined to cwd and
   verifying the error message uses the resolved form.

### 2.5 stdout/stderr Discipline

The contract (from `references/cli-args.md` §"Output format"):

- **stdout**: success lines (`socket ready after ...`,
  `Plant Simulation launched, model loaded, socket port set to <port>.`,
  `Plant Simulation PID: [...]`)
- **stderr**: progress (`Waiting for socket on ...`), warnings
  (`--print-pid` requested but no PS), and errors (`Error: ...`,
  `COMError: ...`)

The grader parses both streams separately. A regression that sends
`Error: ...` to stdout (or `Plant Simulation launched ...` to stderr) is
flagged.

### 2.6 `--wait-ready` Protocol

The poll loop in `wait_for_socket()` is testable without a real PS:

- **Connect to a known-busy port** → `ConnectionRefusedError` → loop, no
  panic. Eventually → `TimeoutError` → exit 3.
- **Connect to a port that is listening** (e.g., the runner opens a
  throwaway listener) → `socket.create_connection` succeeds → "socket ready
  after Xs" on stdout → exit 0 (assuming everything else succeeds).
- **Default (`--wait-ready 0`)** → skip the poll entirely. No
  `Waiting for socket` line on stderr.

Tasks in this dimension don't touch COM — they bypass the script's COM
init by using `--mock` mode where the mock records but doesn't dispatch.

### 2.7 Lifelines L1–L6 Compliance

The hard rules in `references/lifelines.md` become testable predicates:

| ID | Rule | Test |
|---|---|---|
| L1 | SimtalkClaude must be loaded before changing port | The script calls `basis.loadObjectAs` *before* `.SimtalkClaude.Main.SocketServer.mysocket.port:=...`. The order is observable in `--mock` mode. |
| L2 | COM singleton — only one PS at a time | The script does NOT check / enforce; this is a *documented behavior*, not a script guarantee. Lifeline task verifies the doc is intact. |
| L3 | `SetNoMessageBox` default is True | Default invocation (no `--allow-message-box`) sets `no_message_box=True`. Verifiable via mock. |
| L4 | Paths should be absolute | `os.path.abspath` is called before `os.path.isfile`. See §2.4. |
| L5 | `--wait-ready` doesn't verify protocol | Documented; no test needed beyond confirming the doc. |
| L6 | `pywintypes` import failure handled gracefully | Inject a fake `ImportError` for `pywintypes` and verify the script raises `RuntimeError("pywin32 (win32com) is required...")` instead of `NameError`. |

Tasks tagged `lifeline-L1` ... `lifeline-L6`. Any regression = auto-fail.

---

## 3. Task Suite Design

### 3.1 Categories

9 files in `tasks/`, one per category:

| File | Tasks | What it covers |
|---|---:|---|
| `01-cli-validation.json` | 7 | missing `--model`, missing `--simtalkclaudefile`, bad port (0/65536/abc), unknown flag |
| `02-com-errors.json` | 4 | 0x80040154, 0x80080005, 0x80020009, unknown HRESULT → generic hint |
| `03-model-load.json` | 5 | happy path (integration), relative path → abs, no such file, SetTrustModels called, no overwrite without warning |
| `04-injection.json` | 3 | `basis.loadObjectAs` called with right path, with quotes escaped, with `(true, false)` flags |
| `05-port-change.json` | 3 | `changeport_command` has the right shape, default 50007, custom port |
| `06-wait-ready.json` | 5 | skip on default, busy port → timeout, listener up → ready, host unreachable, negative timeout |
| `07-print-pid.json` | 3 | PID list printed, warning when not found, no warning when not requested |
| `08-lifelines.json` | 6 | L1–L6 each as a test |
| `09-exit-codes.json` | 5 | every code reachable from its documented trigger (mini matrix) |

Total: **~41 tasks**. Most are hermetic; ~5 are integration (need real PS).

### 3.2 Task Schema

```json
{
  "id": "cli-001-missing-model",
  "category": "cli-validation",
  "name": "missing --model → exit 2 + argparse error",
  "args": ["-s", "C:/lib/SimtalkClaude.pslib"],
  "mock": true,
  "timeout": 5,
  "weight": 1,
  "expected": {
    "exit_code": 2,
    "stderr_includes": ["required", "--model"],
    "stdout_empty": true
  },
  "tags": ["smoke", "hermetic", "exit-2", "cli-args-§exit-codes"]
}
```

| Field | Required | Meaning |
|---|---|---|
| `id` | ✓ | unique slug |
| `category` | ✓ | bucket for reporting |
| `name` | ✓ | human-readable |
| `args` | ✓ | list of CLI args (passed verbatim to the script) |
| `mock` | ✓ | `true` = use fake `win32com.client` (no PS needed); `false` = real COM |
| `timeout` | ✓ | seconds; runner enforces |
| `weight` | optional | default 1; used for weighted pass rate |
| `expected` | ✓ | grader predicates (see §4) |
| `tags` | optional | for filtering (`smoke`, `regression`, `lifeline-L1`, ...) |

### 3.3 Expected Verdict Vocabulary

Predicates the grader supports:

| Predicate | Meaning |
|---|---|
| `exit_code: int` | exact match |
| `exit_code_in: [int, ...]` | one-of |
| `stderr_includes: [str, ...]` | all substrings present in stderr |
| `stderr_excludes: [str, ...]` | no substring present in stderr |
| `stdout_includes: [str, ...]` | all substrings present in stdout |
| `stdout_excludes: [str, ...]` | no substring present in stdout |
| `stdout_empty: bool` | `true` means stdout must be exactly empty |
| `stderr_empty: bool` | `true` means stderr must be exactly empty |
| `wall_time_max_ms: int` | upper bound on wall time |
| `mock_call_sequence: [str, ...]` | ordered list of method names the mock must have seen |

Multiple predicates combine with **AND**.

### 3.4 Mock Mode

When `mock: true`, the runner injects a fake `win32com.client` into the
script's process via `PYTHONPATH` (a `_mock_win32com.py` shim). The shim:

- Implements `Dispatch(progid)` → returns a `MockRemoteControl` object.
- The `MockRemoteControl` records every method call in a list.
- Default `MockRemoteControl` returns success for everything; tasks can
  override via `mock_setup` to inject faults (HRESULTs, exceptions, etc.).

For `mock: false` (integration), the runner:
1. Asserts the script's required environment is present (pywin32 importable,
   `win32com.client.Dispatch("...RemoteControl.26.6")` doesn't fail).
2. Records the script's call sequence via the real COM proxy.
3. Asserts the host's `Plant Simulation.exe` process appears (or was
   already there).
4. **Does NOT** auto-cleanup — the calling agent decides.

---

## 4. Grader Design

```
observed_run  ─┐
                ├─► Grader.grade(task, observed_run) → GraderResult
task.expected ──┘
```

`GraderResult` records:

- `verdict`: `pass` | `fail` | `inconclusive`
- `bucket`: failure attribution (per §5)
- `failed_predicates`: which predicates failed (for actionable feedback)
- `observed`: raw exit code, stdout, stderr, wall time, mock call sequence

A task is `inconclusive` when the runner itself errored out before grading
(e.g., subprocess didn't start, mock shim failed to import). These are
reported separately and excluded from pass-rate calculations.

---

## 5. Failure Attribution Buckets

| Bucket | Trigger |
|---|---|
| `wrong_exit_code` | exit ≠ expected |
| `stderr_missing_required` | a `stderr_includes` substring absent |
| `stderr_has_unexpected` | a `stderr_excludes` substring present |
| `stdout_discipline` | a stdout predicate failed (e.g., `Plant Simulation launched` accidentally on stderr) |
| `mock_call_mismatch` | `mock_call_sequence` doesn't match (L1 / L3 / etc.) |
| `wait_ready_timeout_unexpected` | --wait-ready timed out when it shouldn't have (or vice versa) |
| `com_error_hint_wrong` | wrong hint printed for a known HRESULT |
| `mock_setup_failed` | the mock shim didn't load |
| `subprocess_did_not_start` | `FileNotFoundError` on the script path |
| `inconclusive` | anything else |

The report prints a **bucket histogram** so a regression is immediately
actionable ("6 more `wrong_exit_code` failures this week → refactor broke
the exit-code dispatcher").

---

## 6. Variance & Regression Protocol

### 6.1 Per-run pass rate

For each task, run N times. Pass rate = (number of runs where verdict=pass) / N.

A task is **flaky** if pass rate < 80%. Flaky tasks are reported but don't
auto-fail the suite (they're flagged for investigation).

Hermetic tasks (no COM, no socket) should be 100% deterministic. Flakiness
there is a real bug.

### 6.2 Cross-version regression

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

### 6.3 CI gate suggestion

Recommended CI invariant (in `reports/summary.md`):

- ≥ 95% overall weighted pass rate
- 0 new flaky tasks
- 0 regression in `08-lifelines.json` (Lifeline compliance is non-negotiable)
- 0 wrong exit code (every documented code reachable)

---

## 7. Limitations

1. **Real PS is required for integration tasks.** The hermetic tasks (CLI
   validation, exit code matrix, COM error hints) run fine under `--mock`,
   but the happy-path integration case (load model + inject + change port)
   needs a real `Plant Simulation.exe` to validate end-to-end.
2. **No parallel integration runs.** Plant Simulation is a COM singleton;
   the runner serializes integration cases.
3. **No auto-cleanup of `Plant Simulation.exe`.** A successful integration
   run leaves the GUI process running. CI must explicitly tear it down
   (e.g., `taskkill /IM "Plant Simulation.exe" /F`).
4. **`--mock` covers validation tasks only.** The mock replaces
   `win32com.client.Dispatch` with a recorder. It validates the CLI
   surface, exit-code logic, and call-order (L1/L3). It does NOT validate
   the COM wire protocol.
5. **No model-state isolation.** Integration tasks that load a `.spp` will
   actually load it; subsequent tasks see the loaded model. Cross-test
   contamination is possible if you run integration tasks in a sequence.
   Use `--task-id` to isolate when debugging.
6. **L2 (singleton) and L5 (wait-ready limits) are documentation-only
   tests** — the skill documents them but does not enforce them in code.
   The lifeline tasks verify the *doc* matches the *intent*; they cannot
   verify runtime behavior without infrastructure we don't have.

---

## 8. Extending the Suite

To add a task:

1. Pick the right category file (or create a new one if it's a new dimension).
2. Write the JSON task per §3.2 schema.
3. Pick predicates per §3.3 — be **specific**. `stderr_includes:
   ["regsvr32"]` is more useful than `exit_code: 3` alone because it
   survives refactors.
4. Set `mock: true` unless you specifically need real PS.
5. Cite the source in `tags` (e.g., `lifelines-§1`, `cli-args-§exit-codes`,
   `v9-R5`).
6. Re-run the suite and confirm pass rate is ≥ 95%.

See `CONTRIBUTING.md` for the full review checklist.
