# Exploration Log — Class Inheritance Map

Captured 2026-08-26 against the Plant Simulation server at
`host.docker.internal:50007` (build 2606.0002, the production model loaded
in the dispatch Frame `.SimtalkClaude.main`).

## Method

1. **Candidate generation** — took the 327-node depth-4 folder tree from
   `local-simtalk-get-folder-tree/data/basis_tree_depth4.json` and filtered
   out non-class structural types (`Folder`, `Frame`, `Method`, `Variable`,
   `DataTable`, `Socket`, `Button`, `Dialog`, `Chart`, `HtmlReport`,
   `DataList`, `Comment`, `FileLink`). The remaining **65 nodes** are
   candidate Plant Simulation classes.

2. **Probe** — for each of the 65 candidate paths, sent SimTalk to the
   server that:
   - resolves the path with `str_to_obj(p)`;
   - reads `o.Name`, `o.InternalClassType`, `o.Origin`, `o.OriginRoot`,
     `o.Class`;
   - prints one line per path with a unique batch marker `###INH_BATCH###`
     as delimiter.
   Probing was done in batches of 12 paths to stay under the v15+ readlog
   buffer cap (see `protocol-notes.md`).

3. **Render** — partitioned the 65 rows into:
   - **Root classes** (Origin=VOID, 61 of them) — Plant Simulation built-ins
   - **Derived classes** (Origin≠VOID, 4 of them) — user-defined subclasses
   …and emitted a parent → children map.

4. **Independent verification** — re-probed 6 critical classes (all 4
   derived classes + 2 representative roots) via a fresh `simtalk_run` +
   `readlog` round-trip. All 6 results matched the JSON claims.

## Inheritance map (65 classes, 4 derived)

### Derived classes (user-defined, Origin ≠ VOID)

| # | Path | InternalClassType | Origin | OriginRoot | Class |
|---|---|---|---|---|---|
| 1 | `.Models.Model.EventController` | EventController | `.MaterialFlow.EventController` | `.MaterialFlow.EventController` | `.MaterialFlow.EventController` |
| 2 | `.UserObjects.MyFrame.Connector` | Connector | `.MaterialFlow.Connector` | `.MaterialFlow.Connector` | `.MaterialFlow.Connector` |
| 3 | `.UserObjects.MyFrame.Conveyor` | Conveyor | `.MaterialFlow.Conveyor` | `.MaterialFlow.Conveyor` | `.MaterialFlow.Conveyor` |
| 4 | `.UserObjects.MyFrame.Station` | Station | `.MaterialFlow.Station` | `.MaterialFlow.Station` | `.MaterialFlow.Station` |

All four are **single-level derivations** — `Origin == OriginRoot == Class`,
pointing into the standard MaterialFlow class library.

### Root classes by parent (61 total, all Origin=VOID)

#### `.MaterialFlow.*` (22 roots)

| Path | Type |
|---|---|
| `.MaterialFlow.Connector` | Connector |
| `.MaterialFlow.EventController` | EventController |
| `.MaterialFlow.Interface` | Interface |
| `.MaterialFlow.Source` | Source |
| `.MaterialFlow.Drain` | Drain |
| `.MaterialFlow.Station` | Station |
| `.MaterialFlow.ParallelStation` | ParallelStation |
| `.MaterialFlow.AssemblyStation` | AssemblyStation |
| `.MaterialFlow.DismantleStation` | DismantleStation |
| `.MaterialFlow.PickAndPlace` | PickAndPlace |
| `.MaterialFlow.Store` | Store |
| `.MaterialFlow.Buffer` | Buffer |
| `.MaterialFlow.Sorter` | Sorter |
| `.MaterialFlow.Conveyor` | Conveyor |
| `.MaterialFlow.AngularConverter` | AngularConverter |
| `.MaterialFlow.Converter` | Converter |
| `.MaterialFlow.Turntable` | Turntable |
| `.MaterialFlow.Turnplate` | Turnplate |
| `.MaterialFlow.Track` | Track |
| `.MaterialFlow.TwoLaneTrack` | TwoLaneTrack |
| `.MaterialFlow.FlowControl` | FlowControl |
| `.MaterialFlow.Cycle` | Cycle |

Derived from these: `.Models.Model.EventController`,
`.UserObjects.MyFrame.Connector`, `.UserObjects.MyFrame.Conveyor`,
`.UserObjects.MyFrame.Station`.

#### `.Fluids.*` (9 roots)

| Path | Type |
|---|---|
| `.Fluids.Pipe` | Pipe |
| `.Fluids.FluidSource` | FluidSource |
| `.Fluids.FluidDrain` | FluidDrain |
| `.Fluids.Tank` | Tank |
| `.Fluids.Mixer` | Mixer |
| `.Fluids.ContinuousMixer` | ContinuousMixer |
| `.Fluids.Portioner` | Portioner |
| `.Fluids.DePortioner` | DePortioner |
| `.Fluids.PatchMatrix` | PatchMatrix |

#### `.Resources.*` (10 roots)

| Path | Type |
|---|---|
| `.Resources.Workplace` | Workplace |
| `.Resources.FootPath` | FootPath |
| `.Resources.WorkerPool` | WorkerPool |
| `.Resources.Worker` | Worker |
| `.Resources.Exporter` | Exporter |
| `.Resources.Broker` | Broker |
| `.Resources.AGVPool` | AGVPool |
| `.Resources.Marker` | Marker |
| `.Resources.ShiftCalendar` | ShiftCalendar |
| `.Resources.LockoutZone` | LockoutZone |

