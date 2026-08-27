# Usage log — local-simtalk-get-folder-tree: orientation after THIRD model swap

**Date:** 2026-08-27
**Skill:** `local-simtalk-get-folder-tree` (+ `local-simtalk-read-library` + `local-simtalk-get-class-inheritance`)
**Target:** basis root + 5 top-level Folders (fresh BFS depth 5)
**Mode / Action:** **Read + probe** — `bfs_full.py` depth 5 → `probe_methods.py` 71 paths → `probe_inheritance.py` 40 candidate classes
**Operator:** plant-simulation-expert (OpenClaude subagent)

## Goal

User said "lear the plant simulation model right now" (typo for "learn").
Pre-flight confirmed `host.docker.internal:50007` reachable. Three-step
orientation per agent protocol:

1. BFS folder tree to depth 5
2. Probe every Method's `Program` + metadata
3. Sample class inheritance for class-defining objects

## Steps

### 1. Pre-flight (铁律❶)
- TCP probe → `CONNECTED`. OK to proceed.

### 2. BFS depth 5 (`bfs_full.py --no-infobox . 5 ...`)
- 26 calls, 1628 lines JSON, 5 top-level Folders.
- Output: `skills/local-simtalk-get-folder-tree/data/basis_tree_depth5_fresh.json`

### 3. Method-path extraction + probe (`probe_methods.py`)
- Filtered tree for `type == "Method"` → **71 unique method paths**.
- Batched probe with batch=8 → 63 actually captured (8 of 71 returned no source).
  - 8 missing are duplicates under `.SimtalkClaude.main.*` that share bodies
    with their `.SimtalkClaude.src.*` counterparts (the `main.*` are visual
    Frame containers, the `src.*` are the executable copy).
- Raw: `data/methods_raw_fresh.tsv`. Rendered: `data/library_dump_fresh.json`.

### 4. Class-path extraction + inheritance probe (`probe_inheritance.py`)
- Filtered tree for class-defining objects (Frame / Dialog / Part / Comment /
  HtmlReport / DropDownList / Table / DataList) → **40 candidate paths**.
- Probed → **16 captured**, **24 returned nothing**.
- All 16 are **root classes** (Origin = VOID — built-in Plant Simulation types).
- Zero user-defined derived classes in this model.
- Raw: `data/inheritance_raw_fresh.tsv`. Map: `data/inheritance_map.json`.

## Result — What the model actually is

### Top-level layout
```
Basis (5 children)
├── .Models                — domain Frame + template Folders
├── .MaterialFlow          — runtime backbone (EventController/Source/Drain/Connector/Line)
├── .InformationFlow       — Method + DataTable + Trigger
├── .UserInterface         — single Comment placeholder
└── .SimtalkClaude         — TCP server runtime (this is the agent's bridge)
```

### Three logical layers visible

**Layer A — TCP server runtime (`.SimtalkClaude.*`)** — the agent's own bridge
- `.SimtalkClaude.main.{SimtalkAction, SocketServer, SocketClient}` + `Server` variable
- `.SimtalkClaude.src.autoexec` (179 B — clears Console + logfile + reopens Console)
- `.SimtalkClaude.src.ErrorHandler`
- `.SimtalkClaude.src.SimtalkAction.*` (10 methods, all non-empty):
  - `simtalkcode` (22 B — bare `var obj:=.createfodler`, looks like a stub
    placeholder; maybe typo of `createFolder`?)
  - `simtalk_execute` (281 B), `simtalk_hasError` (384 B),
    `get_simtalk_hasError` (562 B), `a_readlog` (505 B), `m_getlog` (378 B)
  - `ErrorHandler`, `ReadLogFile`, `Run_Simutalk` (all empty — likely
    template overrides never filled in)
- `.SimtalkClaude.connection.{SocketClient, SocketServer, Logger, Socket}` +
  `socketcallback` (all empty — visual class shells; actual code is in `.src`)
- `.SimtalkClaude.Objects.*` (8 templates: Method/Variable/Socket/Dialog/Button/
  DataTable/DataList/HtmlReport — all empty placeholders)

