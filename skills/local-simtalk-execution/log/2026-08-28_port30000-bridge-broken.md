# Usage log — port-30000 bridge returns "Unknown identifier 'hasSyntaxError'"

**Date:** 2026-08-28  **Skill:** `local-simtalk-execution`  **Target:** host.docker.internal:30000 (old Plant Simulation, new SimtalkClaude bridge)
**Mode / Action:** simtalk_run / simtalk_syntax / readlog probes  **Operator:** plant-simulation-expert

## Goal
User request: "我新打开了另外一个plant simulation，监听30000端口，这是老版本的plant simulation，我在里面新创建了simtalkclaude，适配老版本的plant simulation,请测试下所有技能是否正常使用"
→ Test all 9 skills against the new server on port 30000.

## Steps
1. Pre-flight TCP probe port 30000 — CONNECTED.
2. Patched test copies into `/tmp/skills_patched/` (source files untouched) with `--port 30000` injected via `sed`.
3. Ran raw `simtalk_run` via socket_client.py → every call returns `log="Unknown identifier 'hasSyntaxError'"`.
4. Ran raw `simtalk_syntax` → same error.
5. Ran raw `readlog` → returns a stale cached `"copyFile"` error from prior session, not the new print output.
6. ping → works.
7. probe_methods.py / probe_inheritance.py on port 30000 → return empty rows (readlog stale).
8. Same `print "hello"` payload on port 50007 (newer bridge) → `result=success` (sanity check).
9. `bfs_one_level.py` returned valid JSON earlier in the session, but inspection shows its main `run`/`readlog` calls do NOT pass `--port 30000` — they hit default port 50007. So the bfs "success" was NOT port-30000 success.

## Result
**Bridge on port 30000 is fundamentally broken.** Every `simtalk_run` and `simtalk_syntax` payload returns:
```json
{ "type": "simtalk_run", "result": "", "log": "Unknown identifier 'hasSyntaxError'" }
```
The new SimtalkClaude bridge was adapted for the old Plant Simulation API, but its Method-frame still references `Method.hasSyntaxError(errMsg, errLine)` — a Method class method that does not exist in old PS. The compile of the bridge itself fails before user code is ever executed.

`readlog` returns a cached "copyFile" error from an unrelated prior operation; it does not contain new print output.

## Verdict — FAIL
All 9 skills are functionally broken on port 30000 because they all depend on `simtalk_run` (which the bridge cannot execute).

## What this run validated / learned

### Root cause
The new SimtalkClaude bridge code uses `Method.hasSyntaxError()` — see e.g.:
```simtalk
var hasError := &simtalkcode.hasSyntaxError(errMsg, errLine)
```
`hasSyntaxError` is a Method class method introduced in newer Plant Simulation (v15+). Old Plant Simulation lacks this method → bridge itself fails to compile → every `simtalk_run` returns the "Unknown identifier" error and the user code never runs.

References documenting the pattern:
- `02-simulation-file-experience/02-bridge-tool/simtalkclaude-v1-and-v2.md` — describes `hasSyntaxError` usage
- `02-simulation-file-experience/03-workflow-playbook/skill-call-playbook.md` — "hasSyntaxError must be on &Method"
- `01-plantsimulation-knowledge/.../simtalkclaude_raw.tsv` — raw v1 source using `hasSyntaxError`

### Skills tested, all broken on port 30000
| # | Skill | Symptom |
|---|---|---|
| 1 | local-simtalk-execution | ping ✅, simtalk_syntax ❌, simtalk_run ❌, readlog ❌ (stale) |
| 2 | local-simtalk-get-folder-tree | bfs_one_level hit default port 50007 — works only because port 50007 is alive in the environment. NOT a port-30000 success. |
| 3 | local-simtalk-get-class-inheritance | probe_inheritance → 0 rows (readlog stale, simtalk_run fails) |
| 4 | local-simtalk-read-library | probe_methods → 1 row with all empty fields (no print capture) |
| 5 | local-simtalk-write-simtalk | would send simtalk_run → fails immediately |
| 6 | local-simtalk-add-note-to-method | would send simtalk_run → fails immediately |
| 7 | local-simtalk-modify-object-attribute | tested with `--read-only` → "EXEC FAIL: ... Unknown identifier 'hasSyntaxError'" |
| 8 | local-simtalk-class-management | would send simtalk_run → fails immediately |
| 9 | local-simtalk-os-functions | reference-only, no scripts; depends on local-simtalk-execution → same failure |

### Why bfs_one_level "appeared" to work
The `bfs_one_level.py` script's `_run_simtalk` helper passes `--port 30000` correctly, but the main flow's `subprocess.run([sys.executable, SIMTALK_SEND, "--timeout", "15", "run", code])` (line 109) and the corresponding readlog call (line 116) do NOT pass `--port`. They hit default port 50007. So the JSON output the user saw earlier in this conversation was the working 50007 bridge, not the broken 30000 bridge.

This is a real bug in `bfs_one_level.py` (and likely all skill scripts that use `simtalk_send.py` without explicit `--port`) — when the user wants to target a non-default server, the main flow silently falls back to port 50007.

### Fix path
Two options for the user:
- **Option A**: Edit the new SimtalkClaude bridge to NOT call `Method.hasSyntaxError`. Use a try/catch via `try ... exception` and assume hasError=false, then attempt compile directly via `compile()`/`execute()` — or use `_compile_check` only as a hint.
- **Option B**: Upgrade Plant Simulation to a version that ships `Method.hasSyntaxError` (v15+).
Until one of those is done, no skill can run user SimTalk on port 30000.

### What `ping` proves
`{ "type": "ping", "result": "success" }` — TCP connectivity + bridge handshake OK. The failure is downstream of handshake, in the bridge's own compile.