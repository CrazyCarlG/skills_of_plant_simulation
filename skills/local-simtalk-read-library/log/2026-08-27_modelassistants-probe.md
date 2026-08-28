# Usage log — Probe 79 methods of `.ModelAssistants`

**Date:** 2026-08-27  **Skill:** `local-simtalk-read-library`  **Target:** `.ModelAssistants.*` (all Method paths from BFS)
**Mode / Action:** `probe_methods.py` BATCH=8  **Operator:** plant-simulation-expert

## Goal
Dump every Method's metadata (path, name, type, encrypted, has-syntax-error,
num-in-execution) + verbatim `&Method.Program` source for `.ModelAssistants.*`.

## Steps
1. Filtered `data/ModelAssistants_depth4.json` for `type == "Method"` → 79
   paths; wrote `data/ModelAssistants_method_paths.txt`.
2. Ran `probe_methods.py <paths> <out.tsv>` (default BATCH=8, ~10 batches).
3. Output `data/ModelAssistants_probe.tsv` → re-parsed into structured JSON
   `data/ModelAssistants_library.json`.

## Result
| Metric | Count |
|---|---|
| Total Methods probed | 79 |
| Encrypted | 0 |
| Has syntax error | 0 |
| Empty body (program_len=0) | 24 (lifecycle hooks + Dialog event handlers + AIBot methods) |
| Currently in execution | 24 (matches empty-body set → those are loaded but never invoked) |

**Top-10 longest methods** (by program_len):
| chars | path |
|---|---|
| 6396 | `.ModelAssistants.ModelSyncCopy.M_BuildFrameNodes` |
| 5369 | `.ModelAssistants.ModelSyncCopy.M_ApplyObject` |
| 3375 | `.ModelAssistants.QuickArrayTool.ArrayObjects` |
| 2788 | `.ModelAssistants.ModelSyncCopy.M_BuildObject` |
| 2283 | `.ModelAssistants.ModelSyncCopy.M_OnReceive` |
| 1941 | `.ModelAssistants.Calculator3D.M_Convert` |
| 1912 | `.ModelAssistants.ModelSyncCopy.M_BuildFrameMeta` |
| 1698 | `.ModelAssistants.ModelSyncCopy.M_Send` |
| 1640 | `.ModelAssistants.ClassAssistant.AutoSorter` |
| 1608 | `.ModelAssistants.Calculator3D.M_AutomaticRotate` |

**Architectural observations**:
- `ModelSyncCopy` dominates size — it's a full **TCP-based model replication
  protocol**: `M_BuildObject` / `M_BuildFrameNodes` serialize a Frame into
  custom FS/RS (chr(1)/chr(2)) delimited payload; `M_ApplyObject` /
  `M_ApplyFrame` reverse the process on the receiver; `M_OnReceive` parses
  length-prefixed chunks (`headerLen`, `need`, `p`) to handle TCP
  fragmentation; `M_Send` uses `RxBuffer` / `ChunkSize` to break large
  payloads. Frames, attributes, positions, icons, and class metadata are all
  walked.
- `AIBot` (Python integration) — has `Py_SendRequest` (PythonModule),
  `M_SendRequest`, `M_Response`, `M_SetPyEnv`, plus `PythonDLLPath` variable
  for the embedded Python interpreter path. Methods are empty — code lives in
  the Python module.
- `Internal.autoexec` / `onCloseModel` / `autoexecLoadObj` are empty —
  these are lifecycle hooks that would be filled in per-deployment.

## Verdict — PASS
All 79 methods probed, structured JSON dump complete and saved.

## What this run validated / learned
- **Probe script writes TSV with embedded newlines in the program body** —
  naïve `csv.reader` split each Method across multiple rows. Recovery:
  split raw text by lines starting with `.` and having 8+ tab-separated
  fields, then accumulate body lines until the next record starts. After
  re-parse, only 1 row had a 1-char mismatch (`.Templates` actual=252 vs
  declared=251 — trailing newline). All 79 bodies recovered.
- The 24 empty-body methods (24 = currently in execution count) are exactly
  the lifecycle / event stubs that get filled per-deployment. Worth noting
  if a future dump wants to exclude them.
- `probe_methods.py` supports `--no-infobox` correctly; `probe_inheritance.py`
  **does not** (positional args only, always emits infoBox). Inconsistency
  in the skill family.