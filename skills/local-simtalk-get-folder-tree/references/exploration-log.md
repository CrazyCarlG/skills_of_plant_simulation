# Exploration Log — Basis Folder Tree

Captured 2026-08-25 against the Plant Simulation server at
`host.docker.internal:50007` (build 2606.0002, the production model loaded in
the dispatch Frame `.SimtalkClaude.main`).

## Method

1. `scripts/bfs_one_level.py .` enumerated the **basis root** (anonymous
   identifier, display name `"Basis"`, `InternalClassType = "Folder"`,
   `obj_to_str` returns the empty string).
2. Each top-level entry was expanded recursively through `scripts/bfs_full.py`
   with `max_depth = 4`. Only `Folder` / `Frame` nodes are recursed — Method,
   Variable, DataTable, Socket, etc. are leaves.
3. The complete tree is saved at `data/basis_tree_depth4.json` (2282 lines,
   327 nodes, 45 server calls).

## Top-level basis entries (10)

All ten are `Folder` instances, each naming a Plant Simulation domain:

| # | Path | Children | Purpose |
|---|---|---|---|
| 1 | `.MaterialFlow` | 23 | Material-flow library (Source, Drain, Buffer, Conveyor, Station, …) |
| 2 | `.Fluids` | 10 | Fluid handling (Tank, Pipe, Mixer, …) |
| 3 | `.Resources` | 10 | Resource handling (Worker, Broker, Exporter, Workplace, …) |
| 4 | `.InformationFlow` | 14 | Information-flow library (DataTable, FileInterface, MQTTInterface, …) |
| 5 | `.UserInterface` | 10 | UI primitives (Dialog, Button, Display, …) |
| 6 | `.MUs` | 3 | Mobile Units (Transporter, AGVPool, …) |
| 7 | `.UserObjects` | 4 | User-defined class frames (only `MyFrame` here) |
| 8 | `.Tools` | 3 | Analysis tools (`BottleneckAnalyzer`, `EnergyAnalyzer`, `ExperimentManager`) |
| 9 | `.Models` | 1 | The **currently loaded model** — `Model` is the top Frame |
| 10 | `.SimtalkClaude` | 4 | The dispatch folder for the Claude-server integration |

> The first 8 folders are Plant Simulation's **standard Class Library** — they
> exist in every model. `.Models` and `.SimtalkClaude` are **model-specific**.

## `.Models.Model` — the loaded model itself

```
.Models  →  Model  (Frame)  →  1 child:
  [EventController] EventController
```

The loaded model has a single EventController (the simulation engine root). At
depth 4 the tree only enumerates the model's direct children — to see the
actual simulation objects (lines, stations, etc.), recurse deeper from
`.Models.Model`.

## `.SimtalkClaude` — the server dispatch folder

```
.SimtalkClaude
├── Frame  main            ← dispatch frame (currently-running model)
│   ├── Variable  Server
│   ├── Frame      SocketServer   (5 children: m_callback, MySocket, m_send, ping_reply, m_str_send)
│   ├── Frame      SimtalkAction  (14 children — see below)
│   └── Frame      SocketClient   (15 children: auth, request, token, sig, session_id, MySocket,
│                                  auth_success, m_send, m_recieve, m_openconnection, Button,
│                                  m_sendauth, m_authback, Button2, m_disconnect)
├── Folder src              (3 children)
│   └── Frame  SimtalkAction  (14 children — same shape as main/.SimtalkAction)
├── Folder connection       (5 children)
│   ├── Frame  SocketClient
│   ├── Frame  SocketServer
│   └── Frame  Logger        (1 child)
└── Folder Objects          (8 children)
```

### `.SimtalkClaude.main.SimtalkAction` (the dispatch Method host)

14 children — the methods that the TCP server invokes when a
`{type:"simtalk_run"}` request arrives:

| # | Type | Name |
|---|---|---|
| 1 | Method | `simtalkcode` |
| 2 | Method | `m_getlog` |
| 3 | Method | `a_readrootlibrary` |
| 4 | Method | `a_readfolder` |
| 5 | Method | `a_readframe` |
| 6 | Method | `get_simtalk_hasError` |
| 7 | Method | `simtalk_hasError` |
| 8 | Variable | `action_result` |
| 9 | Method | `simtalk_execute` |
| 10 | Method | `a_readlog` |
| 11 | Method | `Run_Simutalk` |
| 12 | Method | `ReadLogFile` |
| 13 | Method | `ErrorHandler` |
| 14 | Method | `Method` |

## `.Tools` — analysis & experiment tools (depth 4 fully expanded)

