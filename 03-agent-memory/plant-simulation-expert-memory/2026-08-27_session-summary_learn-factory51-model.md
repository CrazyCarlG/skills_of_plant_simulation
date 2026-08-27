# Session Summary — learn loaded Factory51 model via SimTalkClaude TCP
**Date:** 2026-08-27
**Agent:** plant-simulation-expert
**Duration:** ~1 turn (cold-start of session)
**Skills called:** `local-simtalk-get-folder-tree`, `local-simtalk-execution` (transport only)

## Goals

Orient on the Plant Simulation model currently loaded in the user's GUI by
probing the TCP bridge at `host.docker.internal:50007`, enumerating the
Class Library (basis) tree, and characterizing the user's main model Frame
(`.Models.Factory51`).

## What was done

- **Pre-flight ✅** — `host.docker.internal:50007` reachable; `ping` returns
  `success`. SimTalkClaude server is live.
- **Depth-4 BFS ✅** — `bfs_full.py --no-infobox . 4` → 48 round-trips,
  `data/basis_tree_depth4_fresh.json` written. Captures the entire class
  library to depth 4 (basis + 9 top-level folders + their children).
- **Whole-model type aggregation ✅** — 767 nodes, 43 distinct types.
  Top contributors: Variables (204), Methods (181), Connectors (58), Comments
  (44), Conveyors (29). Method inventory split cleanly into HBW3D reference
  (`ApplicationObjects.HBW3D.*`), user warehouse (`UserObjects.Warehouse.*`),
  CranesAndMore helpers, and the SimtalkClaude TCP-bridge skeleton
  (`SimtalkClaude.main.*` + `SimtalkClaude.src.*`).
- **Factory51 child-type breakdown ✅** — confirmed 142 direct children via
  `simtalk_run`. Mix dominated by Connectors (58), Conveyors (~20),
  PickAndPlaces (6), Tracks (6, incl. cranes), Converters, Stores, Buffers,
  Sources/Drains, plus 5 Variables, 2 SankeyDiagrams, AGVPool,
  EventController, CostAnalyzer, HtmlReport, and 2 Methods
  (`userSetTarget`, `UnloadTruck`).

Per-skill log:
- `skills/local-simtalk-get-folder-tree/log/2026-08-27_basis-depth4-full-and-factory51-types.md`

## Key findings / decisions

- **The model is `Factory51`, not `.Models.Model`.** An earlier
  2026-08-27 minimal-probe log captured a different (near-empty) model
  state. Today's session reflects a 142-child production layout.
- **User is doing pallet-warehouse + crane + AGV orchestration.** Strong
  signals: 5 `RackLane` instances with WMS clones in `.UserObjects.Warehouse`,
  `MultiPortalCrane` + `SmallCrane` Tracks, `AGVPool`, `ChargeTrack1/2`
  (charging stations for AGVs), `EmptyPalletsStore`, `StorageArea`,
  `StoreEntry/Exit`, `PalDeliveryInterval`, `TrucksArrived/Missed` Variables.
- **`bfs_one_level.py` truncates stdout JSON for sub-frames with > ~130
  children.** Factory51 (142) hit the readlog buffer ceiling. Use
  `bfs_full.py <path> 1 <out>.json` for clean dumps of large frames in the
  future.
- **SimTalk `var d : dictionary` and `make("Dictionary")` are both
  syntax errors in `simtalk_run`.** Workaround: per-child `print` lines +
  external aggregation.
- **Cached `data/basis_tree_depth4.json` (2026-08-26) is now stale.**
  Replaced by `basis_tree_depth4_fresh.json`.

## Cross-references

- `skills/local-simtalk-get-folder-tree/SKILL.md` — read for protocol
- `skills/local-simtalk-get-folder-tree/log/2026-08-27_basis-depth4-full-and-factory51-types.md` — per-skill usage log
- `skills/local-simtalk-get-folder-tree/log/2026-08-27_basis-and-models-model-tree.md` — earlier minimal-state probe (different model)
- `skills/local-simtalk-get-folder-tree/data/basis_tree_depth4_fresh.json` — fresh cached tree
- `skills/local-simtalk-get-folder-tree/data/basis_tree_depth4.json` — superseded by above
- `skills/local-simtalk-execution/references/lifelines.md` §5 — readlog v15+
  degradation, explains why 2nd+ readlog per session only returns the
  "Log file opened!" line
- `.ApplicationObjects.HBW3D.*` — reference warehouse impl
- `.UserObjects.Warehouse.*` — user's warehouse impl (WMS + 5 RackLanes)
- `.UserObjects.Polishing*`, `Milling`, `Shipment`, `Painting`, `Drying`,
  `PostProcess*`, `Production`, `Warehouse`, `Line` — production-line
  components under `.UserObjects.*`

## Open questions / next steps

- **Drill into the WMS / RackLane methods.** These are the load-bearing
  simulation logic; need to read source before any modification.
- **Inspect `.SimtalkClaude.main.SimtalkAction.simtalk_execute` source.**
  It's the bridge between incoming TCP JSON and Plant Simulation code
  execution — understanding it is the foundation for any custom protocol work.
- **Drill into `.UserObjects.Warehouse.*` (5 RackLanes + WMS) and
  `.Models.Factory51.Warehouse` (inbound/outbound pallet store).** Likely
  next target for "modify SimTalk" tasks.
- **Clean up the stale `data/basis_tree_depth4.json`.** Future drift risk.
- **Verify the TCP-bridge auth handshake** before any write that goes
  through it (to avoid silent `result:success` + `log: code execute failed`
  — see lifelines §4 / team-memory `simtalk-run-soft-failure-design.md`).
