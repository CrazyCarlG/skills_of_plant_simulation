# Optimizer report — `local-simtalk-modify-object-atrribute` — 2026-08-27

**Date:** 2026-08-27
**Skill under review:** `skills/local-simtalk-modify-object-atrribute/`
**Logs scanned:** 2 (`SUMMARY.md` covering 2 sessions / 2026-08-26 + 2026-08-27, plus `2026-08-27_eventcontroller-batch-and-boolean.md`)
**Operator:** skills-optimizer

## Skill snapshot

- **SKILL.md** Hard rules table cross-references Quirk #6 / #7 / #13 from `local-simtalk-execution/lifelines.md`.
- **references/quirks.md** declares 12 Quirks (Q1..Q12), all skill-specific.
- **Hard rules** count: 8 in SKILL.md "Hard rules" table + 12 in quirks.md.
- **Last log verdict:** PASS (2026-08-27 eventcontroller 4/4 clean).

## Findings

### P0 — Doc errors (blocking)

*None.* The 2026-08-27 test passed cleanly; the older 2026-08-26 SUMMARY documents **two real bugs in `scripts/attr_modify.py` that have already been fixed in-session** ("Bugs found and fixed in this session"). Per 铁律❺ these are **fixed** and noted in the SUMMARY but **not** propagated to `references/quirks.md`.

### P1 — Undocumented Quirks

1. **[q-moa-001]** **Enum-typed "boolean" attributes masquerade as boolean in the docs.** `.MaterialFlow.FlowControl.EntryBlocking` is documented as `boolean` but Plant Simulation rejects `true`/`false` literals with `"Invalid blocking behavior"`. The actual type is an enum requiring a specific string value (likely `"blocking"` / `"non_blocking"`).
   - **Evidence:** `skills/local-simtalk-modify-object-atrribute/log/SUMMARY.md` Round 2 §Findings line 105-112 (the `2026-08-26` round 2 session).
   - **Suggested patch:** `patches/quirks.md.entry-q001.txt` — append a Q13 entry mirroring the existing Q1..Q12 format.

2. **[q-moa-002]** **Transient syntax-error under load.** When `--read-only` is called three times in quick succession in a shell loop, the first or second call may return `result='failed'` with `Syntax error near line N at '<type>'`, even though the generated SimTalk contains no such literal. Spacing probes with `sleep 1` clears it. Likely cause: readlog flush from previous write collides with next request.
   - **Evidence:** `skills/local-simtalk-modify-object-atrribute/log/SUMMARY.md` Round 1 "Quirks observed" lines 46-55.
   - **Suggested patch:** `patches/quirks.md.entry-q002.txt` — append Q14 entry.

### P1 — Missing best practice

1. **[bp-moa-001]** `"--type per-attribute is mandatory even with --batch"` — The 2026-08-27 EventController test (`--batch RealtimeScale=5:real RandomNumbersVariant=7:integer`) **explicitly learned** this. SKILL.md "Usage" example does include `:type` suffix in `--batch` but does not call it mandatory; `--type` is only listed in the "single-attribute" form.
   - **Evidence:** `skills/local-simtalk-modify-object-atrribute/log/2026-08-27_eventcontroller-batch-and-boolean.md` "What this run validated / learned" lines 119-126.
   - **Suggested patch:** `patches/SKILL.md.bp001-addendum.md`.

### P2 — Copy / examples / dead links

1. **[copy-moa-001]** SKILL.md `(None)` cosmetic note. The 2026-08-27 log notes "the script's per-attribute section header shows `(type)` as `None` for read-only mode (line `=== ... (None) ===`) — cosmetic; can be ignored." Either fix the cosmetic (read-only emits `---` instead of `None`) or document it as expected behavior in the Usage example.

### P3 — Informational

1. The 2026-08-26 SUMMARY's Round 1 already enumerated MaterialFlow classes (`Buffer / Source / Drain / Conveyor / Station`); Round 2 added (`Connector / Sorter / Store / ParallelStation / Track / FlowControl / Cycle / ShiftCalendar / WorkerPool / Variable`). Note `WorkerPool` rejected all three documented attrs — class-library entry vs instance distinction may need a future skill test.

## Verdict

**Actionability score:** 0 P0 / 3 P1 / 1 P2
**Recommended action:** Add the two new quirks (Q13 enum-masquerade, Q14 transient-syntax-under-load) to `references/quirks.md`; lift `--type` mandatory note into SKILL.md Usage. The previously-fixed bugs (line 31-42 of SUMMARY.md) are **already in code** but **not** in the quirk registry — recommend a brief Q1-history note in `quirks.md` for traceability.

## Cross-references

- Related: `local-simtalk-execution-2026-08-27.md` (Quirk #6/7/13 are the foundation)
- Related: `local-simtalk-class-management-2026-08-27.md` (similar write-side dispatcher pattern)
- Plant Simulation Help: `01-plantsimulation-knowledge/.../FlowControl/` (likely the authoritative enum spec)