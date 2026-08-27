# Usage log — local-simtalk-read-library: WorkerChart.* + PalletOptimization core methods on Assembly1

**Date:** 2026-08-27  **Skill:** `local-simtalk-read-library`  **Target:** `.Models.Assembly1.WorkerChart.*` (5 methods) + `.Models.Assembly1.PalletOptimization.*` (11 methods, 16 total)
**Mode / Action:** `probe_methods.py` batch (size 8) + custom multi-line TSV re-parser  **Operator:** plant-simulation-expert

## Goal

Read the assembly-line business-logic SimTalk source on the user's current
loaded model (different from yesterday's Factory51). Focus:
- `WorkerChart.*` — 5-method custom UI Frame embedded inside Assembly1
- `PalletOptimization` experiment-manager spine — Start, prepExp, evalRules,
  performRule, EndSim, reset, setParameter, evalExpTable, makeJobTable,
  storeParam, restoreParam

## Steps

1. **Pre-flight ✅** — `host.docker.internal:50007` CONNECTED; `ping` → `success`.
2. **Targeted path list (16 paths)** — built `/tmp/learning_method_paths.txt`
   by hand from cached `models_d2.json` (`WorkerChart.*` known at depth=2;
   `PalletOptimization.*` methods extracted from raw stdout of failed
   `bfs_one_level.py` call that hit readlog truncation at character 11971).
3. **Probe via `probe_methods.py`** (batches of 8):
   ```bash
   python3 scripts/probe_methods.py /tmp/learning_method_paths.txt \
     /tmp/learning_methods_raw.tsv
   # → 16 methods, calls=4 batches (8+8)
   ```
4. **Render via `render_library.py`**:
   ```bash
   python3 scripts/render_library.py /tmp/learning_methods_raw.tsv \
     /tmp/learning_library_dump.json
   # → wrote JSON but `program` field truncated to first comment line
   ```
5. **Detected renderer bug** — `program_len` field is correct but
   `program` field only contains the leading comment line. Root cause:
   `probe_methods.py` writes the program body with REAL newlines, but
   `render_library.py` parses with `for ln in f: ln.split("\t")` which
   treats each line as a separate row. The continuation lines lack the
   8-field header and so the program body is lost on every multi-line
   method.
6. **Workaround: custom TSV re-parser** — wrote a python parser that
   recognizes a method-start header line (path + tab + name + tab +
   Method/Frame/Variable/DataTable + tab + ≥6 more tabs) and accumulates
   body lines until the next header. Reconstructed all 16 methods with
   full source (-25 to -87 char diff vs declared `program_len`, all
   attributable to LF normalization).
7. **Source dump to `/tmp/learning_library_full.json`** for downstream
   reading.

## Result

- 16/16 methods captured, 0 encrypted, 0 syntax errors, 0 empty.
- PalletOptimization.Start (9673B) is the largest; WorkerChart.init (145B)
  smallest.
- All methods legible — none encrypted.

## Verdict

**PASS** for reading source via probe.
**FAIL (renderer bug)** for `render_library.py` — silently drops multi-line
program bodies on every Method. Affects ANY method with >1 line of code.
**Workaround** (custom TSV re-parser) shipped to `/tmp/`.

## What this run validated / learned

### Concrete reading on the current loaded model

**WorkerChart** is a **Frame-with-5-methods + Dialog + 2 DataTables**
custom UI for visualizing `WorkerPool` utilization over time:
- `init` (145B) — guards `VarObj /= void`, calls `GetWorkersFromPool`,
  `switchRadioButton`, `Refresh`.
- `DragAndDrop` (893B) — accepts drop of object whose `internalClassname`
  == `"NwWorkerPool"`, then sets dialog caption + `Open` + populates
  `myWorkerTable`.
- `Open` (1289B) — uses **SimTalk 2.0 syntax** (`is`/`do`/`inspect`/`when`/
  `end;`). Restores persisted settings (VarInterval, VarChartType,
  VarPointOfView, VarStatisticGroup) into dialog widgets.
- `CallBack` (3708B) — UI event router via `switch item ... case`. Handles:
  radio buttons for "Worker/Group/Pool" grouping, "Working time/Overall
  time" occupancy metric (copies `myWorkingTimeStatisticTable` /
  `myOverallTimeStatisticTable` → `myStatisticTable`), Apply button
  (validates WorkerPool type + `eventController.isRunning` guard), help
  menus (`HTMLHelp`, `openBox`).
- `Refresh` (3152B) — the rendering core. `Transpose(myStatisticTable,
  myBufferTable)` to flip rows/cols, then constructs `Chart.InputChannels`
  rows based on `VarStatisticGroup`: for "Worker" uses `MakeString(...)`
  per worker; for "Group" sums over `myWorkerClasses[i, WorkerNo]` with
  `(s)/numWorkers` division for non-Pie charts; for "Pool" concatenates
  with `+` then `(s)/numWorkers`.

**PalletOptimization** is a **custom ExperimentManager** (a richer
re-implementation of `.Tools.ExperimentManager`). Key findings:

