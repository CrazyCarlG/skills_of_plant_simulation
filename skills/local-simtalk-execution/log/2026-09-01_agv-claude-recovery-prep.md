# Usage log — AGV_Claude recovery prep: read_library shows 7 methods empty, then server JSON layer hung

**Date:** 2026-09-01  **Skill:** `local-simtalk-execution` (sibling: `local-simtalk-read-library`, `local-simtalk-get-folder-tree`)  **Target:** `.AGV_Claude.Pool.{AGV_init, AGV_dispatch, AGV_release, AGV_requestCharge, AGV_dashboard, AGV_batchedRoute, AGV_reset}`
**Mode / Action:** read-library + ping/bfs probe  **Operator:** plant-simulation-expert

## Goal
Continue work from 2026-08-31 (`create-agv-claude-library`). User reports the previous `.AGV_Claude` version "still has issues". Goals:
1. Re-confirm `.AGV_Claude` still exists in current model
2. Read each of the 7 methods' actual program bodies
4. Identify what's broken
5. Rewrite / extend

## Steps
1. Pre-flight TCP probe `host.docker.internal:50007` → `CONNECTED` ✅
2. `bfs_full.py ".AGV_Claude" 4 /tmp/agv_claude_tree.json --no-infobox` → wrote tree (calls=3)
3. `read_library.py --path ".AGV_Claude"` → ran end-to-end; **BFS step + 14 probe batches completed**; produced 98-row TSV
4. **CRITICAL FINDING from read_library output**:
   - `.AGV_Claude.Pool.AGV_init`, `.AGV_Claude.Pool.AGV_dispatch`, `.AGV_Claude.Pool.AGV_release`, `.AGV_Claude.Pool.AGV_requestCharge`, `.AGV_Claude.Pool.AGV_dashboard`, `.AGV_Claude.Pool.AGV_batchedRoute`, `.AGV_Claude.Pool.AGV_reset` — **all 7 show `program_len:0, program:""`** in the rendered library dump
   - Compare: `.SimtalkClaude.src.SimtalkAction.*` methods (same probe, same script) show full program text correctly
   - Therefore the issue is NOT a read_library bug — the 7 methods are genuinely empty in Plant Simulation
5. Direct probe via raw `socket_client.py` of `.AGV_Claude.Pool.AGV_dispatch.program` → **TIMEOUT 10s** (JSON layer hung)
6. `simtalk_send.py ping` → EXIT=1 (timeout)
7. `simtalk_send.py run 'return 1+1'` → EXIT=1 (timeout)
8. `bfs_full.py ".AGV_Claude" 3 /tmp/agv_tree2.json` → JSON decode error (server returned no parseable JSON)
9. TCP-level re-verify → `CONNECTED` ✅ — but **no JSON reply on any subsequent request**
10. **STOP** per Hard Rule #1 (don't retry blindly) + lifelines §6 protocol

## Result
- 7 method bodies are empty in Plant Simulation (last session's `write_simtalk` was a soft-fail despite `[verify] method executes OK after edit` log lines — see 08-31 session notes)
- Server's JSON layer is now unresponsive (TCP accept still works but no reply to ping/readlog/simtalk_run)

## Verdict — BLOCKED + needs user intervention
1. **Restart SimTalkClaude server** — user must reopen `.SimtalkClaude2` Frame in Plant Simulation, re-run `init`/`start` (waits for `Server listening on 50007`), then say "已启动" so I can retry
2. **After restart, my plan**:
   - Read each empty method body (will be empty) and confirm
   - Re-write bodies using the proper per-skill procedure (must read source first per Hard Rule #8, even if empty — empty is a valid prior state, just record it)
   - Apply Open Questions from 08-31 session summary:
     - `AGV_dispatch`: upgrade scoring from `1/(1+d)` to `(1-battery_used)^k * 1/(1+d)` weighted
     - `AGV_batchedRoute`: investigate `Transporter.setRouteSegments(...)` API for true milk-run
     - `AGV_dashboard`: replace `print` with a writeable location (writeToConsole, DataTable row, or writeToFile) since v15+ readlog regression hides `print`
   - Verify with `objexecute` (already proven works per 08-31)
   - Update session summary

## What this run validated / learned
- **Quirk — write_simtalk silent failure mode**: 08-31 session claimed "all 7 methods wrote + verified" but the methods are empty. The `[verify] method executes OK after edit` log line came from a different code path that doesn't actually persist the `program` attribute (likely confused a syntax-check success with a write success). For future write operations, **must readback `o.Program` after write** (not just execute).
- **SimTalkClaude JSON-layer hang** is reachable after a long batch probe (14 batches × 8 paths). The bridge handler probably doesn't release a lock between simtalk_runs. Mitigation: send a tiny `ping` between batches to keep the channel live, or call `.~.~.~.~.~.Server.Reconnect` to bounce the socket. (User has to do this manually today.)
- **probe_methods.py works for methods under Frame-derived parents** (it just lists them in the BFS tree then calls `str_to_obj(path).Program`) — so the "empty program" finding is reliable.