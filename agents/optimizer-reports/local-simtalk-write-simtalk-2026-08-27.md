# Optimizer report — `local-simtalk-write-simtalk` — 2026-08-27

**Date:** 2026-08-27
**Skill under review:** `skills/local-simtalk-write-simtalk/`
**Logs scanned:** 2 (`session-20260826.md` + `2026-08-27_flow-a-replace-and-flow-b-duplicate.md`)
**Operator:** skills-optimizer

## Skill snapshot

- **SKILL.md** Hard rules table declares **16 Quirks** (#1..#16). All skill-specific; cross-references `local-simtalk-execution` Quirk #6/7/13 and `local-simtalk-add-note-to-method` Quirk #10.
- **Last log verdict:** PASS (Flow A + Flow B; 8/9 ops successful — 1 test-author bug in Test 2 step 5).

## Findings

### P0 — Doc errors (blocking)

*None.* Quirk #15 (create-vs-duplicate) is well-documented and verified in `2026-08-27_flow-a-replace-and-flow-b-duplicate.md`.

### P1 — Undocumented Quirks

1. **[q-ws-001]** **SimTalk string literals do NOT backslash-escape inner `"`.** When building SimTalk source via Python string concatenation, un-escaped `"` inside the SimTalk source (i.e. `"hello from..."` inside a Python `"..." + chr(10) + ...` string) will break the Python literal, and using `\"` inside the SimTalk source gets passed through as literal `\"` (since SimTalk doesn't interpret `\` either). Workaround options: avoid inner `"` in the SimTalk source (use `print to_str(...)` only); use SimTalk's `""` doubling (`""hello""` → `"hello"`); or build the inner string via `chr(34) + "hello" + chr(34)`.
   - **Evidence:** `skills/local-simtalk-write-simtalk/log/2026-08-27_flow-a-replace-and-flow-b-duplicate.md` §"What this run validated / learned" lines 198-208 (Test 2 step 5 first attempt with `print "hello..."` failed).
   - **Suggested patch:** `patches/SKILL.md.bp001-addendum.md` — add to Step 6 / Quirk table: "Building SimTalk source from Python: inner `"` in SimTalk source must be `chr(34)` to avoid Python-string-literal corruption."

### P1 — Missing best practice

*None beyond q-ws-001.*

### P2 — Copy / examples / dead links

1. **[copy-ws-001]** SKILL.md "Limitations" header appears **twice** (lines 296-297). Cosmetic duplicate; remove one.

### P3 — Informational

1. The 2026-08-27 log confirms **`.&Method.duplicate(<frame>, <name>)` is the only correct Method-creation path** (Quirk #15) and that the `&` operator is mandatory. Already in Quirk #16 of SKILL.md. No new finding.
2. The session-20260826 log is mostly about Q-15 evolution; older context.

## Verdict

**Actionability score:** 0 P0 / 1 P1 / 1 P2
**Recommended action:** Add the chr(34) inner-quote escape rule to SKILL.md Step 6 / Quirk table; cosmetic dedupe of Limitations header.

## Cross-references

- Related: `local-simtalk-add-note-to-method-2026-08-27.md` (this skill uses `add_note.py --mode replace` which has the readlogic bug — `write-simtalk`'s write path is compromised)
- Related: `local-simtalk-execution-2026-08-27.md` (Quirk #6/7/13)
- Plant Simulation Help: `01-plantsimulation-knowledge/.../Method/` (where the duplicate() vs create() distinction is documented)