- **`Start`** (9673B) — full state machine over 4 states
  (`stopped`/`wait4stop`/`running`/`ready`). Two paths: `stopped` →
  resume next experiment; `ready` → start fresh study. Validates:
  computer access (saveExcelatEnd / saveHTMLatEnd / MailAtEnd),
  Remote machines table, EventController present + has `End` time,
  ValueDescriptions registered, Output/Input tables defined. For
  distributed sim optionally saves model (`askForSaveModel` messagebox),
  then `DistributedSimulation.Start` triggers callbacks
  `M_NewJobId` → `M_setParams` → `M_ReadResult`. For non-distributed:
  reset eventController, `DefSeed4Run`, prepares `DetailedResults` /
  `Protocol` / `ProgressTable`. Iterates experiments calling
  `prepExp(ExpNo)`.
- **`evalRules`** (2899B) — **rule engine**. Reads `Rules.Rules` table
  (cols: priority, name, condition_table, condition_method,
  action_table, action_method, active, init_rule, valid_for_exps).
  Sorts by priority desc. For each rule: checks `Rules.TestConditionExp`
  + condition_method → if satisfied, executes `Rules.DoActionExp` +
  optional method action. **Init-rules** only fire on experiment 1.
  **Non-init rules** must satisfy `Rules.validExp(s)` for the current
  experiment number. Per-column fallback: if `InputValues[col, localExp]
  == void`, inherit from `InputValues[col, localExp-1]`.
- **`performRule`** (971B) — single rule executor: composite condition =
  `Rules.TestConditionExp(table_condition)` AND `method_condition.execute`
  ; composite action = `Rules.DoActionExp` + optional method action.
- **`EndSim`** (360B) — calls `&endOfSim.executeNewCallChain(false)` for
  continuation + `&SingleRunFinished.executeNewCallChain` if SingleRun.
- **`reset`** (712B) — first reset triggers `DefExperiments` chain
  (which calls `evalRules` → `performRule`), subsequent resets call
  `eventController.start`. If `dialog.restoring`, then `restoreParam`.
- **`setParameter`** (856B) — writes input values from `ExpTable` to
  actual model attributes via `writeValue(AttrStr, AttrVal)`, then
  `DefSeed4Run(ExpNo, ObsNo)`. Supports custom `UserConfigMethod`
  (e.g., `setCreationTable`).
- **`makeJobTable`** (1544B) — creates per-run job entries in
  `JobsTable` (cols: ExpNo, RunNo, status), populates `ProgressTable`
  for visualization, calls `ProgressTable.refillDialog` to refresh UI.
- **`storeParam`/`restoreParam`** (1387B/2545B) — snapshot baseline
  attribute values into `Kind_Input[2,j]`, restore via `executeSilent`
  using type-aware `str_to_time` / `str_to_length` / `str_to_speed` /
  `str_to_acceleration` / `str_to_weight` dispatch. Handles WorkerPool
  `creationTable` inheritance via `o.setCreationTable(void)` /
  `o.inheritAttribute(AttrName)`.

### Key architectural observations

1. **PalletOptimization ≡ ExperimentManager rewrite** — implements the
   same lifecycle as `.Tools.ExperimentManager` but with custom rules
   engine, distributed-simulation hooks, advanced reporting
   (`makeReport` → `HtmlReport`), and rich dialog (`Dialog` Frame with
   `openWizard`, `resetWizard`, `prepExp`, `ShowReport`, etc.).
2. **Same code lives in `.Models.Assembly2.BufferOptimization`** —
   numNodes=135 in both (proved via failed BFS that printed identical
   method list up to char 11971). Means the user duplicated the
   PalletOptimization Frame and renamed it — risk of drift.
3. **WorkerChart = textbook custom UI Frame pattern** — Frame +
   Dialog + 2 DataTables + VarObj (Variable for state) + chart-internal
   controls. The 5 methods split cleanly: init / DragAndDrop / Open
   (SimTalk 2.0 syntax) / CallBack (event router) / Refresh (render).
4. **`NwWorkerPool` is the worker-pool class** (vs generic `WorkerPool`)
   — internalClassname check in DragAndDrop guards the type.
5. **SimTalk 2.0 syntax is selectively used** — WorkerChart.Open uses
   `is ... do ... end;` + `inspect ... when ... end;` + `then` clauses;
   all other methods use SimTalk 1.0 (`if ... end` + `case`). Probably
   because `Open` was rewritten later.

### Renderer bug discovered (worth a separate fix PR)

`scripts/render_library.py` line 32–35 splits TSV rows on `\t` but does
NOT handle the case where the `program` field contains embedded
newlines. As a result, for any Method with multi-line source, only the
first line of the body is preserved in the `program` field of
`library_dump.json`. The fix is to either:
- (a) have `probe_methods.py` replace `\n` with a sentinel (e.g.,
  `\\n`) before writing TSV and have the renderer reverse the
  substitution, OR
- (b) quote-enclose the program field and use a real CSV-style parser.
  Filed for follow-up; **do NOT fix in-session** (out of scope for
  learning).

### Cross-references

- Session summary: `03-agent-memory/plant-simulation-expert-memory/2026-08-27_session-summary_learn-new-assembly-model.md`
- Renderer bug workaround: `/tmp/learning_library_full.json` (custom
  multi-line TSV re-parser output)
- Raw probe output: `/tmp/learning_methods_raw.tsv`
- Method-path list used: `/tmp/learning_method_paths.txt`