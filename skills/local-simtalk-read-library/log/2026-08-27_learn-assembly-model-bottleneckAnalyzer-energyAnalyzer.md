# Usage log — local-simtalk-read-library: Assembly2.BottleneckAnalyzer + EnergyAnalyzer source

**Date:** 2026-08-27  **Skill:** `local-simtalk-read-library`  **Target:** `.Models.Assembly2.BottleneckAnalyzer.*` (13 methods) + `.Models.Assembly2.EnergyAnalyzer.*` (12 methods) = 25 total
**Mode / Action:** `probe_methods.py` batch-8 + single-method re-probe + readlog-extraction fallback + custom multi-line TSV re-parser
**Operator:** plant-simulation-expert

## Goal

Read the assembly-line analyzer business-logic SimTalk source on
Assembly2 (the "instrumented production" model — vs Assembly1's lean
baseline). Focus: BottleneckAnalyzer (8-state utilization breakdown +
visualization) + EnergyAnalyzer (energy consumption monitoring +
visualization).

## Steps

1. **Pre-flight ✅** — `simtalk_send.py ping` → `result:success`.
2. **Built method path list (25 paths)** — extracted from cached
   `data/models_d2.json` depth-2 walk (BotleneckAnalyzer=13 Methods;
   EnergyAnalyzer=12 Methods + Dialog/Chart/HtmlReport/DataTables which
   don't need probe).
3. **Probe via `probe_methods.py`** (batches of 8 — 4 batches for 25):
   ```bash
   python3 scripts/probe_methods.py /tmp/analyzer_method_paths.txt \
     /tmp/analyzer_methods_raw.tsv
   # → 17/25 captured cleanly; 8 EnergyAnalyzer methods returned empty
   #    (META_TYPE=Method but all other fields blank)
   ```
4. **Custom multi-line TSV re-parser** — applied `parse_analyzer_tsv.py`
   (same logic as `/tmp/learning_library_full.json` from earlier session).
   17/25 captured; `reset` method had TSV contamination (8 empty rows
   appended after end-of-method) — fixed post-hoc by truncating at first
   `.Models.` line.
5. **Re-probed the 8 missing methods one-at-a-time** — readlog v15+
   degradation causes simtalk_run response to truncate when batched;
   single-method probes avoid this. Used simtalk_send.py run + readlog
   extraction at the end:
   ```bash
   python3 /tmp/probe_with_log_capture.py /tmp/analyzer_to_reprobe.txt \
     /tmp/analyzer_reprobe.json
   # → all 8 captured from readlog buffer
   ```
6. **Merged** — `/tmp/analyzer_all_25.json` (25 methods, full source).

## Result

- **25/25 methods captured**, 0 encrypted, 0 syntax errors.
- Sizes: largest = `EnergyAnalyzer.VisObject` (4296B) — the 2D+3D
  visualization core; second = `BottleneckAnalyzer.analyzeObject`
  (5119B) — per-object utilization breakdown.
- Smallest = `EnergyAnalyzer.endSim` (18B, just `updateConsumption`).
- All methods legible — none encrypted.

## Verdict

**PASS** for source capture, with a workaround pipeline:
- `probe_methods.py` batch-8 works for first ~17 methods then readlog
  v15+ degradation returns empty metadata.
- Re-probe one-at-a-time + readlog extraction is the reliable fallback
  when batched readlog goes stale.

## What this run validated / learned

### BottleneckAnalyzer — assembly-line utilization breakdown

**Domain**: per-object `statWorkingPortion` / `statSetupPortion` /
`statWaitingPortion` / `statBlockingPortion` / `statPoweringUpDownPortion` /
`statFailPortion` / `statStoppedPortion` / `statPausingPortion` +
`statUnplannedPortion` → 8-state utilization breakdown → visual bar +
3D-statistics layer.

- **`analyzeFrame(frame)` (3478B)** — recursive walk over a Frame;
  for each `obj.internalClassName == "Network"` it recurses and aggregates;
  for each leaf object that has `StatWorkingPortion` method (probed via
  `executeSilent`), it calls `analyzeObject`. Returns `list[real]` of
  state-factors. Special-cases: `NwTank` / `NwFluidSource` / `NwFluidDrain`
  / `NwMixer` / `NwPipe` (fluid — no `statStoppedPortion`); `Method`,
  `NwWorkplace`, `NwWorkerPool`, `NwData`, `NwExporter` (containers —
  skip). Track-back _3D via `createStatistics(makearray(...))` if 3D open.
- **`analyzeObject(obj)` (5119B)** — extracts the 8 stat*Portion attrs;
  multi-branch on `isFluid`. Guarded by `obj.resStatOn` + 3 checkboxes
  `Production` / `Transport` / `Storage` (resource-type filtering). Writes
  a row to `resourceStats` DataTable (path + 8 percentages × 100). For
  pipes, blocking/fail/powering/pause are forced to 0 (no stats).
- **`analyzeModel()` (455B)** — top-level entry from dialog; calls
  `removeStats` → `analyzeFrame(~)` → sets `Analyzed := true`.
- **`removeStats` / `removeCharts` (324/502B)** — clean up. `removeCharts`
  is recursive (`eraselayer(layer_of_chart)` + `_3D.deleteStatistics`).
- **`sortStats(criteria)` (1464B)** — 5 sort modes:
  - 1: by working time only
  - 2: by setup time only
  - 3: working + fail (default for `fill4Report`)
  - 4: working + fail + pause
  - 5: working + setup + fail + pause
  Uses hidden column 10 as sort key, then `resStats.sort(colSort,"down")`.
- **`draw_Scale` / `drawBar` / `insRootStr` (1411/577/626B)** — 2D layer
  drawing primitives. `drawBar` reads color from `colors[1,typeStr]`
  DataTable (e.g., `"work"` / `"setup"` / `"wait"` / `"block"` /
  `"PoweringUpDown"` / `"fail"` / `"stop"` / `"pause"`).
- **`fill4Report` (744B)** — convenience: `analyzeModel` + writes a
  localized header row + `sortStats(3)`. External-callable.
- **`markBottleneckObject` (1056B)** — finds max-working / max-waiting /
  max-blocked / max-disrupted (4 ellipses drawn on top of objects).
- **`isTool` (159B)** — guards Tool instances (Experiment / GAwizard /
  BottleneckAnalyzer itself) so analyzers don't analyze tools.
- **`reset` (12B)** — just `removeStats`.

### EnergyAnalyzer — energy-consumption observer pattern

**Domain**: find objects with `EnergyActive == true` → register observer
on `PowerInput` attribute → on every change, write to
`EnergyConsumers` DataTable + roll up cumulative `Consumption` /
`ConsumptionOperational` / `powerConsumption` / `maxPowerConsumption` /
`PeakTime` → visualize via 2D ellipses + 3D cones.

- **`init` (123B)** — calls `prepareObserver(true)` if `MonitoringActive`
  + `updateConsumption`.
- **`findConsumers(frame)` (392B)** — recursive walk; for each non-Network
  child, calls `detectEnergyobjects(o)` → if true, append
  `makePathRelative(o,~)` to `Objects` DataTable.
- **`reset` (763B)** — `delVisualize` → `prepareObserver(false)` →
  `EnergyConsumers.delete` + `UsageProfile.UtilizationTable.delete` →
  zero custom attrs (`Consumption` / `ConsumptionOperational` /
  `powerConsumption` / `maxPowerConsumption` / `PeakTime`) → restore
  `numPlottedValues` to 10000 if out of bounds.
- **`observeEnergyState` (1747B)** — **the observer**. Called on
  `PowerInput` change of every energy-active object.
  Guards:
  - `@.EnergyActive == false` → return
  - `@.rootframe /= root` → return (shouldn't happen)
  - `EnergyConsumers.getRowNo(objStr) < 1` → messageBox(56) error +
    `eventController.stop` (one-time via `InfoWasGiven` static)
  Action:
  - write row: `statEnergyTotalConsumption` (kWh) + operational portion +
    `PowerInput` (kW)
  - roll up `Consumption` / `ConsumptionOperational` / `powerConsumption`
    via `EnergyConsumers.sum(...)`
  - update `refEnergy.value` to `" X kWh"`
  - track `maxPowerConsumption` + `PeakTime`
  - if `EnergyConsumers.isOpen` OR `UsageProfile.active` →
    `updateConsumption` (refresh dialog)
- **`detectEnergyobjects(o)` (96B)** — `return o.EnergyActive` with
  error handler (try/catch wrapper).
- **`visualize` (621B)** — "Show" button. Builds `GrGroupName := "_<name>_<abs(layer)>_"` (looping `_` until `isNameUniqueEverywhere(root, GrGroupName)`) → if `MaxCons == 0`, messageBox(55) "no consumption" → for each row, compute `relScaling` and call `visObject(objNo, relScaling)`.
- **`delVisualize` (819B)** — "Remove" button. `Dialog.VisualizationON := false` → for each row (iterate YDimIndex downward), erase 2D layer + delete `_3D.getObject(GrGroupName)` if exists.
- **`endSim` (18B)** — `updateConsumption` (refresh report).
- **`VisObject(objNo, relScaling)` (4296B)** — **the visualization core**.
  - Color gradient: `cr := floor(relScaling*255)` → `makeRGBValue(cr, 0, 255-cr)` (red/blue blend).
  - 4 bands by relScaling: < 0.4 (1px wide, gray) / < 0.7 (3px, mid-blue) / < 0.9 (5px, light-blue) / top 10% (7px, red).
  - 2D positioning:
    - If curve (track): use `obj.getCurveSegments(tabNew)` + axes math
      (origin / scaling factor / curve tangent + radius vector → pixel
      coordinate). Handles both straight segments and right/left turns.
    - Else: bounding-box center.
  - Draw ellipse at center (`drawellipse(layer, mx-R, my-R, 2R, 2R, color, circleWidth)`).
  - Draw 6 small rectangles below for energy-state breakdown (Working /
    Setting_up / Operational / Failed / Standby / Off — columns 4..9 of
    EnergyConsumers) with colors from `Colors.RGB` table.
  - 3D: `analysis.getGraphic("default").createConeFrustum(1, 1, h)` where
    h scales linearly with `relScaling` × `(z3D_upperSurface -
    z3D_lowerSurface)`. Cone positioned at object's 3D position (with
    curve-aware offset). Material: 0.6 transparency, 0.1 shininess.
- **`prepareObserver(add)` (1222B)** — `add=true` registers
  `addObserver("PowerInput", absPathOfMethod)` for every row in
  `EnergyConsumers`; `add=false` calls `removeAllPowerInputObserver(root)`.
- **`updateConsumption` (1501B)** — `-> string` return type. For each
  active object: copy 6 statEnergy*Consumption values into
  `UsageProfile.UtilizationTable` cols 1..6 + write row in
  EnergyConsumers cols 4..9. Then roll up 3 custom attrs + update
  `refEnergy.value` + track `maxPowerConsumption`.
- **`isNameUniqueEverywhere` (342B)** — recursive walk: if
  `frame.isNameUnique(name) == false` → false; for each child, recurse
  into Networks (skipping non-Network nodes).

### Architectural observations

1. **BottleneckAnalyzer = "8-state utilization visualization"**
   - 8 stat*Portion attributes × 2D bar layer (`layer_of_chart`) +
     3D `createStatistics` overlay
   - Resource-type filtering (Production/Transport/Storage checkboxes)
   - 5 sort modes via hidden column 10
   - Fluid special-case (no statStoppedPortion)
2. **EnergyAnalyzer = "observer + visualization"**
   - Observer pattern: `addObserver("PowerInput", absPathOfMethod)`
     per energy-active object
   - 2D ellipse + 6 state bars + 3D cone frustum
   - Curve-aware positioning (track segments vs bounding box)
   - Recursive name uniqueness via `isNameUniqueEverywhere`
3. **BottleneckAnalyzer is heavier on analysis logic** (5119B
   `analyzeObject` vs 1747B `observeEnergyState`); EnergyAnalyzer is
   heavier on visualization (4296B `VisObject` vs 1411B `draw_Scale`).
4. **Both analyzers share `is3Dopen` + `obj._3D` pattern** for 3D
   rendering — same conditional overlay idiom.
5. **`Colors` DataTable** (in EnergyAnalyzer) holds RGB per energy state
   — 6 colors × RGB triplets; **`colors` Variable** (in BottleneckAnalyzer)
   holds RGB per utilization type — same pattern, different structure
   (Variable vs DataTable).
6. **DRIFT RISK #2**: `Models.Assembly1.PalletOptimization` ≡
   `Models.Assembly2.BufferOptimization` (proven earlier). Now adding:
   `Models.Assembly2.BottleneckAnalyzer` and `EnergyAnalyzer` are
   unique to Assembly2 — no parallel in Assembly1 (Assembly1 is the
   "lean baseline" without analyzers, by design). So no drift within
   Assembly2.

### Renderer bug discovered (recap, applies again)

`scripts/render_library.py` line 32–35 STILL drops multi-line programs.
Same `RENDER-1` bug. This time ALSO `parse_analyzer_tsv.py` got
contaminated when probe_methods.py wrote empty rows for the 8
readlog-degraded methods — my parser appended them to the prior method
(`reset`). Need to add a safeguard: stop accumulating body lines if a
line matches the path-header pattern.

### Cross-references

- Session summary: `03-agent-memory/plant-simulation-expert-memory/2026-08-27_session-summary_learn-new-assembly-model.md`
- Per-skill log: `skills/local-simtalk-read-library/log/2026-08-27_learn-assembly-model-palletOptimization-workerChart.md` (earlier session)
- Merged library dump: `/tmp/analyzer_all_25.json` (25 methods)
- Raw probe batch 1: `/tmp/analyzer_methods_raw.tsv` (17 valid + 8 empty rows)
- Raw probe batch 2: `/tmp/analyzer_missing_raw.tsv` (8 empty — all)
- Re-probe from readlog: `/tmp/analyzer_reprobe.json` (8 fixed)
- Re-probe capture script: `/tmp/probe_with_log_capture.py`
