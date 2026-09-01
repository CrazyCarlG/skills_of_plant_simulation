# Usage log — Create `.AGV_Claude` library (2 DataTables + 7 Methods)

**Date:** 2026-08-31  **Skill:** `local-simtalk-write-simtalk` (+ `local-simtalk-class-management` + `local-simtalk-create-method-object`)  **Target:** `.AGV_Claude.*`
**Mode / Action:** write-simtalk (replace mode) × 7  **Operator:** plant-simulation-expert

## Goal
Populate the AGV_Claude optimized library created by `class_ops.py derive` and `create_method_object.py` with SimTalk source code for each method, then run `AGV_init` to set up the Jobs + Telemetry tables.

## Steps
1. **class_ops.py derive** 4 elements:
   - `.AGV_Claude.Objects` (Folder)
   - `.AGV_Claude.Objects.AGVJobs` (DataTable)
   - `.AGV_Claude.Objects.AGVTelemetry` (DataTable)
   - `.AGV_Claude.Pool` (Frame)
2. **create_method_object.py × 7**: AGV_init, AGV_dispatch, AGV_release, AGV_requestCharge, AGV_dashboard, AGV_batchedRoute, AGV_reset
3. **write_simtalk.py × 7**: all methods written, each `[verify] method executes OK after edit`
4. **simtalk_send.py syntax** to invoke `str_to_obj(".AGV_Claude.Pool.AGV_init").execute` — execute success, headers populated.

## Result
- AGV_init: 839 bytes, setSize + 17 header cell assignments
- AGV_dispatch: scores by `1/(1+distanceTo(pickStation))`, filters `BatCharge >= minBattery`
- AGV_release: upsert pattern into AGVTelemetry by column 1 (AGV ref)
- AGV_requestCharge: scans pool, returns 1-col table of low-battery AGVs
- AGV_dashboard: prints per-pool idle/busy + cumulative distance
- AGV_batchedRoute: chains `Destination := stop[0, i]`, ends with `agv.move`
- AGV_reset: `setSize(1, cols)` truncate, returns count

All 7 methods verified PASS via write_simtalk verify step. Tree dump at `/tmp/agvclaude_final.json` shows full hierarchy.

## Verdict — PASS (with caveats)
- Code is in place and syntactically valid (write_simtalk verify).
- **Caveat 1**: methods depend on caller passing arguments through Method dialog, not source-level `param x: type` (which IS valid syntax but declaration lives in GUI Parameters tab — out-of-band via TCP).
- **Caveat 2**: `AGV_dashboard` uses `print`; v15+ readlog regression means user must check GUI Console manually.
- **Caveat 3**: not yet validated against actual AGV instances — needs a minimal demo model with 1 AGVPool + 2 Stations to fully exercise dispatch/release/charge.

## What this run validated / learned
- **Quirk #10 hit**: writing SimTalk files starting with `--` comment lines via write_simtalk fails because argparse --note stops at first `--` token. Workaround: `grep -v '^--' file.sim` before write, or change comments to `//` form. Should be documented in lifelines.md.
- **Quirk #2 confirmed**: `str_to_obj("...")[0, 0] := "..."` chain-index parse error — must use `var t : table; t := str_to_obj(...); t[0, 0] := "..."`.
- **Quirk #4 confirmed**: `param x: type, y: type` (comma-separated) is valid SimTalk 2 syntax in v18+.
- **`class_ops.py derive` is the reliable way to create Folder/DataTable children** — direct `createObject` from SimTalk is fragile.
- **`write_astart.py` chunked TCP mode** is the right escape hatch when add_note.py --mode replace fails (bypasses argparse entirely).