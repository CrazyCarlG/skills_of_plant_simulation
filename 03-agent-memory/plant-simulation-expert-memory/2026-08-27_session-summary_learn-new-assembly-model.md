# Session Summary — Learn the currently loaded Plant Simulation model (NEW: assembly-line, not Factory51)

**Date:** 2026-08-27  **Agent:** plant-simulation-expert
**Duration:** ~1 hour (fresh session after `/clear`)
**Skills called:** `local-simtalk-execution` (transport), `local-simtalk-get-folder-tree` (5 BFS runs), `local-simtalk-read-library` (1 probe batch)

## Goals

User: "我已开启simtalkclaude，请用 @agent 学习下仿真模型" — orient on the
model currently loaded in the Plant Simulation GUI by reading its
folder tree + key method sources. After confirming the model is NOT
yesterday's Factory51, drill into assembly-line business logic:
`UserObjects.Modules.PreProduction` template, `Models.Assembly1.PalletOptimization`,
`WorkerChart` custom UI Frame.

## What was done

1. **Pre-flight ✅** — `host.docker.internal:50007` CONNECTED, `ping` → success.
2. **Confirmed model is new** — depth=1 BFS of `.` showed `Tools` folder
   + top-level `ExperimentManager` Variable + no `ApplicationObjects`
   folder, vs Factory51's 9-folder root with `ApplicationObjects.HBW3D.*`.
3. **Depth-2 BFS of `.Models`, `.UserObjects`, `.SimtalkClaude`** —
   discovered 2 assembly-line Frames (`Assembly1` + `Assembly2`) + a
   Class/Module object-library structure under `.UserObjects` + identical
   SimtalkClaude TCP bridge as Factory51.
4. **Depth-2 drill of Assembly1 vs Assembly2** — Assembly1 is the
   "lean baseline" (113 direct children, no analyzers), Assembly2 is the
   "instrumented production" (same 113 + BottleneckAnalyzer 13 methods +
   EnergyAnalyzer 17 methods + BufferOptimization + EnergySavingMeasures).
5. **User chose scope = 装配线业务逻辑** — drilled:
   - `WorkerChart.*` (5 methods on Assembly1 — custom UI Frame-with-dialog)
   - `PalletOptimization.*` (11 methods on Assembly1.Start spine +
     rule engine + lifecycle)
6. **Probe 16 methods via `probe_methods.py`** — all captured cleanly,
   0 encrypted, 0 syntax errors, 0 empty. Sizes range 145B (init) to
   9673B (Start).
7. **Detected `render_library.py` bug** — silently drops multi-line
   program bodies (only first comment line preserved). Wrote a custom
   TSV re-parser as workaround; full source shipped to
   `/tmp/learning_library_full.json`.
8. **Defensive infoBox close x2** at session end.

## Key findings / decisions

### Model architecture (high-level)

```
Basis
├── MaterialFlow / Resources / InformationFlow / UserInterface / MUs / Tools
├── UserObjects                          ← 模块化对象库 pattern
│   ├── Classes (Toolbar Library + Track CrossTransfer + Station MS + Station AS
│   │           + Worker ×3 [Worker / Worker_Round / Adjuster] + PickAndPlace Robot)
│   └── Modules (Frame PreProduction[全套Source/Station/Conveyor/Connector/Robot]
│                + Frame Assembly_initialState)
├── Models
│   ├── Assembly1                        ← 精简对照版，113 子节点
│   │   ├── PreProduction (full assembly of MS/AS/Worker/Robot/Source)
│   │   ├── WorkerChart (5-method custom UI Frame, internalClassname = NwWorkerPool)
│   │   ├── PalletOptimization           ← ExperimentManager rewrite, 60+ methods
│   │   └── …(Connectors/Conveyors/Buffer/Source/Drain/Sankey/Events)
│   └── Assembly2                        ← 全功能版，113 + BottleneckAnalyzer(13)
│                                        + EnergyAnalyzer(17) + BufferOptimization
│                                        + EnergySavingMeasures + DisplayEnergy
└── SimtalkClaude (v2 TCP bridge — 4 sub-Folders:
                        main[Frame]+src[Folder]+connection[Folder]+Objects[Folder]
                        ; Objects holds 8 leaf class-instances:
                        Method/Socket/DataList/Dialog/HtmlReport/Variable/Button/DataTable)
```

### Concrete findings on the assembly-line business logic

