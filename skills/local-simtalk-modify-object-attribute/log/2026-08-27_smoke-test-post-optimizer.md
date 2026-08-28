# Smoke Test — local-simtalk-modify-object-attribute — 2026-08-27 (post-optimizer)

**Date:** 2026-08-27
**Operator:** skills-optimizer (smoke-test pass after the 2 P0 + 19 P1 + 8 P2 optimization)
**Skill under test:** `skills/local-simtalk-modify-object-attribute/`

## Verdict: **PASS** (`--read-only` mode + `(None)` cosmetic verified)

## Tests

### Test 1: `attr_modify.py --read-only` (cosmetic verification)

```bash
python3 skills/local-simtalk-modify-object-attribute/scripts/attr_modify.py \
    --path .Models.Model.EventController \
    --attr SkipLongEventIntervals \
    --read-only
```

**Output:**
```
=== .Models.Model.EventController.SkipLongEventIntervals (None) ===
  2026-08-27 21:32:22: SkipLongEventIntervals: true
  2026-08-27 21:32:22:
```

✅ PASS — read-only mode works correctly:
1. **Section header shows `(None)` for the type slot** — this is the documented cosmetic per [copy-moa-001] just added to SKILL.md Usage example.
2. **The actual attribute value is read back correctly**: `SkipLongEventIntervals: true`.
3. **No `--type` required** for read-only (correctly relaxed).

### Test 2: Q-moa-001 (enum-masquerade) — partial

The Q13/Q14/Q15 entries cover enum-typed "boolean" attributes (e.g., `.MaterialFlow.FlowControl.EntryBlocking`) that reject `true`/`false` literals. Not safely smoke-testable on `.Models.Model.EventController` (which has real booleans).

### Test 3: Q-moa-002 (transient syntax-error under load) — partial

The Q14 entry covers transient `result: failed` errors when `--read-only` is called three times rapidly. Not reproduced in this single-shot smoke test; covered by prior session logs.

## What this run validated / learned

1. **`--read-only` mode works** — value successfully extracted via print+readlog despite v15+ regression (the value appeared in the readlog response in this run; prior session reported it didn't always).
2. **`(None)` cosmetic verified** in section header — matches the just-added [copy-moa-001] Usage note.
3. **No regressions** from the doc-only [copy-moa-001] change.

## Conclusion

The read-only path works and the cosmetic `(None)` is documented as expected behavior. Write-side ops (which would need a planned restore) are not safe to smoke-test.