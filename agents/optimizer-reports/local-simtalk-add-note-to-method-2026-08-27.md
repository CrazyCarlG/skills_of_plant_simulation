# Optimizer report — `local-simtalk-add-note-to-method` — 2026-08-27

**Date:** 2026-08-27
**Skill under review:** `skills/local-simtalk-add-note-to-method/`
**Logs scanned:** 6 (oldest: 2026-08-26 `m_paramRack_annotation`, newest: 2026-08-27 `readlogic-readlog-pollutes-backup`)
**Operator:** skills-optimizer

## Skill snapshot

- **SKILL.md** Hard rules table declares 13 Quirks (#1..#13).
- **references/quirks.md** declares 11 Quirks (Q1..Q11) — **drift from SKILL.md** (SKILL.md has #12, #13 that aren't in quirks.md).
- **Last log verdict:** **FAIL** on `add_note.py` (real defect); PASS on raw `socket_client.py` workaround.

## Findings

### P0 — Doc errors (blocking)

1. **[doc-anno-001]** **Quirk numbering drift between SKILL.md and quirks.md.** SKILL.md §"Hard rules (Quirks)" table has **13 entries** (#1..#13) including #12 (`simtalk_hasError` returns string) and #13 (single `obj.program :=` payload ≤ ~2 KB). `references/quirks.md` only has **Q1..Q11** — Q12 and Q13 are not in the references file.
   - **Evidence:** SKILL.md lines 222-237 (Hard rules table #1..#13) vs `references/quirks.md` lines 1-274 (Q1..Q11 only).
   - **Suggested patch:** `patches/quirks.md.entry-q12-q13.txt` — append Q12 + Q13 entries mirroring the table cells in SKILL.md.

### P0 — Real defect discovered in 2026-08-27 log

2. **[bug-anno-001]** **`add_note.py` has a real exploitable bug.** The script calls `readlog()` to capture `print obj.program` output, instead of trusting the `simtalk_run` reply directly. Consequences: (a) every "read" pulls in stale content from earlier test runs; (b) the on-disk backup is the polluted readback; (c) subsequent `prepend`/`append`/`replace` builds new program on top of polluted source; (d) `--restore` is broken because backup is corrupt.
   - **Evidence:** `skills/local-simtalk-add-note-to-method/log/2026-08-27_readlogic-readlog-pollutes-backup.md` §"What went wrong" lines 71-102 + verification lines 137-189.
   - **Impact:** at least two on-disk backups have already been corrupted (`.bak-stale` proves it).
   - **Workaround (verified working):** raw `socket_client.py` `obj.program := <src-string>` pattern using `chr(10)` joins + `chr(8212)` for em-dash; documented in the log lines 104-118.
   - **Suggested fix (NOT in scope per 铁律❶ — for verification/user):** rewrite `add_note.py` to send the read as part of the same `simtalk_run` request and parse `log` field of that one response, OR use `local-simtalk-read-library`'s `probe_methods.py` (which uses `&o.Program` as direct attribute access) as a library call for the read step.
   - **Severity:** P0 — the helper script is unsafe to use; backups are corrupted silently; user has already lost data once (see `.bak-stale` evidence).

### P1 — Undocumented Quirks

1. **[q-anno-001]** **Single `obj.program :=` payload cap of ~2 KB** is documented in SKILL.md (#13) but **not** in `references/quirks.md`. Server-side JSON parser truncates payloads > ~2 KB and returns `Error in line 1: Unexpected end of string`. 5 retries don't recover (this is **not** transient). For long NOTE blocks, split into chunks of 25-30 lines each (~1.5-2 KB payload), first chunk via `obj.program := chunk_1`, subsequent chunks via `obj.program := obj.program + chr(10) + chunk_N`. The original body is appended as the last chunk the same way.
   - **Evidence:** SKILL.md line 237; cross-referenced in 2026-08-27 log but no separate log evidences the 2 KB limit (latent).
   - **Suggested patch:** already in SKILL.md; just promote to `references/quirks.md`.

2. **[q-anno-002]** **`simtalk_hasError(<source>)` returns a `string`** (not `boolean`). SKILL.md #12 documents this; `references/quirks.md` doesn't.
   - **Evidence:** SKILL.md line 236; no dedicated log evidence (latent).
   - **Suggested patch:** add Q12 entry mirroring SKILL.md #12.

### P2 — Copy / examples / dead links

*None.*

### P3 — Informational

1. The `2026-08-26_simtalkclaude2_annotation.md` log uses a more sophisticated strategy (avoiding `"` and `||END||` in header text via `encode_for_simtalk()`) than `add_note.py` — the annotation script `/tmp/annotate3.py` was hand-rolled. Recommend capturing that strategy in a future patch.

## Verdict

**Actionability score:** 2 P0 / 2 P1 / 0 P2
**Recommended action:**
- **LAND P0 #2 NOW**: `add_note.py` readlogic is unsafe; do not use until fixed. (Per 铁律❶ this is reported only, not patched; user/verification must approve.)
- **LAND P0 #1 NOW**: fix Quirk numbering drift (just `references/quirks.md` needs Q12 + Q13 added; cosmetic).
- P1: trivial, land with P0 #1.

## Cross-references

- Related: `local-simtalk-execution-2026-08-27.md` (Quirk #6 / §5 readlog regression is the root cause of `add_note.py`'s bug)
- Related: `local-simtalk-read-library-2026-08-27.md` (`probe_methods.py` is the recommended workaround — same `&o.Program` access pattern bypasses readlog)
- Related: `local-simtalk-write-simtalk-2026-08-27.md` (this skill uses `add_note.py --mode replace --confirm` so it inherits the bug)