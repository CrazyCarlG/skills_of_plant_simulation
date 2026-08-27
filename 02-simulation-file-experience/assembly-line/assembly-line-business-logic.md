# Assembly-line Model — Business Logic Patterns

> Deep dive on the **assembly-line** model currently loaded in
> Plant Simulation. Focus: model architecture, the `UserObjects/`
> library split, `WorkerChart` Frame-with-UI, `PalletOptimization`
> rule engine, A/B baseline-vs-instrumented design.
>
> All findings are from live `simtalk_run` + `readlog` probes against
> `host.docker.internal:50007`. See the source session log:
> `skills/local-simtalk-read-library/log/2026-08-27_learn-assembly-model-palletOptimization-workerChart.md`

---

## 1. Model architecture

```
Basis
├── MaterialFlow / Resources / InformationFlow / UserInterface / MUs / Tools
├── UserObjects                              ← modular object-library pattern
│   ├── Classes                              ← reusable class definitions
│   │   ├── Toolbar Library
│   │   ├── Track CrossTransfer
│   │   ├── Station MS / Station AS
│   │   ├── Worker ×3 (Worker / Worker_Round / Adjuster)
│   │   └── PickAndPlace Robot
│   └── Modules                              ← instance templates (Frames)
│       ├── PreProduction (full assembly of
│       │   MS/AS/Worker/Robot/Source)
│       └── Assembly_initialState
├── Models
│   ├── Assembly1                            ← lean baseline, 113 children
│   │   ├── PreProduction
│   │   ├── WorkerChart (5-method custom UI)
│   │   ├── PalletOptimization               ← custom ExperimentManager
│   │   └── …(Connectors/Conveyors/Buffer/
│   │         Source/Drain/Sankey/Events)
│   └── Assembly2                            ← instrumented production
│       └── Assembly1 (113) +
│       BottleneckAnalyzer (13 methods) +
│       EnergyAnalyzer (17 methods) +
│       BufferOptimization +
│       EnergySavingMeasures +
│       DisplayEnergy
└── SimtalkClaude (v2 TCP bridge — 4 sub-Folders:
    main[Frame]+src[Folder]+connection[Folder]+Objects[Folder];
    Objects holds 8 leaf class-instances:
    Method/Socket/DataList/Dialog/HtmlReport/Variable/Button/DataTable)
```

**Key observation**: this is **not** the Siemens Factory51 model.
Factory51 is a static library + a single `Models.Factory51` instance;
the assembly-line model uses a **two-level split** (`Classes` for
reusable definitions + `Modules` for instance templates) and ships
**two** parallel production-line instances (Assembly1 + Assembly2).

---

## 2. The `UserObjects/` library pattern (two-level split)

`UserObjects` is the project's contribution to its own class library.
The split is **deliberate**:

| Folder | Holds | Modification frequency |
|---|---|---|
| `UserObjects/Classes/*` | Reusable class definitions (Toolbar, Stations, Workers, Robot) | rarely |
| `UserObjects/Modules/PreProduction` | Frame template — assembles MS/AS/Worker/Robot/Source | occasionally |
| `UserObjects/Modules/Assembly_initialState` | "Reset-to-here" template, used by `BufferOptimization.restoreParam` | rarely |

Each line instance (`.Models.Assembly1`, `.Models.Assembly2`)
**embeds its own `PreProduction` Frame instance**. This means
modifying the template requires touching both Assembly1 and
Assembly2 — which is exactly where `PalletOptimization` /
`BufferOptimization` drift risk lives (see §5).

**Compared to Factory51's pattern**:

| Pattern | Factory51 | Assembly-line |
|---|---|---|
| Class library | `ApplicationObjects/` + `UserObjects/` (flat) | `UserObjects/Classes/` |
| Module templates | none | `UserObjects/Modules/PreProduction` |
| Production line | single `Models.Factory51` (142 children) | dual `Models.Assembly1` + `Models.Assembly2` (113 children each) |
| SimtalkClaude integration | `.SimtalkClaude2/` | `.SimtalkClaude/` |