#### `.InformationFlow.*` (7 roots)

| Path | Type |
|---|---|
| `.InformationFlow.DataStack` | DataStack |
| `.InformationFlow.DataQueue` | DataQueue |
| `.InformationFlow.TimeSequence` | TimeSequence |
| `.InformationFlow.Trigger` | Trigger |
| `.InformationFlow.Generator` | Generator |
| `.InformationFlow.AttributeExplorer` | AttributeExplorer |
| `.InformationFlow.FileInterface` | FileInterface |
| `.InformationFlow.MQTT` | MQTTInterface (note: InternalClassType is `MQTTInterface` but Name is `MQTT`) |

> Note: `.Tools.ExperimentManager.BasicObjects.InformationFlow.FileInterface`
> is also captured as a root — same Name/Type/Origin triple, just a deeper
> path.

#### `.UserInterface.*` (5 roots)

| Path | Type |
|---|---|
| `.UserInterface.Display` | Display |
| `.UserInterface.SankeyDiagram` | SankeyDiagram |
| `.UserInterface.CostAnalyzer` | CostAnalyzer |
| `.UserInterface.Checkbox` | Checkbox |
| `.UserInterface.DropDownList` | DropDownList |

#### `.MUs.*` (3 roots)

| Path | Type |
|---|---|
| `.MUs.Part` | Part |
| `.MUs.Container` | Container |
| `.MUs.Transporter` | Transporter |

#### `.UserObjects.*` (5 roots — **plus 3 derived, listed above**)

| Path | Type |
|---|---|
| `.UserObjects.PartA` | Part |
| `.UserObjects.PartB` | Part |
| `.UserObjects.Box` | Container |

> All three have Origin=VOID, so despite being in `.UserObjects` they
> are root classes (Plant Simulation built-in `Part` / `Container`
> instances placed under a user folder, not subclasses of them).

## Parent → Children Map (rendered)

```
.MaterialFlow.Station            (1 child)
  └─ .UserObjects.MyFrame.Station            [Station]

.MaterialFlow.Conveyor           (1 child)
  └─ .UserObjects.MyFrame.Conveyor           [Conveyor]

.MaterialFlow.Connector          (1 child)
  └─ .UserObjects.MyFrame.Connector          [Connector]

.MaterialFlow.EventController    (1 child)
  └─ .Models.Model.EventController           [EventController]
```

Every other class in the 65-class sample has Origin=VOID (no children).

## Headline insights

1. **The model defines only 4 user classes** — all are **single-level
   subclasses** of standard MaterialFlow classes. No deep chains exist in
   this loaded model.

2. **`.UserObjects.PartA` / `.PartB` / `.Box` are NOT user-defined
   subclasses** — they're root Plant Simulation instances placed inside a
   user folder, with `InternalClassType` matching the built-in (`Part`,
   `Container`). The name is misleading.

3. **`.InformationFlow.MQTT` has Name=`MQTT` but `InternalClassType=`
   `MQTTInterface`** — Plant Simulation renames classes on instantiation;
   always trust `InternalClassType` for type identity, not `Name`.

4. **`.Models.Model.EventController` is a derived class**, but it's the
   only child of `.MaterialFlow.EventController` in this model.

## Re-running the exploration

```bash
# 1. Generate candidate paths from the folder tree
python3 - <<'PY'
import json
tree = json.load(open(
    "../local-simtalk-get-folder-tree/data/basis_tree_depth4.json"))
SKIP = {"Folder","Frame","Method","Variable","DataTable","Socket",
        "Button","Dialog","Chart","HtmlReport","DataList","Comment",
        "FileLink"}
classes = set()
def walk(n):
    if n["type"] not in SKIP: classes.add(n["path"])
    for c in n.get("children", []): walk(c)
walk(tree)
open("paths.txt","w").write("\n".join(sorted(classes)) + "\n")
PY

# 2. Probe inheritance (batched, with marker-based extraction)
python3 scripts/probe_inheritance.py paths.txt data/inheritance_raw.tsv

# 3. Render the parent -> children map
python3 scripts/render_inheritance_map.py data/inheritance_raw.tsv
```

## Quirks observed during this exploration

See `protocol-notes.md` for the full v15+ `readlog` workaround details.
Summary of skill-specific quirks:

1. **`Origin == OriginRoot == Class`** for the 4 user-defined classes in
   this model — all are single-level derivations. No multi-level chains.
2. **`InternalClassType` may differ from the displayed `Name`** — trust
   `InternalClassType` for type identity. Examples:
   `.InformationFlow.MQTT` → Name=`MQTT`, Type=`MQTTInterface`.
3. **`UserObjects` ≠ derived** — being under a `.UserObjects.*` folder
   doesn't mean the object is a user-defined subclass. `.UserObjects.PartA`
   has `InternalClassType=Part` (built-in) and `Origin=VOID` (root).
4. **`readlog` v15+ requires batched marker-based extraction** — see
   `protocol-notes.md` §1.
5. **Embedded `+` and `\\"` in shell heredoc corrupt SimTalk code** — see
   `protocol-notes.md` §2.
6. **`array` ≠ `list` in SimTalk** — see `protocol-notes.md` §3.