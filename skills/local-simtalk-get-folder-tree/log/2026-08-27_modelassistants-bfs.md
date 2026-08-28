# Usage log — BFS-enumerate `.ModelAssistants` to depth 4

**Date:** 2026-08-27  **Skill:** `local-simtalk-get-folder-tree`  **Target:** `.ModelAssistants`
**Mode / Action:** `bfs_full.py` depth=4  **Operator:** plant-simulation-expert

## Goal
The user asked to study the model `ModelAssistants`. First action: enumerate the
folder/frame hierarchy so I know what's inside before any read-library /
class-inheritance probing.

## Steps
1. Pre-flight TCP probe: `host.docker.internal:50007` → **CONNECTED**.
2. First probe `bfs_one_level.py ""` failed (`ERR: cannot resolve path: ""`)
   — empty-string root path is rejected. Switched to `"."` per SKILL.md usage
   example → success. Located `.ModelAssistants` at index 13 / 14 of basis
   root (between `.DefaultLibrary` and `.SimtalkClaude`).
3. Full recursive BFS: `bfs_full.py .ModelAssistants 4 .../ModelAssistants_depth4.json`
   → 21 round-trips, tree written to disk.

## Result
- `numNodes` at root = **14** (top-level subfolders / sub-frames under basis).
- `.ModelAssistants` contains 14 direct children (13 Frames + 1 Folder +
  1 Folder under BasicObjects + Internal). Layout captured in
  `data/ModelAssistants_depth4.json` (1258 lines).
- Top-level Frame toolkit (11 production frames + 3 support frames):
  | Sub | Type | Role |
  |---|---|---|
  | `Assistants` | Frame | User-menu / icon management (M_AddUserMenu, M_TransCtrl, …) |
  | `ClassAssistant` | Frame | Class-library operations (search, derive, add BscObj) |
  | `AutoSave` | Frame | Periodic model autosave with stop/pause hooks |
  | `Namer` | Frame | Object-rename utility (sort keys, prefix strategy) |
  | `FrameReplacer` | Frame | Find/replace object paths in DataTables |
  | `QuickArrayTool` | Frame | Quick 2D-array helper |
  | `FrameEncrypt` | Frame | Frame / method encryption tool |
  | `ClassAttrDepulicator` | Frame | Copy attribute values between class instances |
  | `Calculator3D` | Frame | 3D rotation / position converter (M_Convert, M_AutomaticRotate) |
  | `AIBot` | Frame | Python-integration bridge (Py_SendRequest + M_SendRequest) |
  | `ModelSyncCopy` | Frame | TCP-based model serialize/deserialize (the heaviest, 6 KB method) |
  | `Templates` | Method | Stub (empty body) |
  | `BasicObjects` | Folder | Template skeletons for new MF / IF / UI objects |
  | `Internal` | Folder | Lifecycle hooks (`autoexec`, `onCloseModel`, `autoexecLoadObj`) + a Socket |

## Verdict — PASS
Full BFS into `.ModelAssistants` succeeded in 21 calls; tree dumped to disk and
ready for downstream skill consumption (read-library / class-inheritance).

## What this run validated / learned
- `bfs_one_level.py` **does not accept empty path** — use `"."` for basis root.
  This was a first-call stumble; nothing more serious than a one-line error.
- The model is **clearly a productivity toolkit for Plant Simulation modelers**
  (a "Swiss-army-knife" Frame library). All Frame-typed top-level children are
  UI-driven dialogs that operate on the current model.
- `BasicObjects` is a **template library** — Frame, Dialog, Connector, Method,
  Variable, DataTable, PythonModule, Socket. New helper frames reuse these as
  starting points (visible in inheritance dump).