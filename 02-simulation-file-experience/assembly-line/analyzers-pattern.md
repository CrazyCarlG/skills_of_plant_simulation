# Analyzers — BottleneckAnalyzer + EnergyAnalyzer Patterns

> Detailed patterns from `.Models.Assembly2.BottleneckAnalyzer.*`
> (13 methods) + `.Models.Assembly2.EnergyAnalyzer.*` (12 methods
> in source — the "17" count in session notes likely includes
> DataTables/Chart/Dialog/HtmlReport children).
>
> Source: live `simtalk_run` + `readlog` probes. Per-method source
> is in `skills/local-simtalk-read-library/data/` plus the session
> log `skills/local-simtalk-read-library/log/2026-08-27_learn-assembly-model-bottleneckAnalyzer-energyAnalyzer.md`.

---

## 1. `BottleneckAnalyzer` — 8-state utilization breakdown + visual bars

8 stat attributes → 8 utilization factors per object → bar layer +
3D-statistics overlay.

### 1.1 Method inventory (13 methods)

| Method | Size | Role |
|---|---|---|
| `analyzeFrame` | 3478B | Recursive Frame walk. Switch on `obj.internalClassName`: recurse into `Network`, skip `Method`/`NwWorkplace`/`NwWorkerPool`/`NwData`/`NwExporter`; for leaves with `StatWorkingPortion` call `analyzeObject`. Aggregates 8 factors + draws via `drawBar`. |
| `analyzeObject` | 5119B | Extracts 8 `stat*Portion` attrs; multi-branch on `isFluid` (`NwTank`/`NwFluidSource`/`NwFluidDrain`/`NwMixer`/`NwPipe` — no `statStoppedPortion`); guarded by `obj.resStatOn` + 3 resource-type checkboxes (Production/Transport/Storage); writes row to `resourceStats` DataTable (path + 8 percentages × 100); for pipes, blocking/fail/powering/pause forced to 0. |
| `analyzeModel` | 455B | Dialog entry — `removeStats` → `analyzeFrame(~)` → `Analyzed := true`. |
| `removeStats` / `removeCharts` | — | Cleanup; `removeCharts` recursive via `eraselayer(layer_of_chart)` + `_3D.deleteStatistics`. |
| `sortStats(criteria)` | 1464B | 5 modes: by working / setup / working+fail / working+fail+pause / working+setup+fail+pause. Uses hidden col 10 + `resStats.sort(colSort,"down")`. |
| `draw_Scale` / `drawBar` / `insRootStr` | — | 2D layer primitives. `drawBar` reads color from `colors[1,typeStr]` (Variable map: work/setup/wait/block/PoweringUpDown/fail/stop/pause). |
| `fill4Report` | 744B | `analyzeModel` + localized header + `sortStats(3)`. External-callable. |
| `markBottleneckObject` | 1056B | Finds max working/waiting/blocked/disrupted, draws 4 colored ellipses on top. |
| `isTool` | 159B | Guards Tools (Experiment/GAwizard/self). |
| `reset` | 12B | `removeStats`. |

### 1.2 The 8-state utilization model

Plant Simulation exposes these stats per object:

```
statWorkingPortion      -- actively producing
statSetupPortion        -- in setup (changeover)
statWaitingPortion      -- idle, waiting for input
statBlockedPortion      -- blocked by downstream
statPoweringUpDownPortion  -- powering up or down
statFailedPortion       -- in failed state
statStoppedPortion      -- explicitly stopped (not fluid objects)
statPausedPortion       -- paused (not fluid objects)
```

The 8 × 100% breakdown is the universal Plant Simulation "where
did the time go" lens. `BottleneckAnalyzer` reads all 8 and
visualizes per-object.

### 1.3 The fluid special-case

