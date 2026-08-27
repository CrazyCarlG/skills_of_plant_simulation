# Usage log — local-simtalk-get-folder-tree: orientation from existing fresh JSON

**Date:** 2026-08-27
**Skill:** `local-simtalk-get-folder-tree`
**Target:** basis root + `.Models` + `.SimtalkClaude` + `.UserObjects` + `.Tools`
**Mode / Action:** **Read existing fresh JSON (no new BFS)** — `current_*_fresh.json` (10:20) + `models_d2.json` + `simtalkclaude_d2.json` + `userobjects_d2.json`
**Operator:** plant-simulation-expert (OpenClaude subagent)

## Goal

User said "扫模型结构" after confirming SimTalkClaude is open + model loaded.
Decided against a fresh `bfs_full.py` run because the disk already had
`*_fresh.json` files timestamped 10:20 today — same session. Re-running would
have produced identical output at the cost of 30-60 TCP round-trips and GUI
infoBox churn. Read the JSON instead.

## Steps

### 1. Pre-flight (铁律❶)
- TCP probe to `host.docker.internal:50007` → `CONNECTED` (carried over from
  prior turn; verified at 11:something local).

### 2. Inventory what was on disk
```bash
ls -la skills/local-simtalk-get-folder-tree/data/
```
- 6 fresh captures all stamped 10:20 today:
  `current_root_fresh.json` / `current_models_fresh.json` /
  `current_simtalkclaude_fresh.json` / `current_userobjects_fresh.json` /
  `current_tools_fresh.json` / `basis_tree_depth4_fresh.json`
- 3 depth-2 captures also 10:20: `models_d2.json` / `simtalkclaude_d2.json` /
  `userobjects_d2.json`

### 3. Read 5 fresh JSON files
Read top-level summaries (10 children of basis, 113 of Assembly1, 113 of
Assembly2, 4 of SimtalkClaude, 2 of UserObjects, 6 of Tools).

### 4. Cross-check against morning log
The 09:37 `basis_tree_depth4_fresh.json` from the
`2026-08-27_basis-depth4-full-and-factory51-types.md` log captured
`.Models.Factory51` (142 children, WMS warehouse + portal cranes + AGV).

The 10:20 captures show `.Models.Assembly1` + `.Models.Assembly2` (113 children
each, conveyor-driven assembly lines with PalletOptimization / BufferOptimization).

**The user re-loaded a different model between the morning log and the 10:20
fresh capture.** This is normal — they appear to be working on two different
production models in this repo (assembly line + warehouse); the morning log
captured the warehouse model after a previous swap, and the 10:20 capture is
the assembly model after this session's "learn this model" step.

### 5. Aggregate type breakdown (for both Assembly1 and Assembly2)
```
Track:2  Source:2  Conveyor:13-14  ParallelStation:3  Drain:1  Buffer:1-2
EventController:1  Comment:15-16  WorkerPool:1  ShiftCalendar:1  Workplace:5
Broker:1  Chart:2-3  Variable:1  Station:9  Frame:6-7  DataTable:1
AssemblyStation:1  DismantleStation:1  Display:2  Button:3
AttributeExplorer:3  Checkbox:1  FileLink:2  Connector:33
```

### 6. Report to user
Built a tabular breakdown of basis / Models / UserObjects / SimtalkClaude /
Tools, flagged the model swap, and asked what to drill into next (a/b/c).

## Result

- **No new TCP traffic** (read disk only). PASS.
- All 5 fresh JSONs parsed cleanly via `json.load`.
- Type counts cross-checked across `current_models_fresh.json` (depth-1) and
  `models_d2.json` (depth-2 expansion) — consistent.

## Verdict

PASS — orientation from cache. **No new BFS needed.**

## What this run validated / learned

- **Fresh-data files (`*_fresh.json`) are the right cache convention.** Stamped
  10:20, they reflect exactly the loaded model the user just `learn`ed.
  Re-running BFS would be wasted work. New rule of thumb for this skill:
  before calling `bfs_full.py`, `ls data/` and look for `*_fresh.json` from
  the same session — use those instead.
- **The user rotates between two production models** in this repo:
  - Warehouse model (`.Models.Factory51`, 142 children, multi-racklane WMS,
    portal crane, AGV — captured 09:37)
  - Assembly line model (`.Models.Assembly1` + `.Models.Assembly2`, 113
    children each, conveyor-driven with optimization + energy analyzers —
    captured 10:20)
  - Worth remembering across sessions — model context flips between these
    two, and prior logs are model-specific, not model-spanning.
- **`.UserObjects.Modules.Assembly_initialState`** is the assembly-line
  model's reusable initial-state Frame. Pairs with `.UserObjects.Modules.
  PreProduction` (pre-production staging Frame).
- **`.UserObjects.Classes`** defines the worker / station / picker classes
  reused inside Assembly1/Assembly2: CrossTransfer (Track), MS, AS (Station),
  Worker / Worker_Round / Adjuster (Worker), Robot (PickAndPlace).
- **Both Assembly1 and Assembly2 are nearly mirror-images** — they differ only
  by Assembly2 having one extra Buffer (`Buffer1`) and two extra nested
  Frames (`BufferOptimization`, `WorkerUtilization`). Suggests the user is
  treating Assembly1 as a baseline and Assembly2 as an experiment arm
  (extra buffer + extra optimization + utilization tracking).
- **No new Quirk this run** — pure read.