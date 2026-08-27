# Optimizer report — `local-simtalk-execution` — 2026-08-27

**Date:** 2026-08-27
**Skill under review:** `skills/local-simtalk-execution/`
**Logs scanned:** 20 (oldest: 2026-08-24 v1, newest: 2026-08-27 ping-syntax-run-readlog)
**Operator:** skills-optimizer

## Skill snapshot

- **SKILL.md** declares 7 Quirks via `lifelines.md` reference (Quirks #1, #2, #5, #6, #7, #8, #13, plus #9/Q12/v15 readlog regression in §5). **references/lifelines.md** documents 13 explicit Quirks (#1, #2, #3, #4, #5, #6, #7, #8, #9, #10, #11, #12, #13).
- **Hard rules** count: 7 in `lifelines.md` numbered sections + 1 modal-trap section.
- **Last log verdict:** PASS (`2026-08-27_ping-syntax-run-readlog.md` 3/3 clean; `2026-08-27_ping-syntax-run-readlog-2.md` 8/8 with `1/0` compile-time detection case).

## Findings

### P0 — Doc errors (blocking)

*None.* SKILL.md / `lifelines.md` match observed behavior in all 20 logs.

### P1 — Undocumented Quirks

1. **[q-001]** `var x: integer := 1/0` returns **`result:"failed"` + exit 10** at *compile time*, NOT `result:"success"` + `code execute failed` (Quirk #7). Confirmed in `2026-08-27_ping-syntax-run-readlog-2.md` §Steps 6 ("`run '1/0'` exit=10, result=failed — compile-time division-by-zero detection, NOT Quirk #7"). The current `lifelines.md` §6 says **"Quirk #7 is universal"** — the log contradicts this: **Quirk #7 only fires for runtime-detected errors; compile-time errors set `result:"failed"` and exit 10.**

   - **Evidence:** `skills/local-simtalk-execution/log/2026-08-27_ping-syntax-run-readlog-2.md` lines 45-46 + "What this run validated / learned" lines 75-80.
   - **Suggested patch:** add to `patches/lifelines.md.entry-q001.txt`:
     > **Q-001.** `simtalk_run` of code that fails at **compile time** (e.g. literal `1/0`, undeclared identifier in declaration position, mismatched-arity builtin) returns `result:"failed"` (NOT `result:"success"`) and exit code 10. **Quirk #7's soft-failure pattern (`result:"success"` + `log:"code execute failed..."`) only fires for runtime exceptions**, i.e. cases where the compiler can't see the bad value. Always parse the `log` field regardless of `result`.

2. **[q-002]** `class_ops.py` and other write skills report `simtalk_send.py readlog` **exit code 20** (`readlog_unreliable_warning`) on v15+, but `stdout` still carries the log content. Documented in `local-simtalk-class-management/log/session-20260826.md` Part B Bug #2 fix (lines 113-137). `lifelines.md` §5 documents the warning but **does NOT document exit code 20** as a "still-valid" exit.

   - **Evidence:** `skills/local-simtalk-class-management/log/session-20260826.md` lines 113-137 (`if rl_proc.returncode not in (0, 20): envelope["error"] = "readlog_fetch_failed"`).
   - **Suggested patch:** `patches/lifelines.md.entry-q002.txt` — append to §5: "On v15+ server, `simtalk_send.py readlog` exits **20** (`readlog_unreliable_warning`) but stdout still carries the log content. Treat exit 20 as success for readlog extraction."

### P1 — Missing best practice

1. **[bp-001]** `local-simtalk-execution/log/2026-08-27_ping-syntax-run-readlog.md` line 56-63: **"Treat any path starting with `.SimtalkClaude` (with or without trailing digit) as off-limits for writes."** This is now the user-canonical form of the rule (`.SimtalkClaude`, `.SimtalkClaude2`, … all forbidden). SKILL.md says "off-limits by user convention" but does not specify the wildcard form. Recommend lifting the wildcard phrasing into a Hard rule.
   - **Evidence:** `skills/local-simtalk-execution/log/2026-08-27_ping-syntax-run-readlog.md` "What this run validated / learned" lines 56-62.
   - **Suggested patch:** see `patches/SKILL.md.bp001-addendum.md`.

### P2 — Copy / examples / dead links

1. **[copy-001]** `lifelines.md` §6 success criteria row for `readlog` says "v15 不可信" but the table cell only has the icon, not the full warning. Move the v15+ warning into the same cell.

### P3 — Informational

1. The SKILL.md's "When to use" describes a broad trigger set; the new server-build fingerprint `2606.0002` mentioned in `lifelines.md` §5 is the only concrete version pin. If the server is bumped to v17+, the v15 readlog regression may be re-fixed (as v13 briefly did). Future operators should re-test `readlog` behavior on each new build.

## Verdict

**Actionability score:** 0 P0 / 3 P1 / 1 P2
**Recommended action:** Land the Q-001 + Q-002 Quirk additions (P1) immediately — they would have saved the recent class-management session from going through 3 cascading bugs. P2 cosmetic can wait.

## Cross-references

- Related: `local-simtalk-modify-object-atrribute-2026-08-27.md` — reuses Quirk #6/7/13 interpretation
- Related: `local-simtalk-add-note-to-method-2026-08-27.md` — `add_note.py` is readlog-degraded (Quirk #6/§5)
- Related: `local-simtalk-class-management-2026-08-27.md` — confirmed exit-code-20 behavior
- Plant Simulation Help: `01-plantsimulation-knowledge/.../method/attributes/`