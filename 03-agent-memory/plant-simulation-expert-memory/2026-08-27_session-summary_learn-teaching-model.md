# Session Summary — Learn the currently loaded Plant Simulation model (NEW: teaching model, third swap today)

**Date:** 2026-08-27  **Agent:** plant-simulation-expert
**Duration:** ~5 min (single-turn orientation)
**Skills called:** `local-simtalk-execution` (transport), `local-simtalk-get-folder-tree` (1 BFS depth 5), `local-simtalk-read-library` (1 batch probe, 71 paths), `local-simtalk-get-class-inheritance` (1 batch probe, 40 candidate paths)

## Goals

User: "you are @/root/skills_of_plant_simulation/agents/plant-simulation-expert-by-simtalkclaude.md , lear the plant simulation model right now" — orient on whatever model is currently loaded in Plant Simulation right now. Three layers:
1. Folder/Frame/Method topology
2. Every Method's `Program` source
3. Class inheritance for class-defining objects

## What was done

1. **Pre-flight ✅** — `host.docker.internal:50007` CONNECTED.
2. **BFS depth 5** (`bfs_full.py --no-infobox . 5 ...`) — 26 calls,
   5 top-level Folders: `Models / MaterialFlow / InformationFlow / UserInterface / SimtalkClaude`.
3. **Method-path filter + probe** (`probe_methods.py`) — 71 unique Method
   paths, 63 captured (8 silent duplicates under `.SimtalkClaude.main.*`
   that share bodies with `.SimtalkClaude.src.*`), 0 encrypted,
   0 syntax errors, 35 empty templates. Library dump →
   `data/library_dump_fresh.json`.
4. **Class-inheritance probe** (`probe_inheritance.py`) — 40 candidate
   paths, 16 captured, **all 16 are root classes (Origin=VOID)**, **zero
   user-defined derived classes**. Inheritance map →
   `data/inheritance_map.json`.
5. **Usage log written** →
   `skills/local-simtalk-get-folder-tree/log/2026-08-27_orientation-summary-from-fresh-data-2.md`
   (preserves prior 10:20 log as `-1` variant; this is `-2`).

## Key findings / decisions

- **Model is NOT yesterday's Factory51 OR today's earlier assembly model.**
  Third distinct model loaded today. Three swaps in one day:
  1. ~09:37 — warehouse (`.Models.Factory51`, 142 children, WMS + portal crane + AGV)
  2. ~10:20 — assembly line (`.Models.Assembly1/.Assembly2`, 113 children each, conveyor + PalletOptimization + WorkerChart + EnergyAnalyzer)
  3. **~12:16 (now) — teaching model**: `.Models.internal.Admin` (Frame, 17 methods, student-grading/exam-No analyzer) + `.Models.internal.Localization` + `.Models.SourceTrigger.*` (5 Source template Frames + 3 sample Parts) + the SimTalkClaude TCP runtime.
- **Layered architecture**:
  - **Layer A — TCP server runtime** (`.SimtalkClaude.*`) — the agent's own bridge; real code in `.SimtalkClaude.src.SimtalkAction.*` (6 non-empty methods); `main.*` + `connection.*` are visual shell templates.
  - **Layer B — Demo / teaching domain** (`.Models.internal.*`) — `Admin` Frame is the model author's working area; `autoexec` (3072 B) is the largest method in the model.
  - **Layer C — Material-flow templates** (`.Models.SourceTrigger.*`) — 5 Source variants + Parts.
  - **Runtime backbone** (`.MaterialFlow.*`) — root MaterialFlow class instances (Source, Drain, Conveyor, Connector, EventController).
- **No user-defined classes.** Every Frame/Dialog/HtmlReport/Comment inherits directly from Plant Simulation built-ins. Worth flagging if user later asks "what classes does this model define" — answer is "none derived".
- **35 empty Methods are mostly template placeholders** (template class shells under `.SimtalkClaude.connection`, `.SimtalkClaude.main.SimtalkAction.*`, `.Models.internal.Admin.*`, `.Models.SourceTrigger.*` etc.). Real code lives in 28 methods concentrated in `.Models.internal.Admin.*` (~10 KB total), `.Models.internal.autoexec`, `.Models.internal.Localization.*`, and `.SimtalkClaude.src.SimtalkAction.*`.
- **Possible bug spotted** (out of scope): `.SimtalkClaude.src.SimtalkAction.simtalkcode` body is literally `var obj:=.createfodler` (22 B). `createfodler` is not a real PS function — likely typo of `createFolder`. Flagging in case user wants to fix later.

## Cross-references

- `skills/local-simtalk-get-folder-tree/data/basis_tree_depth5_fresh.json` (this run's BFS)
- `skills/local-simtalk-read-library/data/library_dump_fresh.json` (63-Method library dump)
- `skills/local-simtalk-get-class-inheritance/data/inheritance_map.json` (16 root classes, 0 derived)
- `skills/local-simtalk-get-folder-tree/log/2026-08-27_orientation-summary-from-fresh-data-2.md` (this run's usage log)
- `skills/local-simtalk-get-folder-tree/log/2026-08-27_orientation-summary-from-fresh-data.md` (the 10:20 assembly-model log — same day, different model)
- `03-agent-memory/plant-simulation-expert-memory/2026-08-27_session-summary_learn-factory51-model.md` (09:37 warehouse summary)
- `03-agent-memory/plant-simulation-expert-memory/2026-08-27_session-summary_learn-new-assembly-model.md` (10:20 assembly summary)

## Open questions / next steps

- Model rotates every ~1-2 hours today; new runs MUST re-verify which model is loaded (`bfs_full.py` depth 1 of `.` is cheap and definitive).
- If user wants to drill into the teaching model next: start with `.Models.internal.autoexec` (3072 B, the entry point) then `.Models.internal.Admin.dispatcher` (1323 B, the main flow controller).
- If user wants to extend the agent runtime: focus on `.SimtalkClaude.src.SimtalkAction.simtalk_execute` (281 B — the actual code-execution handler) — that's the hottest path for the TCP bridge.
- Open bug to surface (not actioned): `.SimtalkClaude.src.SimtalkAction.simtalkcode` body is a 22-byte stub with a typo (`createfodler`).