`isFluid` triggers a branch where `statStoppedPortion` and
`statPausedPortion` are **not present** (continuous-flow objects
can't be "paused" or "stopped" the same way). The code forces
`blocking/fail/powering/pause = 0` for pipes (they can't be
"blocked" in the discrete sense).

This is a general lesson: **Plant Simulation's stat model is
different for fluid vs discrete objects**. Always check
`internalClassName` before reading `stat*Portion` attrs.

### 1.4 The 5-mode sort

`sortStats(criteria)` accepts one of 5 integer codes:

| Code | Sort key |
|---|---|
| 1 | working (descending) |
| 2 | setup |
| 3 | working + fail |
| 4 | working + fail + pause |
| 5 | working + setup + fail + pause |

The implementation uses a **hidden col 10** in the DataTable to
pre-compute the sort key per row, then calls
`resStats.sort(colSort, "down")`. Hidden columns are a common
Plant Simulation idiom for "computed sort keys without polluting
the visible schema".

### 1.5 The color map pattern

`colors` is a **Variable** (not a DataTable) mapping type strings
to RGB values:

```
colors[1, "Working"]        := makeRGBValue(...)
colors[1, "Setup"]          := ...
colors[1, "Waiting"]        := ...
colors[1, "Blocked"]        := ...
colors[1, "PoweringUpDown"] := ...
colors[1, "Failed"]         := ...
colors[1, "Stopped"]        := ...
colors[1, "Paused"]         := ...
```

`drawBar` reads `colors[1, typeStr]` to color each utilization
bar. The Variable-vs-DataTable choice matters — Variables are
faster for small fixed maps; DataTables for editable lists.

> **Lesson**: for **fixed enum-to-RGB maps**, prefer `Variable`
> (faster). For **user-editable maps**, use `DataTable`.

---

## 2. `EnergyAnalyzer` — energy-consumption observer pattern

Find energy-active objects → register observer on `PowerInput` → on
change, update DataTable + roll up custom attrs → visualize via 2D
ellipses + 3D cones.

### 2.1 Method inventory (12 methods)

| Method | Size | Role |
|---|---|---|
| `init` | 123B | `prepareObserver(true)` if `MonitoringActive` + `updateConsumption`. |
| `findConsumers(frame)` | 392B | Recursive walk; for each non-Network child, `detectEnergyobjects(o)` → append path to `Objects` DataTable. |
| `reset` | 763B | `delVisualize` → `prepareObserver(false)` → clear tables + zero `Consumption`/`ConsumptionOperational`/`powerConsumption`/`maxPowerConsumption`/`PeakTime` → restore `numPlottedValues=10000`. |
| `observeEnergyState` | 1747B | **The observer** (param `valueName:string, oldValue:any`). Guards: `!EnergyActive` / `rootframe /= root` / row not found in `EnergyConsumers` (one-time error `messageBox(56)` + `eventController.stop`). Action: write row `statEnergyTotalConsumption` + operational portion + `PowerInput`, roll up 3 custom attrs via `EnergyConsumers.sum`, update `refEnergy.value`, track `maxPowerConsumption` + `PeakTime`, refresh dialog if `EnergyConsumers.isOpen` OR `UsageProfile.active`. |
| `detectEnergyobjects(o)` | 96B | `return o.EnergyActive` with error handler. |
| `visualize` | 621B | "Show" button. Builds unique `GrGroupName` (`_name_layer_` looped until `isNameUniqueEverywhere`); errors out if `MaxCons == 0`; for each row calls `visObject(objNo, relScaling)`. |
| `delVisualize` | 819B | "Remove" button. Clears 2D layer + deletes `_3D.getObject(GrGroupName)`. |
| `endSim` | 18B | `updateConsumption` (refresh report). |
| `VisObject(objNo, relScaling)` | 4296B | **Visualization core**. Color: `makeRGBValue(cr, 0, 255-cr)`. 4 bands by relScaling (1/3/5/7 px wide). 2D positioning: if curve, use `getCurveSegments` + axes math (origin/scaling/tangent/radius vector → pixel) with right/left-turn handling; else bounding-box center. Draws ellipse + 6 state bars (Working/Setting_up/Operational/Failed/Standby/Off from `Colors.RGB`). 3D: `getGraphic("default").createConeFrustum` with height scaled by `relScaling × (z3D_upperSurface - z3D_lowerSurface)`, positioned at object's 3D coord (curve-aware offset). |
| `prepareObserver(add)` | 1222B | Registers `addObserver("PowerInput", absPathOfMethod)` per row, or `removeAllPowerInputObserver(root)` to clear. |
| `updateConsumption` | 1501B | `-> string`. For each active object: copy 6 `statEnergy*Consumption` to `UsageProfile.UtilizationTable` cols 1..6 + write EnergyConsumers cols 4..9; roll up custom attrs + update `refEnergy` + track `maxPowerConsumption`. |
| `isNameUniqueEverywhere(frame, name)` | 342B | Recursive: if `!frame.isNameUnique(name)` → false; recurse into Networks. |

### 2.2 The observer pattern

The signature pattern is:

```simtalk
-- prepareObserver(true):
for each row in EnergyConsumers
  o := str_to_obj(row.path)
  o.addObserver("PowerInput",
                absPathOfMethod(~.observeEnergyState))
end

-- observeEnergyState(valueName, oldValue):
-- runs whenever PowerInput changes on any registered object
-- signature MUST be (valueName: string, oldValue: any)
```

This is the Plant Simulation **observer** idiom. The observer
callback is invoked on every attribute write, so the callback must
be cheap and idempotent.

> **Critical**: the observer signature `(valueName, oldValue)` is
> mandatory. Plant Simulation dispatches observers with these two
> arguments — getting them wrong silently breaks the callback.

### 2.3 The 6-state energy color palette

`Colors` is a **DataTable** (not a Variable, unlike BottleneckAnalyzer):

```
Working       → RGB
Setting_up    → RGB
Operational   → RGB
Failed        → RGB
Standby       → RGB
Off           → RGB
```

The 6-state palette is **the same enum as WorkerChart's
"occupancy views"** (Working time vs Overall time vs the 6
operational states). This suggests a shared model:

```
operational state: {Working, Setting_up, Operational, Failed, Standby, Off}
utilization state: {Working, Setup, Waiting, Blocked, PoweringUpDown,
                    Failed, Stopped, Paused}
```

Both are 6-or-8-state breakdowns of "what was the object doing
during this time slice?". The two palettes may overlap but the
enum sets are not identical.

> **Open**: a shared `Colors`/`colors` definition could be
> extracted. Worth checking if `UserObjects.Classes` already has
> one.

### 2.4 Curve-aware 2D positioning

`VisObject` has two positioning branches:

1. **Curve objects** (Conveyors, Tracks) — use `getCurveSegments`
   to get the curve's geometry, then axes math to project
   arc-length position → pixel position. Right/left-turn handling
   is explicit.
2. **Non-curve objects** — use the bounding-box center.

The 3D placement is also curve-aware: `curve-aware offset` on
top of `(x, y, z3D_lowerSurface)` to place the cone at the
right point on the curve.

> **Lesson**: when visualizing per-object overlays, always handle
> curves differently from non-curves. The geometry primitives
> differ.

### 2.5 Recursive name uniqueness

`isNameUniqueEverywhere(frame, name)` is recursive: check
`frame.isNameUnique(name)`, then recurse into all child Networks.
This is needed because Plant Simulation names are **only unique
within their parent Frame**, not globally — so a 3D group name
needs recursive checking before being assigned.

```simtalk
-- isNameUniqueEverywhere
if not frame.isNameUnique(name)
  return false
end
for each child in frame
  if child is Network
    if not isNameUniqueEverywhere(child, name)
      return false
    end
  end
end
return true
```

> **Lesson**: 3D / 2D group names must be globally unique across
> all child Networks. Plant Simulation's `isNameUnique` only
> checks the immediate parent.

---

## 3. Architectural observations (analyzer-specific)

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
   `analyzeObject` vs 1747B `observeEnergyState`); EnergyAnalyzer
   is heavier on visualization (4296B `VisObject` vs 1411B
   `draw_Scale`).