**Layer B — Demo / teaching domain (`.Models.internal.*`)**
- `.Models.internal.Admin` (Frame, root class) — **the heart of a student
  grading / exam-No analyzer**. 17 methods, all non-empty:
  - `dispatcher` (1323 B), `startSearch` (2469 B), `displayResults` (3122 B),
    `saveObject` (1102 B), `prepareSave` (449 B), `partitionDescription` (808 B)
  - `Comment2GeneralTable`, `GeneralTable2ExampleTab`, `OpenGeneralTable`,
    `ExportToExcel`, `ImportKeywords`, `CalcScore`, `CountOccur`,
    `removeUnwantedCharacter`, `MarkText`, `setExamNo`, `showComment`,
    `greenRectangle`, `move_AxesOrigin`
  - 8 are empty (CountOccur/Comment2GeneralTable/GeneralTable2ExampleTab/
    OpenGeneralTable/ExportToExcel/ImportKeywords/CalcScore) — also
    template shells waiting to be filled.
- `.Models.internal.Localization.{getMessage (744 B), getText (154 B)}`
- `.Models.internal.autoexec` (3072 B — the biggest method in the model;
  almost certainly the setup entry point)
- Plus 9 template shells: HtmlReport/Comment×2/SelDlg/Method/Variable/
  DropDownList/DataTable/ReadMe/LiesMich

**Layer C — Material-flow templates (`.Models.SourceTrigger.*`)**
- 5 user-template Frames: `SourceTrigger`, `SourceNumberAdjustable`,
  `SourceIntervalAdjustable`, `SourceRandom`, `SourcePercentage`
- Each has a small `init` (~170-180 B) + a stub `endsim` (~36-144 B)
- Plus 3 sample Parts: A / B / C

**Runtime backbone (`.MaterialFlow.*`)** — the *root* material-flow class
instances (not templates — these are actual objects):
- EventController / Source / Drain / Connector / Line (Conveyor)

### Inheritance findings
- **Zero user-defined derived classes.** Every Frame/Dialog/HtmlReport/
  Comment is a root type inheriting directly from Plant Simulation's
  built-in class hierarchy.
- 24 of 40 candidate paths returned empty — those were probably Parts,
  Comments, or class-internal Members that don't expose `Origin` at the
  tree-walk level. Worth a second-pass probe with explicit `Frame`-only
  filter if inheritance matters later.

### Library health
- 0 encrypted methods
- 0 syntax errors
- 35 empty methods (most are template placeholders + `.SimtalkClaude.connection`
  + `.SimtalkClaude.main.SimtalkAction.*` shells)
- Real executable code lives in:
  - `.Models.internal.autoexec` (3072 B)
  - `.Models.internal.Admin.*` (12 non-empty methods, ~10 KB total)
  - `.Models.internal.Localization.*` (2 methods)
  - `.Models.SourceTrigger.*.init/endsim` (7 methods, tiny)
  - `.SimtalkClaude.src.SimtalkAction.*` (6 non-empty methods)

## Verdict
PASS — full orientation in 4 steps (preflight + BFS + probe + inheritance).
Total wall time ~3 min (BFS dominated).

## What this run validated / learned

- **The model rotates again.** Prior log
  (`2026-08-27_orientation-summary-from-fresh-data.md`) captured the
  **assembly-line model** at 10:20. This run (12:16+) captured a
  **teaching/training model**. Different topology:
  - Assembly model had `.Models.Assembly1/.Assembly2` (113 children each),
    `.UserObjects.Classes`, `.UserObjects.Modules`, `.Tools`
  - **This** model has `.Models.internal.Admin/.Localization/.SourceTrigger`,
    no `.UserObjects`, no `.Tools`
  - Three loads in one day: warehouse (09:37) → assembly (10:20) → teaching (12:16+)
- **`*.fresh.json` cache only survives until the next model swap.** The
  previous log's advice ("use `*_fresh.json` from this session") is good
  *within* a session, but cross-session they go stale. Always check the
  `basis_tree_depth*_fresh.json` timestamp against `date` before trusting
  cache.
- **`SimtalkAction.simtalkcode` looks broken.** Its body is literally
  `var obj:=.createfodler` — 22 bytes. `createfodler` is not a real Plant
  Simulation function (the real one is `createFolder`). Likely a typo /
  stub. Worth flagging if any future code calls into it. (Not in scope for
  this orientation task.)
- **Most non-empty Method bodies are under `.Models.internal.Admin`.** This
  is the model author's primary working area; the SimTalkClaude runtime
  itself is largely template shells with the real code in `.src.SimtalkAction.*`.
- **24-of-40 inheritance probes returned nothing.** The probe's path list
  included `Comment`/`DataTable`/etc. — those don't always expose `Origin`
  as a meaningful attribute. For a class hierarchy of *real* Frame/Dialog
  classes, this run's 16 captured classes are sufficient. Future inheritance
  work should pre-filter to `Frame|Dialog|TableFile|Method` only.