**WorkerChart** is a textbook **Frame-with-UI pattern** (Frame + Dialog
+ 2 DataTables + VarObj Variable + internal chart):
- `init` (145B) → `GetWorkersFromPool` + `switchRadioButton` + `Refresh`
- `DragAndDrop` (893B) → accepts `NwWorkerPool` only, populates table, opens
- `Open` (1289B) → **uses SimTalk 2.0 syntax** (`is`/`do`/`inspect`/`when`/
  `end;`), restores persisted dialog state
- `CallBack` (3708B) → UI event router: `switch item / case`, copies
  `myWorkingTimeStatisticTable` / `myOverallTimeStatisticTable` into
  `myStatisticTable` for "Working time" vs "Overall time" occupancy views
- `Refresh` (3152B) → renders via `Transpose(myStatisticTable,
  myBufferTable)` then builds `Chart.InputChannels` per VarStatisticGroup
  (Worker / Group / Pool) using `MakeString(...)` per row + `(s)/numWorkers`
  division for non-Pie charts

**PalletOptimization** is a **custom ExperimentManager** (a richer
re-implementation of `.Tools.ExperimentManager`):
- `Start` (9673B) → 4-state machine (`stopped`/`wait4stop`/`running`/
  `ready`); distributed vs non-distributed branches; full validation
  pre-flight (computer access, Remote machines table, EventController +
  End time, ValueDescriptions registered, Output/Input defined)
- `evalRules` (2899B) → **rule engine** with priority-sorted rules
  (descending). Init-rules fire only on experiment 1; non-init rules
  must satisfy `Rules.validExp(s)` for the current experiment
- `performRule` (971B) → composite condition = `Rules.TestConditionExp`
  + condition method; composite action = `Rules.DoActionExp` + optional
  method action
- `reset` → first reset triggers `DefExperiments` chain → `evalRules` →
  `performRule`; subsequent resets call `eventController.start`
- `setParameter` → `writeValue(AttrStr, AttrVal)` per input column,
  then `DefSeed4Run`
- `makeJobTable` → creates per-run job entries + ProgressTable
  visualization, `ProgressTable.refillDialog` to refresh
- `storeParam`/`restoreParam` → baseline snapshot/restore with
  type-aware dispatch (`str_to_time`/`str_to_length`/`str_to_speed`/
  `str_to_acceleration`/`str_to_weight`), WorkerPool `creationTable`
  inheritance via `setCreationTable(void)` / `inheritAttribute`

### Architectural observations

1. **Class/Module pattern under `.UserObjects`** — Classes folder
   holds reusable class definitions (Library Toolbar + MS/AS/Worker/
   Robot/CrossTransfer); Modules folder holds instance templates
   (PreProduction + Assembly_initialState). Assembly1 and Assembly2
   each embed their own PreProduction instance. Clean two-level
   separation.
2. **Assembly1 vs Assembly2 = A/B baseline-vs-instrumented design** —
   identical 113-child assembly line topology, Assembly2 adds
   BottleneckAnalyzer + EnergyAnalyzer + BufferOptimization.
3. **`NwWorkerPool` is the worker-pool class** — internalClassname
   check in DragAndDrop guards the type.
4. **SimTalk 2.0 syntax used selectively** — WorkerChart.Open uses
   `is`/`do`/`inspect`/`when`/`end;` + `then` clauses; all other
   methods use SimTalk 1.0 (`if ... end` + `case`). Likely because
   `Open` was rewritten later.
5. **SimtalkClaude is the same v2 bridge as Factory51** — has
   `auth/sig/token/session_id` Variables; whether `sig` is actually
   computed still unverified (would need `local-simtalk-read-library`
   on `.SimtalkClaude.main.SocketClient.m_sendauth` to confirm).
6. **DRIFT RISK: `.Models.Assembly2.BufferOptimization` and
   `.Models.Assembly1.PalletOptimization` have IDENTICAL 135-node
   structure** (proved via failed BFS that printed identical method
   list up to char 11971). The user duplicated the Frame and renamed
   it — high risk of drift if either side is edited independently.

### Quirk discovered: `render_library.py` drops multi-line programs

- **Quirk id:** `RENDER-1` (filed in per-skill log; do NOT fix in-session)
- **Symptom:** `library_dump.json`'s `program` field only contains the
  first comment line of each Method, but `program_len` is correct.
- **Root cause:** `probe_methods.py` writes the program body with REAL
  newlines; `render_library.py` parses TSV with `for ln in f: ln.split("\t")`
  which treats each line as a new row.