4. **Both share `is3Dopen` + `obj._3D` conditional overlay idiom.**

5. **`Colors` DataTable** (EnergyAnalyzer) = RGB per energy state
   (6 colors × RGB); **`colors` Variable** (BottleneckAnalyzer) =
   RGB per utilization type (Variable vs DataTable — same pattern,
   different shape — see §1.5).

6. **DRIFT STATUS**: BottleneckAnalyzer + EnergyAnalyzer are
   UNIQUE to Assembly2 — no parallel in Assembly1 (by design —
   Assembly1 is the lean baseline). So no drift risk within
   Assembly2.

---

## 4. Cross-references

- `assembly-line-business-logic.md` — model architecture, library
  pattern, WorkerChart, PalletOptimization
- `probe-pipeline-quirks.md` — pipeline bugs hit while probing
  these methods
- `01-plantsimulation-knowledge/.../Method/attributes` —
  authoritative Method-object docs (used `&m.Program`,
  `&m.Encrypted`, `&m.HasSyntaxError`, `&m.NumInExecution`)

## 5. Reproduce this analysis

```bash
# Probe all 13 BottleneckAnalyzer methods
for m in analyzeFrame analyzeObject analyzeModel removeStats \
         removeCharts sortStats draw_Scale drawBar insRootStr \
         fill4Report markBottleneckObject isTool reset; do
  python3 skills/local-simtalk-execution/scripts/simtalk_send.py run \
    ".Models.Assembly2.BottleneckAnalyzer.~.$m"
  sleep 1.2  # critical — avoids readlog degradation
done

# Probe all 12 EnergyAnalyzer methods (same pattern)
for m in init findConsumers reset observeEnergyState \
         detectEnergyobjects visualize delVisualize endSim \
         VisObject prepareObserver updateConsumption \
         isNameUniqueEverywhere; do
  python3 skills/local-simtalk-execution/scripts/simtalk_send.py run \
    ".Models.Assembly2.EnergyAnalyzer.~.$m"
  sleep 1.2
done
```

> **Critical**: probe **one method at a time** with `sleep(1.2)`
> between calls. Batch probing of 8+ methods triggers readlog v15+
> degradation — see `probe-pipeline-quirks.md` §2.