> **Worth copying**: the `Classes` vs `Modules` separation in
> `UserObjects/`. It makes it obvious which objects are definitions
> (don't instance) vs which are templates (instance + customize).

---

## 3. `WorkerChart` — Frame-with-UI pattern

`WorkerChart` is a textbook example of a **Frame that owns a Dialog +
DataTables + chart input**. The frame is dragged onto a Frame from
the class library; `DragAndDrop` validates the dropped object type
via `internalClassName`, then opens the dialog.

### 3.1 Method inventory (5 methods on `.Models.Assembly1.WorkerChart`)

| Method | Size | Role |
|---|---|---|
| `init` | 145B | `GetWorkersFromPool` + `switchRadioButton` + `Refresh` |
| `DragAndDrop` | 893B | Accepts `NwWorkerPool` only; populates table; opens dialog |
| `Open` | 1289B | **SimTalk 2.0 syntax** (`is`/`do`/`inspect`/`when`/`end;`/`then`); restores persisted dialog state |
| `CallBack` | 3708B | UI event router — `switch item / case`; copies `myWorkingTimeStatisticTable` / `myOverallTimeStatisticTable` into `myStatisticTable` for "Working time" vs "Overall time" occupancy views |
| `Refresh` | 3152B | Renders via `Transpose(myStatisticTable, myBufferTable)` then builds `Chart.InputChannels` per VarStatisticGroup (Worker / Group / Pool) using `MakeString(...)` per row + `(s)/numWorkers` division for non-Pie charts |

### 3.2 The Frame-with-UI pattern (worth copying)

```
.WorkerChart                              ← Frame object
├── Dialog (custom UI)                   ← drag-target, event source
├── myWorkingTimeStatisticTable           ← DataTable (source 1)
├── myOverallTimeStatisticTable           ← DataTable (source 2)
├── myStatisticTable                      ← DataTable (combined view)
├── myBufferTable                         ← DataTable (transposed for input)
├── myRadioButton                         ← Variable (Working/Overall toggle)
└── Chart (built-in Plant Simulation chart object)
```

The lifecycle is **init → drag → open → callback → refresh**:

1. **Init** — auto-runs once at model open, sets default radio + calls Refresh.
2. **DragAndDrop** — user drops a `NwWorkerPool` onto the Frame.
   The type check (`internalClassName = "NwWorkerPool"`) is the
   contract.
3. **Open** — user opens the dialog from the Frame's context menu.
   Persists last-used radio button state across sessions.
4. **CallBack** — UI events land here. Two main views are toggled
   by switching the active DataTable source. The `switch item / case`
   is the event dispatcher.
5. **Refresh** — rebuilds `Chart.InputChannels` from scratch every
   time. Uses `Transpose()` to flip row/column orientation, then
   `MakeString(...)` per row to build the chart's channel spec.

### 3.3 SimTalk 2.0 vs 1.0 — selectively mixed

`Open` is the only method that uses SimTalk 2.0 syntax
(`is` / `do` / `inspect` / `when` / `end;` + `then` clauses).
All other methods use SimTalk 1.0 (`if ... end` + `case`).

**Interpretation**: `Open` was rewritten later (likely to add the
persisted-dialog-state feature). The author kept the rest in 1.0
because SimTalk 2.0 syntax does not provide benefits when the
control flow is simple.

> **Lesson**: SimTalk 2.0 is a **per-method** choice, not a
> project-wide switch. Mixed-syntax projects are normal.

---

## 4. `PalletOptimization` — custom ExperimentManager

`PalletOptimization` is a **richer re-implementation of
`.Tools.ExperimentManager`**. It is the project-specific experiment
runner — defined locally rather than reused because it adds a
rule-engine for experiment-time adaptations.

### 4.1 Method inventory (11 methods on `.Models.Assembly1.Start` spine)

| Method | Size | Role |
|---|---|---|
| `Start` | 9673B | 4-state machine (`stopped`/`wait4stop`/`running`/`ready`); distributed vs non-distributed branches; full validation pre-flight |
| `evalRules` | 2899B | Rule engine — priority-sorted rules (descending); init-rules fire only on experiment 1 |
| `performRule` | 971B | Composite condition = `Rules.TestConditionExp` + condition method; composite action = `Rules.DoActionExp` + optional method action |
| `reset` | — | First reset triggers `DefExperiments` chain → `evalRules` → `performRule`; subsequent resets call `eventController.start` |
| `setParameter` | — | `writeValue(AttrStr, AttrVal)` per input column, then `DefSeed4Run` |
| `makeJobTable` | — | Creates per-run job entries + `ProgressTable` visualization, `ProgressTable.refillDialog` to refresh |
| `storeParam` | — | Baseline snapshot with type-aware dispatch (`str_to_time`/`str_to_length`/`str_to_speed`/`str_to_acceleration`/`str_to_weight`) |
| `restoreParam` | — | Restore from baseline, including WorkerPool `creationTable` inheritance via `setCreationTable(void)` / `inheritAttribute` |
| `DefExperiments` | — | Re-derives experiment list when rules change |
| `DefSeed4Run` | — | Reproducibility hook |
| `Rules.*` | — | Rule-condition + rule-action helper sub-Frame |

### 4.2 The 4-state machine in `Start`

```simtalk
-- Pseudo-shape of Start's state machine:
switch currentState
case "stopped"
  -- validation pre-flight:
  --   computer accessible, Remote machines table populated,
  --   EventController + End time set, ValueDescriptions registered,
  --   Output/Input defined
  -- then → "wait4stop"
case "wait4stop"
  -- distributed mode: wait for remote workers
  -- non-distributed: run immediately → "running"
case "running"
  -- increment experiment counter, evalRules, performRule
  -- → "ready" when done
case "ready"
  -- eventController.start, repeat
end
```

The state machine exists because Plant Simulation's built-in
`EventController.start` is fire-and-forget; this state machine
adds **synchronous readiness semantics** so the agent can probe
"is experiment N done yet?" via `currentState`.

### 4.3 The rule engine (`evalRules` + `performRule`)

Rules are stored in a DataTable with columns:
`priority:int, initRule:boolean, conditionMethod:string,
conditionExp:string, actionMethod:string, actionExp:string,
validExp:string`.

`evalRules`:
1. Sort rules by priority (descending).
2. For each rule, check `initRule` — if true, fire only on experiment 1.
3. Else, call `Rules.validExp(s)` for the current experiment.
4. If valid, call `performRule(rule)`.

`performRule(rule)`:
- **Composite condition** = `Rules.TestConditionExp(rule, conditionExp)` AND a method call (`rule.conditionMethod`).
- **Composite action** = `Rules.DoActionExp(rule, actionExp)` AND optionally a method call (`rule.actionMethod`).

This pattern is a **mini-DSL**: rules are stored as data, condition
+ action are split between a SimTalk expression and a method name.
The expression handles arithmetic / comparison; the method handles
complex logic.

> **Worth copying**: the priority-sorted rule table + composite
> condition/action. It's how you give end-users a way to add
> experiment logic without recompiling.

### 4.4 `storeParam` / `restoreParam` — type-aware snapshot

These are the **parameter baseline** for an experiment run.
`storeParam` captures every input parameter; `restoreParam` resets
to baseline before the next run.

The type-aware dispatch is notable — Plant Simulation's
`writeValue` does **not** auto-convert strings to typed values, so
the code explicitly maps:

```
"length"  → str_to_length
"time"    → str_to_time
"speed"   → str_to_speed
"acceleration" → str_to_acceleration
"weight"  → str_to_weight
```

WorkerPool inheritance is special — uses
`setCreationTable(void)` + `inheritAttribute` rather than
`writeValue`, because WorkerPool members are dynamic.

> **Lesson**: Plant Simulation's `writeValue` is **untyped**. Always
> use the type-specific `str_to_*` converter on restore.

---

## 5. A/B baseline-vs-instrumented design — drift risk

Assembly1 and Assembly2 are **two parallel instances of the same
assembly line**. They share topology but not analyzers:

| Aspect | Assembly1 | Assembly2 |
|---|---|---|
| Children | 113 | 113 + analyzers |
| `PreProduction` | embedded | embedded (same instance? — unverified) |
| `PalletOptimization` | ✅ | ❌ |
| `BufferOptimization` | ❌ | ✅ |
| `BottleneckAnalyzer` | ❌ | ✅ (13 methods) |
| `EnergyAnalyzer` | ❌ | ✅ (17 methods, 12 methods in source) |
| `EnergySavingMeasures` | ❌ | ✅ (Checkbox) |
| `DisplayEnergy` | ❌ | ✅ |

### 5.1 Drift risk: `PalletOptimization` ≡ `BufferOptimization`

A failed BFS run emitted **identical method lists** for both
Frames up to char 11971 (truncated by readlog v15+ buffer ceiling).
This is strong evidence that `BufferOptimization` was created by
**duplicate-and-rename** of `PalletOptimization`.

**Risk**: if either side is edited independently, the two will
silently diverge. There is no `inheritsFrom` or template link.

**Mitigation options** (not yet applied):
1. Convert one to inherit from the other (Plant Simulation supports
   Frame inheritance via the class system).
2. Make `BufferOptimization` a Frame with shared base methods via
   a parent class.
3. At minimum, add a self-check method that asserts the two are
   byte-identical after any edit.

> **Lesson**: when duplicating a Frame to specialize it, **prefer
> inheritance** over copy. The duplication pattern is a known
> drift source.

### 5.2 Drift risk: `PreProduction` is embedded, not inherited

Each Assembly instance embeds its own `PreProduction` instance.
Editing the template (`UserObjects.Modules.PreProduction`) does
**not** propagate to either Assembly.

> **Lesson**: for production-line templates, prefer Frame
> inheritance over embedding. Plant Simulation supports it.

---

## 6. Other observations

### 6.1 `NwWorkerPool` — the worker-pool class

The class name `NwWorkerPool` (the "Nw" prefix matches Plant
Simulation's internal naming convention for class library
classes) is the runtime type of worker-pool objects. The
`DragAndDrop` method of `WorkerChart` guards on
`internalClassName = "NwWorkerPool"` to ensure only worker pools
can be dropped onto the chart.

### 6.2 SimtalkClaude v2 bridge — identical to Factory51

The `.SimtalkClaude` Folder structure is the **same v2 bridge** as
Factory51: `auth/sig/token/session_id` Variables are present;
whether `sig` is actually computed still unverified (would need
`local-simtalk-read-library` on
`.SimtalkClaude.main.SocketClient.m_sendauth` to confirm).

### 6.3 Sankey + HtmlReport + DisplayEnergy — reporting stack

The line has multiple visualization layers:
- **Sankey** diagrams — material flow between stations
- **HtmlReport** — text-based summary
- **DisplayEnergy** (Assembly2 only) — energy overlay
- **EnergyAnalyzer.visualize** (Assembly2 only) — 2D ellipses + 3D
  cones per energy-active object

This is a **multi-view reporting stack** where each visualization
uses a different rendering primitive (DataTable-driven chart,
DataTable-driven HTML, custom 2D layer, custom 3D group).

---

## 7. Cross-references

- `analyzers-pattern.md` — BottleneckAnalyzer + EnergyAnalyzer deep dive
- `probe-pipeline-quirks.md` — pipeline bugs hit while probing this model
- `facory51/README.md` — Factory51 + SimtalkClaude v2 (orthogonal model)
- `simtalkclaude-best-practices.md` — SimtalkClaude v1 base experience

## 8. Reproduce this analysis

```bash
# 1) Pre-flight: confirm bridge reachable
python3 skills/local-simtalk-execution/scripts/simtalk_send.py ping

# 2) Identify model
python3 skills/local-simtalk-get-folder-tree/scripts/bfs_full.py --no-infobox . 2 \
  /tmp/root_d2.json

# 3) Drill into Assembly1 + Assembly2
python3 skills/local-simtalk-get-folder-tree/scripts/bfs_full.py --no-infobox .Models 2 \
  skills/local-simtalk-get-folder-tree/data/models_d2.json

# 4) Drill into UserObjects
python3 skills/local-simtalk-get-folder-tree/scripts/bfs_full.py --no-infobox .UserObjects 2 \
  skills/local-simtalk-get-folder-tree/data/userobjects_d2.json

# 5) Probe specific methods (one-at-a-time to avoid readlog degradation)
python3 skills/local-simtalk-execution/scripts/simtalk_send.py run \
  '.Models.Assembly1.WorkerChart.~.init'  # etc.
```

> **Critical**: probe **one method at a time** with `sleep(1.2)`
> between calls. Batch probing of 8+ methods triggers readlog v15+
> degradation (the cumulative log buffer caps at 65536 bytes; later
> methods return blank metadata). See `probe-pipeline-quirks.md`.