```
.Tools
├── BottleneckAnalyzer       (Folder)
│   ├── BottleneckAnalyzer   (Frame, 22 children)
│   │   └── dialog           (Frame, 11 children)
│   ├── BasicObjects         (Folder, 6 children)
│   │   └── Frame            (Frame, 0 children)
│   └── Localization         (Folder, 5 children)
├── EnergyAnalyzer           (Folder)
│   ├── EnergyAnalyzer       (Frame, 24 children)
│   ├── BasicObjects         (Folder, 8 children)
│   └── Localization         (Folder, 5 children)
└── ExperimentManager        (Folder)
    ├── ExperimentManager    (Frame, 0 children)
    ├── Internal             (Folder, 4 children)
    │   ├── DistributedSimulation (Frame, 11 children)
    │   └── SimulationMachine      (Frame, 12 children)
    ├── BasicObjects         (Folder, 3 children)
    │   ├── InformationFlow  (Folder, 8 children)
    │   ├── UserInterface    (Folder, 4 children)
    │   └── MaterialFlow     (Folder, 2 children)
    │       └── Frame        (Frame, 0 children)
    └── Localization         (Folder, 5 children)
```

## Node type distribution (depth ≤ 4, 327 nodes)

Counts are a fresh recursive walk over `data/basis_tree_depth4.json`:

| Type | Count |
|---|---|
| Method | 115 |
| Variable | 38 |
| Folder | 26 |
| DataTable | 22 |
| Frame | 19 |
| Dialog | 8 |
| Socket | 7 |
| Button | 6 |
| HtmlReport | 6 |
| Chart | 5 |
| DataList | 4 |
| Comment | 4 |
| Part | 3 |
| Connector | 2 |
| EventController | 2 |
| Station | 2 |
| Conveyor | 2 |
| Source / Drain / Buffer / Sorter / Store / Container | 1–2 each |
| Mixer / Tank / Pipe / FluidSource / FluidDrain | 1–2 each |
| Worker / Broker / Exporter / Workplace / WorkerPool | 1–2 each |
| FileInterface / MQTTInterface / FileLink | 1–2 each |
| AttributeExplorer / Display / SankeyDiagram / CostAnalyzer | 1–2 each |

> Many class types appear **once or twice** — the standard class library has
> many classes per type (e.g. 115 Methods across all the loaded class frames).
> The numbers reflect what's actually enumerated in this run; re-running
> against a different model will give different totals but the same shape.

## Quirks observed during this exploration

1. **`obj_to_str(basis)` returns `""`** — basis is the anonymous root identifier
   and has no stringifiable path representation. Every child of basis starts
   with `.` (e.g. `.Models.Model`).
2. **Assigning `any[]` to `j["children"]` clobbers `j`** — the JSON object
   becomes the array. Workaround: build the entire output as a SimTalk string
   buffer (`chr(123) + chr(34) + ...`) and `print` it.
3. **`readlog` v15+ is degraded** — but for a single print right after a
   `simtalk_run` it still captures the printed line in the `log` field.
   Multiple `readlog`s in a tight loop exhibit buffer inflation; this skill
   keeps calls sequential and bounded.
4. **Quirk #6 (`data` empty) means we need `print + readlog`** — every
   enumeration step is a round-trip pair. ~45 round-trips for the depth-4 tree.
5. **`EventController` does not expose `numNodes`** — `.Models.Model.EventController`
   is the loaded model's simulation root, but calling `numNodes` on it returns
   nothing enumerable. The actual simulation objects (lines, stations, MUs)
   inside the EventController cannot be enumerated via this technique; they
   would need a different property (`Children` / `<attribute>` access) and
   fall outside the scope of folder-tree exploration.
6. **`bfs_full.py` recursion whitelist is `(Folder, Frame)` only** —
   `EventController`, `Method`, `Variable`, etc. are leaves. If a tree branch
   has non-Folder/Frame structural nodes that should be recursed into, edit
   the `if ch["type"] in ("Folder", "Frame"):` line in `bfs_full.py`.
7. **Root node field naming differs from children** — the captured JSON uses
   `root_path` / `root_name` / `root_type` / `root_numNodes` for the top-level
   node, but children use `path` / `name` / `type` (no prefix). When walking
   the JSON, handle the root separately or normalize keys first.

## Re-running the exploration

```bash
# Quick re-run on the same server (assumes path layouts haven't changed):
python3 scripts/bfs_one_level.py .                          # 10 top-level
python3 scripts/bfs_one_level.py .SimtalkClaude             # 4 children
python3 scripts/bfs_one_level.py .SimtalkClaude.main        # 4 children
python3 scripts/bfs_one_level.py .SimtalkClaude.main.SimtalkAction   # 14 methods
python3 scripts/bfs_full.py . 4 data/basis_tree_depth4.json # full depth-4 tree
```

For deeper dives into the loaded model:

```bash
python3 scripts/bfs_full.py .Models.Model 8 data/model_tree_depth8.json
python3 scripts/bfs_full.py .SimtalkClaude 5 data/simtalkclaude_tree.json
```