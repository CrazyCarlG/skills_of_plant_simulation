# Optimizer report — `local-simtalk-read-library` — 2026-08-27

**Date:** 2026-08-27
**Skill under review:** `skills/local-simtalk-read-library/`
**Logs scanned:** 5 (oldest: `test-session-20260826-v1.md`, newest: `2026-08-27_learn-assembly-model-bottleneckAnalyzer-energyAnalyzer.md`)
**Operator:** skills-optimizer

## Skill snapshot

- **SKILL.md** Hard rules table cross-references `local-simtalk-execution` Quirk #6/7/13; declares **6 LIB-specific Quirks** (LIB-1..LIB-6).
- **Last log verdict:** **PASS for source capture; FAIL for renderer bug** (multi-line program drop in `render_library.py`).

## Findings

### P0 — Real defect discovered

1. **[bug-rl-001]** **`render_library.py` line 32-35 STILL drops multi-line programs.** `program_len` field is correct but `program` field only contains the leading comment line. Root cause: `probe_methods.py` writes the program body with REAL newlines, but `render_library.py` parses with `for ln in f: ln.split("\t")` which treats each line as a separate row. Continuation lines lack the 8-field header so the program body is lost on every multi-line method.
   - **Evidence:** `skills/local-simtalk-read-library/log/2026-08-27_learn-assembly-model-palletOptimization-workerChart.md` lines 34-46 + lines 159-172 (the documented "Renderer bug discovered" section explicitly recommends (a) sentinel substitution OR (b) CSV-style quoting, and says **"do NOT fix in-session"**).
   - **Re-confirmed in:** `skills/local-simtalk-read-library/log/2026-08-27_learn-assembly-model-bottleneckAnalyzer-energyAnalyzer.md` lines 206-212 (the "Renderer bug discovered (recap)" section).
   - **Severity:** P0 — every Method with >1 line of code loses all but its first line in `library_dump.json`. Affects ALL real Methods.
   - **Workaround (verified working):** custom multi-line TSV re-parser at `/tmp/learning_library_full.json` / `/tmp/analyzer_all_25.json` (see logs).
   - **Suggested fix (NOT in scope per 铁律❶):** (a) have `probe_methods.py` replace `\n` with sentinel before writing TSV and renderer reverse; OR (b) quote-enclose the program field with CSV-style parser.

### P0 — Doc errors (blocking)

*None for SKILL.md / references/.* The bug is in script, not doc.

### P1 — Undocumented Quirks

1. **[q-rl-001]** **LIB-7: Batched readlog degrades after ~17 methods in v15+.** `probe_methods.py` batch-8 works for the first ~17 methods, then readlog returns empty metadata (cumulative buffer or feedback-loop regression). Re-probing single-method via `simtalk_send.py run` + readlog extraction is the reliable fallback.
   - **Evidence:** `skills/local-simtalk-read-library/log/2026-08-27_learn-assembly-model-bottleneckAnalyzer-energyAnalyzer.md` lines 22-43 ("Probe via `probe_methods.py` (batches of 8 — 4 batches for 25): 17/25 captured cleanly; 8 EnergyAnalyzer methods returned empty").
   - **Suggested patch:** `patches/SKILL.md.bp001-addendum.md` — add LIB-7 to SKILL.md quirks table with the empirical batch-size note.

### P1 — Missing best practice

*None beyond q-rl-001.*

### P2 — Copy / examples / dead links

*None.*

### P3 — Informational

1. The `2026-08-27_p4-ctu-dump.md` log uses **BATCH=1 + sleep 1.2** for 86 methods — successfully captured all. This is the recommended pattern for batched `probe_methods.py` runs in v15+. (Already reflected in LIB-2's "Batch ≤ 8 Methods per `simtalk_run`" guidance; the `BATCH=1` extreme is the safest workaround.)

## Verdict

**Actionability score:** 1 P0 / 1 P1 / 0 P2
**Recommended action:**
- **LAND P0 #1 NOW**: `render_library.py` multi-line drop is silent — affects every real Method. Per 铁律❶ this is reported only.
- Land P1 LIB-7 with the empirical batch-size note; this is documentation only.

## Cross-references

- Related: `local-simtalk-add-note-to-method-2026-08-27.md` (the working `probe_methods.py` is the recommended workaround for `add_note.py`'s readlogic bug)
- Related: `local-simtalk-execution-2026-08-27.md` (Quirk #6 / §5 readlog regression is the root cause of LIB-7)
- Plant Simulation Help: `01-plantsimulation-knowledge/.../Method/attributes/Program/`