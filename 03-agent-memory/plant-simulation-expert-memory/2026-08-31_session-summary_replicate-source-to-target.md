# Session Summary — Replicate source 50007 model onto target 50010

**Date:** 2026-08-31  **Agent:** plant-simulation-expert
**Skills called:** `local-simtalk-execution` (raw socket), `local-simtalk-get-folder-tree` (bfs_full.py — via PATH leak), ad-hoc diagnostic scripts

## Critical findings (must report to user before proceeding)

### 1. Target 50010 is genuinely minimal, not a hidden twin
- Live `str_to_obj` probe + error-driven check confirms:
  - `.` `.MaterialFlow` `.InformationFlow` `.UserInterface` `.SimtalkClaude` → EXISTS (built-ins + bridge)
  - `.Models.internal.*` → **VOID** (ModelAssistants plugin NOT loaded on target)
  - `.Models.SourceTrigger.*` → **VOID** (5 teaching Frames NOT present)
  - `.Models.Animation3D.*` → **VOID** (3D Frame NOT present)
  - `.Models.SimtalkClaude2` → **VOID**
- Confirms user statement "50010开了一个空白的模型" — the user's premise was correct.

### 2. **`bfs_full.py` always scans port 50007 regardless of intent**
- Script hardcodes `HOST=50007` via `simtalk_send.py` invocation. No `--host/--port` flags.
- Side effect: earlier `data/target/tree.json` was produced by hitting SOURCE (both files md5-identical). All prior structural diffing was meaningless.
- Fix needed before any re-run: either patch `bfs_full.py` to read `SIMTALK_HOST/PORT` env vars, or pass `--host/--port` through to `simtalk_send.py`.

### 3. **Target 50010 readlog buffer is broken / frozen**
- Symptom: `print "X"` on target → simtalk_run returns `execute success`, but `readlog` returns a fixed 715-char slice ending mid-line. New prints do NOT appear in subsequent readlogs.
- Source 50007 has working readlog echo (prints visible in `log` field).
- Both bridges report same Plant Simulation version (2606.0002). The difference is the **SimtalkClaude bridge build** on each Plant Simulation instance.
- **Workaround**: state readback on target must be via simtalk_run error messages (which DO come back), not via readlog.

### 4. Source tree (data/source/tree.json, 213 nodes) is the only reliable map
- Source has 62 Methods, 17 DataTables, 12 Folders, 12 Frames, 11 Variables, 7 EventControllers, plus ~30 MaterialFlow instances.
- Three skip-list categories: `.SimtalkClaude.*` (bridge, MUST NOT replicate), `.MaterialFlow/.InformationFlow/.UserInterface` (built-ins), `.SimtalkClaude2.*` (different bridge — replicate if source has it).

### 5. Write-side skills cannot target port 50010 out-of-the-box
- `write_simtalk.py` and `add_note.py` invoke `simtalk_send` without `--host/--port`, so they default to source (50007).
- To write to target, must wrap calls in `SIMTALK_HOST/PORT` env or `--host/--port` plumbing — not currently wired.

## Open questions / next steps (need user decision)

Three viable strategies:
- **A) Full structural replication via skills** (~30-60 min, 100+ TCP ops, no read-back verification on target).
- **B) `loadModel(<source_path>)` on target** — but no source `.spp` file accessible from container (`find / -name '*.spp'` only found knowledge-base models, not the running source).
- **C) Fix target's bridge first** — user inspects why readlog is stuck; once fixed, all read-side skills work normally.
- **D) Hybrid + scripted** — script-write the source → target replication using SOURCE as truth (BFS + probe work) and TARGET as sink (write skills + error-driven verification). Most defensible given current constraints.

Awaiting user direction on which path to take.