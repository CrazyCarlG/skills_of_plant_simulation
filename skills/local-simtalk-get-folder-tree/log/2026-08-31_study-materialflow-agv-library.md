# Usage log — Study MaterialFlow_AGV library structure

**Date:** 2026-08-31  **Skill:** `local-simtalk-get-folder-tree` + `local-simtalk-get-class-inheritance` + `local-simtalk-read-library` (study only)  **Target:** `.MaterialFlow_AGV.*`
**Mode / Action:** read / inspect  **Operator:** plant-simulation-expert

## Goal
Understand the structure and class layout of Plant Simulation's `MaterialFlow_AGV` library so I can design an optimized user-space replacement under `AGV_Claude`.

## Steps
1. Connected to `host.docker.internal:50007` (source model — only port up).
2. Probed root via `bfs_full.py . 1` → root name **"Basis"** with 12 children. Among them: `MaterialFlow_AGV` (target library) and a previously-created `AGV_Claude` folder (sibling).
3. `bfs_full.py .MaterialFlow_AGV 3` revealed 3 top-level subfolders: `BasicObjects`, `AdvancedObejcts` (typo — vendor's spelling), `Area`.
4. `probe_inheritance.py` on the AdvancedObjects classes returned:
   - `PalletAGV` (Transporter) inherits from `.MaterialFlow_AGV.basicObjects.MUs.Transporter`
   - `BoxAGV` (Transporter) same parent
   - `AGVPool` (AGVPool) inherits from `.MaterialFlow_AGV.basicObjects.Resources.AGVPool`
   - `Marker` (Marker) inherits from `.MaterialFlow_AGV.basicObjects.Resources.Marker`
   - `CapacityCalculation_v2` (Frame) — standalone, content not dumpable via bfs_full (JSON parse error)
   - `OrderCreater` (Source) inherits from `.MaterialFlow_AGV.basicObjects.MaterialFlow.Source`
5. Read `01-plantsimulation-knowledge/01-plant-simulation-help/objects/resource-objects/AGVPool/` for AGVPool API:
   - Methods: `getAssignedAGV(No)`, `getAssignedAGVsTable([tab])`, `getIdleAGV()`
   - Read-only: `NumIdleAGVs`, `StatAverageTraveledDistance`
   - Attributes: `AGV` (vehicle class path), `Amount`, `ShiftCalendarObject`
6. `read_library.py` (default depth 5) dumped `data/library_dump.json` — but at depth 5 doesn't reach into `MaterialFlow_AGV.AdvancedObejcts.CapacityCalculation_v2` (which is Frame). Its internal methods are unreachable by BFS.

## Result
| Path | Existence | Inherits From |
|---|---|---|
| `.MaterialFlow_AGV` | ✅ Folder | — |
| `.MaterialFlow_AGV.AdvancedObejcts.PalletAGV` | ✅ Transporter | `.MaterialFlow_AGV.basicObjects.MUs.Transporter` |
| `.MaterialFlow_AGV.AdvancedObejcts.BoxAGV` | ✅ Transporter | same |
| `.MaterialFlow_AGV.AdvancedObejcts.AGVPool` | ✅ AGVPool | `.MaterialFlow_AGV.basicObjects.Resources.AGVPool` |
| `.MaterialFlow_AGV.AdvancedObejcts.Marker` | ✅ Marker | `.MaterialFlow_AGV.basicObjects.Resources.Marker` |
| `.MaterialFlow_AGV.AdvancedObejcts.CapacityCalculation_v2` | ✅ Frame | (standalone) |
| `.MaterialFlow_AGV.AdvancedObejcts.OrderCreater` | ✅ Source | `.MaterialFlow_AGV.basicObjects.MaterialFlow.Source` |
| `.AGV_Claude` | ✅ Folder | (empty, just created) |

## Verdict — PASS
Enough information collected to design AGV_Claude. Vendor uses *typo* `AdvancedObejcts` (not `AdvancedObjects`) — future paths must respect this.

## What this run validated / learned
- **Path quirk**: The vendor library uses `AdvancedObejcts` (typo). All class paths under it follow this spelling.
- **BFS parse failure**: `CapacityCalculation_v2` frame BFS dump fails with "Unterminated string" — likely contains methods with embedded quotes / special chars that the BFS serializer can't handle. Workaround: read its methods via direct path or skip.
- **AGVPool API surface** is small (3 methods + 2 read-only + 3 attributes). Optimizations must be added ON TOP — not via overriding.
- **`NumIdleAGVs`** is watchable → can be used as a precondition in `waituntil` without polling overhead.
- **`getIdleAGV()`** sets `IsIdle = false` automatically — caller must remember to reset.
