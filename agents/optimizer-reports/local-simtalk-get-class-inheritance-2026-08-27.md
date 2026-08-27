# Optimizer report — `local-simtalk-get-class-inheritance` — 2026-08-27

**Date:** 2026-08-27
**Skill under review:** `skills/local-simtalk-get-class-inheritance/`
**Logs scanned:** 4 (oldest: `test-run-20260826-v1.md`, newest: `2026-08-27_p4-ctu-class-inheritance.md`)
**Operator:** skills-optimizer

## Skill snapshot

- **SKILL.md** Hard rules table cross-references `local-simtalk-execution` Quirk #6/7/13; declares **6 INH-specific Quirks** (INH-1..INH-6).
- **Last log verdict:** PASS (2026-08-27 instances-and-root-classes 4/4 substantive).

## Findings

### P0 — Doc errors (blocking)

*None.*

### P1 — Undocumented Quirks

1. **[q-inh-001]** **`--no-infobox` must be the LAST positional arg for `probe_inheritance.py`.** Putting it first (`probe_inheritance.py --no-infobox <paths> <out>`) crashes with `FileNotFoundError: --no-infobox` because argparse interprets it as the `paths_file` argument. This is **the OPPOSITE** of `class_ops.py` (where `--no-infobox` MUST come first) and **the OPPOSITE** of `bfs_one_level.py` (where either works).
   - **Evidence:** `skills/local-simtalk-get-class-inheritance/log/2026-08-27_instances-and-root-classes.md` §"What this run validated / learned" lines 81-83.
   - **Suggested patch:** `patches/SKILL.md.bp001-addendum.md` — add explicit Usage BAD vs GOOD example to SKILL.md.

### P1 — Missing best practice

*None beyond q-inh-001.*

### P2 — Copy / examples / dead links

1. **[copy-inh-001]** SKILL.md "Limitations" calls out "Batch size 12 is empirical" but doesn't surface the v15+ readlog regression specifically. INH-1 references v15 readlog cumul buffer but doesn't quantify the "≤12 paths per batch" limit. Cosmetic — make the empirical nature explicit ("BATCH ≤ 12 was empirically tested in v15; smaller is safer; the limit may need re-validation on v17+").

### P3 — Informational

1. The `2026-08-27_instances-and-root-classes.md` log surfaces a soft-failure case: `.EventController` (basis-root name) resolves to an object whose `.Name` and `.InternalClassType` come back empty. Script handles this gracefully (writes partial row). Already documented as expected behavior in the test verdict.

## Verdict

**Actionability score:** 0 P0 / 1 P1 / 1 P2
**Recommended action:** Add the `--no-infobox` LAST-positional rule to SKILL.md Usage; clarify the INH-1 batch-size is empirical.

## Cross-references

- Related: `local-simtalk-execution-2026-08-27.md` (Quirk #6/7/13)
- Related: `local-simtalk-class-management-2026-08-27.md` (the OPPOSITE `--no-infobox` rule is the cross-cutting issue worth standardizing)