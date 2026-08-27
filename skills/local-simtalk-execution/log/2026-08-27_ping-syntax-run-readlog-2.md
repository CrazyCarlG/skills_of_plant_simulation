# Usage log — local-simtalk-execution: ping + simtalk_syntax + simtalk_run (low-level socket_client)

**Date:** 2026-08-27
**Skill:** `local-simtalk-execution`
**Target:** Plant Simulation server at `host.docker.internal:50007`
**Mode / Action:** ping / simtalk_syntax / simtalk_run (raw `socket_client.py`, no `simtalk_send.py` wrapper)
**Operator:** plant-simulation-expert (OpenClaude subagent)

## Goal

Verify the raw TCP transport layer is alive, the JSON protocol round-trips end-to-end,
and the three core request types (`ping`, `simtalk_syntax`, `simtalk_run`) all behave
per `references/lifelines.md` §6 (success criteria) before delegating to higher-level skills.

## Steps

1. **TCP socket preflight** (Python, no Plant Simulation payload):
   ```bash
   python3 -c "import socket; s=socket.socket(); s.settimeout(3); \
     s.connect(('host.docker.internal',50007)); print('TCP connect OK'); s.close()"
   ```
   → `TCP connect OK`.

2. **`ping`** — minimal connectivity probe:
   - Payload: `{"type":"ping","timestamp":"20260827090000"}||END||`
   - Reply: `{ "type": "ping", "result": "success" }`
   - Verdict: PASS — `type` echoes the request type (Quirk #1).

3. **`simtalk_syntax`** — compile-check of `print(1+1)`:
   - Payload: `{"type":"simtalk_syntax","action_id":"sx-test-1","simtalk_code":"print(1+1)"}||END||`
   - Reply: `result == "has no Error"` → PASS (Quirk #6 path: success iff `"hasError" not in result`).
   - Server-side `log` field contains **stale data** from a prior `bfs_one_level.py` probe
     against `.SimtalkClaude2.Objects` (full JSON dump with `###BFS_MARKER###` header).
     This matches Quirk #9 — `simtalk_syntax` `log` is unreliable, only read `result`.

4. **`simtalk_run`** — actual execution of `print(42)`:
   - Payload: `{"type":"simtalk_run","action_id":"sr-test-1","simtalk_code":"print(42)"}||END||`
   - Reply: `result == "success"` AND `log == "execute success"` → PASS (Quirk #7 double-check).
   - `data` field absent (Quirk #6 — server is `-> void`, never echoes `print` values).

## Result

| # | Type | Result | Log | Verdict |
|---|---|---|---|---|
| 1 | `ping` | `success` | n/a | PASS |
| 2 | `simtalk_syntax` | `has no Error` | stale BFS JSON | PASS (rely on `result`) |
| 3 | `simtalk_run` | `success` | `execute success` | PASS |

TCP + JSON protocol round-trip is healthy.

## Verdict

PASS — 3/3 calls clean. Plant Simulation server is ready for downstream skill testing.

## What this run validated / learned

- **Server model namespace observation.** The `log` field of the `simtalk_syntax` call
  surfaced a previous `bfs_one_level.py` probe against `.SimtalkClaude2.Objects` —
  an 8-child Folder containing `Method`/`Socket`/`DataList`/`Dialog`/`HtmlReport`/
  `Variable`/`Button`/`DataTable`. This is **not** the legacy `.SimtalkClaude.*` namespace
  the agent's hard rules forbid, but the two are easy to confuse. **Treat any path
  starting with `.SimtalkClaude` (with or without trailing digit) as off-limits for writes.**
- **`simtalk_syntax` `log` is genuinely stale** — the JSON we received contained a
  full sibling-folder dump from a different code path. Stick to the Quirk #6 contract:
  only read `result`, ignore `log` on `simtalk_syntax`.
- All three primary request types round-trip cleanly under the
  `--resp-mode delimiter --resp-delimiter '||END||'` framing — no need to retune.
- This run used the **raw `socket_client.py`** rather than the higher-level `simtalk_send.py`
  wrapper. Both work; raw mode is what the other skills' scripts (`bfs_one_level.py`,
  `probe_inheritance.py`, `probe_methods.py`) use internally to avoid shell escaping
  the SimTalk payloads (lifelines §A2 / LIB-1 / INH-3).