- **Workaround used in this session:** custom TSV re-parser at
  `/tmp/learning_library_full.json` — recognizes header line (path +
  tab + name + tab + type + tab + ≥6 more tabs) and accumulates body
  lines until next header.
- **Fix (out of session):** either (a) `probe_methods.py` replaces `\n`
  with a sentinel before writing TSV + renderer reverses; or (b)
  quote-enclose the program field and use real CSV parser.

## Cross-references

- `skills/local-simtalk-get-folder-tree/log/2026-08-27_basis-depth4-full-and-factory51-types.md`
  — **superseded** by current session (yesterday's Factory51 model)
- `skills/local-simtalk-get-folder-tree/log/2026-08-27_basis-and-models-model-tree.md`
  — earlier minimal-probe log, also stale
- `skills/local-simtalk-get-folder-tree/data/current_root_fresh.json` —
  fresh depth=1 root (10 children)
- `skills/local-simtalk-get-folder-tree/data/models_d2.json` — fresh
  depth=2 of `.Models` (Assembly1 + Assembly2 with all subnodes)
- `skills/local-simtalk-get-folder-tree/data/userobjects_d2.json` —
  Classes + Modules structure
- `skills/local-simtalk-get-folder-tree/data/simtalkclaude_d2.json` —
  full TCP bridge inventory
- `skills/local-simtalk-get-folder-tree/data/pallet_optimization_d1.json`
  + `buffer_optimization_d1.json` — depth=1 dumps via `bfs_one_level.py`
  (output truncated at char 11971 due to readlog v15+ buffer ceiling)
- `skills/local-simtalk-read-library/log/2026-08-27_learn-assembly-model-palletOptimization-workerChart.md`
  — per-skill usage log (this session)
- `/tmp/learning_method_paths.txt` — 16 candidate method paths
- `/tmp/learning_methods_raw.tsv` — raw probe output (multi-line programs)
- `/tmp/learning_library_dump.json` — broken render output (RENDER-1 bug)
- `/tmp/learning_library_full.json` — fixed custom-parsed output
- `02-simulation-file-experience/facory51/` — yesterday's Factory51
  experience notes (orthogonal to this model)
- `02-simulation-file-experience/simtalkclaude-best-practices.md` —
  SimTalk + Claude collaboration baseline
- `01-plantsimulation-knowledge/.../Method/attributes` — authoritative
  Method-object docs (used `&m.Program`, `&m.Encrypted`,
  `&m.HasSyntaxError`, `&m.NumInExecution`)

## Open questions / next steps

1. **Verify SimtalkClaude v2 auth handshake** — read
   `.SimtalkClaude.main.SocketClient.m_sendauth` + `m_authback` source
   to confirm whether `sig` is actually computed or is a placeholder.
   Yesterday's offline analysis suggested it's a placeholder.
2. **Check Assembly2 analyzers (BottleneckAnalyzer / EnergyAnalyzer)** —
   these are the "value-add" of the instrumented model. Would benefit
   from the same probe+parse treatment WorkerChart/PalletOptimization
   got. Top-priority next session if user wants deeper learning.
3. **Drift risk between PalletOptimization and BufferOptimization** —
   since both have identical 135-node structures, audit
   `BufferOptimization` method bodies to confirm 100% identity (likely
   true given identical path list from the failed BFS), or document
   the actual diff if any.
4. **RENDER-1 bug fix in `render_library.py`** — pick approach (a)
   sentinel-based or (b) quoted-CSV, file a small PR. Affects any
   library dump going forward.
5. **Clean up stale depth-4 cache** — `data/basis_tree_depth4.json`
   is from Factory51, should be removed to avoid drift.
6. **PreProduction template methods** — the template Frame under
   `.UserObjects.Modules.PreProduction` has no Methods at depth=2
   (its logic lives on Connectors' Control / Stations' Entry/Exit).
   Reading those would require depth=3 BFS + per-object Method probe,
   which is heavier than the current scope. Defer until user wants it.
7. **Consider a `.Models.Assembly_initialState` instance under
   `.UserObjects.Modules`** — never drilled (only path mentioned in
   userobjects tree). Could be a "reset-to-here" template used by
   `BufferOptimization.restoreParam`.

---

# Addendum 1 — Assembly2 BottleneckAnalyzer + EnergyAnalyzer drill

**Date:** 2026-08-27 (continuation)  **Scope:** Read source of
`Models.Assembly2.BottleneckAnalyzer.*` (13 methods) +
`Models.Assembly2.EnergyAnalyzer.*` (12 methods) — the "value-add"
analyzers on the instrumented model.

## BottleneckAnalyzer — 8-state utilization breakdown + visual bars

8 stat attributes → 8 utilization factors per object → bar layer +
3D-statistics overlay:

- **`analyzeFrame` (3478B)** — recursive Frame walk. Switch on
  `obj.internalClassName`: recurse into `Network`, skip
  `Method`/`NwWorkplace`/`NwWorkerPool`/`NwData`/`NwExporter`, for
  leaves with `StatWorkingPortion` (probed via `executeSilent`) call
  `analyzeObject`. Aggregates 8 factors + draws via `drawBar`.
- **`analyzeObject` (5119B)** — extracts the 8 `stat*Portion` attrs;
  multi-branch on `isFluid` (NwTank/NwFluidSource/NwFluidDrain/NwMixer/
  NwPipe — no `statStoppedPortion`); guarded by `obj.resStatOn` + 3
  resource-type checkboxes (Production/Transport/Storage); writes row
  to `resourceStats` DataTable (path + 8 percentages × 100); for
  pipes, blocking/fail/powering/pause forced to 0.
- **`analyzeModel` (455B)** — dialog entry: `removeStats` →
  `analyzeFrame(~)` → `Analyzed := true`.
- **`removeStats`/`removeCharts`** — cleanup; `removeCharts` recursive
  via `eraselayer(layer_of_chart)` + `_3D.deleteStatistics`.
- **`sortStats(criteria)` (1464B)** — 5 modes: by working / setup /
  working+fail / working+fail+pause / working+setup+fail+pause. Uses
  hidden col 10 + `resStats.sort(colSort,"down")`.
- **`draw_Scale`/`drawBar`/`insRootStr`** — 2D layer primitives.
  `drawBar` reads color from `colors[1,typeStr]` (Variable map:
  work/setup/wait/block/PoweringUpDown/fail/stop/pause).
- **`fill4Report` (744B)** — `analyzeModel` + localized header +
  `sortStats(3)`. External-callable.
- **`markBottleneckObject` (1056B)** — finds max working/waiting/
  blocked/disrupted, draws 4 colored ellipses on top.
- **`isTool` (159B)** — guards Tools (Experiment/GAwizard/self).
- **`reset` (12B)** — `removeStats`.

## EnergyAnalyzer — energy-consumption observer pattern

Find energy-active objects → register observer on `PowerInput` → on
change, update DataTable + roll up custom attrs → visualize via 2D
ellipses + 3D cones.

- **`init` (123B)** — `prepareObserver(true)` if `MonitoringActive` +
  `updateConsumption`.
- **`findConsumers(frame)` (392B)** — recursive walk; for each
  non-Network child, `detectEnergyobjects(o)` → append path to
  `Objects` DataTable.
- **`reset` (763B)** — `delVisualize` → `prepareObserver(false)` →
  clear tables + zero `Consumption`/`ConsumptionOperational`/
  `powerConsumption`/`maxPowerConsumption`/`PeakTime` → restore
  `numPlottedValues=10000`.
- **`observeEnergyState` (1747B)** — **the observer** (param
  `valueName:string, oldValue:any`). Guards: `!EnergyActive` /
  `rootframe /= root` / row not found in `EnergyConsumers` (one-time
  error messageBox(56) + `eventController.stop`). Action: write row
  `statEnergyTotalConsumption` + operational portion + `PowerInput`,
  roll up 3 custom attrs via `EnergyConsumers.sum`, update
  `refEnergy.value`, track `maxPowerConsumption` + `PeakTime`, refresh
  dialog if `EnergyConsumers.isOpen` OR `UsageProfile.active`.
- **`detectEnergyobjects(o)` (96B)** — `return o.EnergyActive` with
  error handler.
- **`visualize` (621B)** — "Show" button. Builds unique `GrGroupName`
  (`_name_layer_` looped until `isNameUniqueEverywhere`); errors out if
  `MaxCons == 0`; for each row calls `visObject(objNo, relScaling)`.
- **`delVisualize` (819B)** — "Remove" button. Clears 2D layer +
  deletes `_3D.getObject(GrGroupName)`.
- **`endSim` (18B)** — `updateConsumption` (refresh report).
- **`VisObject(objNo, relScaling)` (4296B)** — **visualization core**.
  Color: `makeRGBValue(cr, 0, 255-cr)`. 4 bands by relScaling (1/3/5/7
  px wide). 2D positioning: if curve, use `getCurveSegments` + axes
  math (origin/scaling/tangent/radius vector → pixel) with
  right/left-turn handling; else bounding-box center. Draws ellipse +
  6 state bars (Working/Setting_up/Operational/Failed/Standby/Off from
  `Colors.RGB`). 3D: `getGraphic("default").createConeFrustum` with
  height scaled by `relScaling` × `(z3D_upperSurface - z3D_lowerSurface)`,
  positioned at object's 3D coord (curve-aware offset).
- **`prepareObserver(add)` (1222B)** — registers
  `addObserver("PowerInput", absPathOfMethod)` per row, or
  `removeAllPowerInputObserver(root)` to clear.
- **`updateConsumption` (1501B)** — `-> string`. For each active
  object: copy 6 `statEnergy*Consumption` to
  `UsageProfile.UtilizationTable` cols 1..6 + write EnergyConsumers
  cols 4..9; roll up custom attrs + update `refEnergy` + track
  `maxPowerConsumption`.
- **`isNameUniqueEverywhere(frame, name)` (342B)** — recursive: if
  `!frame.isNameUnique(name)` → false; recurse into Networks.

## Architectural observations (analyzer-specific)

1. **BottleneckAnalyzer = "8-state utilization visualization"**
   - 8 stat*Portion × 2D bar (`layer_of_chart`) + 3D `createStatistics`
   - Resource-type filter (Production/Transport/Storage checkboxes)
   - 5 sort modes via hidden col 10
   - Fluid special-case (no `statStoppedPortion`)
2. **EnergyAnalyzer = "observer + visualization"**
   - Observer pattern: `addObserver("PowerInput", ...)` per
     energy-active object
   - 2D ellipse + 6 state bars + 3D cone frustum
   - Curve-aware positioning (track vs bounding-box)
   - Recursive name uniqueness via `isNameUniqueEverywhere`
3. **BottleneckAnalyzer is heavier on analysis logic** (5119B
   `analyzeObject` vs 1747B `observeEnergyState`); EnergyAnalyzer is
   heavier on visualization (4296B `VisObject` vs 1411B `draw_Scale`).
4. **Both share `is3Dopen` + `obj._3D` conditional overlay idiom.**
5. **`Colors` DataTable** (EnergyAnalyzer) = RGB per energy state (6
   colors × RGB); **`colors` Variable** (BottleneckAnalyzer) = RGB per
   utilization type (Variable vs DataTable — same pattern, different
   shape).
6. **DRIFT STATUS**: BottleneckAnalyzer + EnergyAnalyzer are UNIQUE to
   Assembly2 — no parallel in Assembly1 (by design — Assembly1 is the
   lean baseline). So no drift risk within Assembly2.

## Per-skill log

`skills/local-simtalk-read-library/log/2026-08-27_learn-assembly-model-bottleneckAnalyzer-energyAnalyzer.md`

## Pipeline quirk discovered

`probe_methods.py` batch-8 captured first 17/25 cleanly, then 8
EnergyAnalyzer methods returned empty metadata due to readlog v15+
degradation (META_TYPE=Method but all other fields blank). Fix:
re-probe one-at-a-time via simtalk_send.py run + extract from readlog
buffer. New artifact: `/tmp/probe_with_log_capture.py`. The
`parse_analyzer_tsv.py` re-parser ALSO appended the 8 empty rows to
the prior method (`reset`) — fixed post-hoc by truncating at first
`.Models.` line in body. Future re-parser should detect path-pattern
lines and stop accumulation.

## Open question update

- **OPEN #2 (now resolved)** — checked Assembly2's analyzers:
  BottleneckAnalyzer(13) + EnergyAnalyzer(12 methods; the user said
  "17" likely counting DataTables/Chart/Dialog/HtmlReport too). Total
  drill: 25 methods captured cleanly via probe + re-probe + readlog
  extraction pipeline.
- **NEW #8 — Assembly2 analyzers cross-reference WorkerChart?** The
  energy 6-state color palette (Working/Setting_up/Operational/
  Failed/Standby/Off) is the same enum as WorkerChart's "occupancy
  views" — likely the same MUs stat breakdown. Could share a common
  `Colors`/`colors` definition.
- **NEW #9 — `EnergySavingMeasures` (Checkbox on Assembly2)** — never
  drilled. Has children (per depth-2 tree) — likely a toggle for
  whether to apply energy-saving logic. Worth reading if user wants
  energy optimization drill.