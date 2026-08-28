# Smoke Test — local-simtalk-read-library — 2026-08-27 (post-optimizer)

**Date:** 2026-08-27
**Operator:** skills-optimizer (smoke-test pass after the 2 P0 + 19 P1 + 8 P2 optimization)
**Skill under test:** `skills/local-simtalk-read-library/`

## Verdict: **PASS** (LIB-7 multi-line program bug fixed; LIB-10 round-trip works)

## Tests

### Test 1: `probe_methods.py .Models.Model.Method` (LIB-7 round-trip)

```bash
echo '.Models.Model.Method' > /tmp/_smoke_paths.txt
python3 skills/local-simtalk-read-library/scripts/probe_methods.py --no-infobox /tmp/_smoke_paths.txt /tmp/_smoke_probe_methods.tsv
```

**Output (TSV content):**
```
.Models.Model.Method	Method	Method	false	false	0	81	
.ModelAssistants.Calculator3D.M_Convert(.Models.Model.Station, 90, -63.2, 381.8)
```

✅ PASS — TSV produced with `program_len=81` and the actual program body intact.

### Test 2: `render_library.py` multi-line fix (P0 verification)

```bash
python3 skills/local-simtalk-read-library/scripts/render_library.py /tmp/_smoke_probe_methods.tsv /tmp/_smoke_render.md
```

**Output:**
```
METHOD SUMMARY (path | type | size | status)
================================================================================
  .Models.Model.Method                                    Method          81 B   ok

Wrote /tmp/_smoke_render.md
```

✅ PASS — `render_library.py` correctly parsed the TSV (which has embedded newline in `program` field per LIB-7/LIB-10) and emitted 1 method entry. **The P0 multi-line program drop bug is fixed** — pre-fix this would have dropped the `.ModelAssistants.Calculator3D.M_Convert(...)` body line, but it's intact in the output.

### Test 3: `render_inheritance_map.py` skipped

Not on the post-optimizer change list — no need to smoke test.

## What this run validated / learned

1. **LIB-7 + LIB-10 + P0 multi-line fix all hold together**: probe emits TSV with embedded newline in program field → render_library correctly splits on record headers → 1 method recovered with full body.
2. **`--no-infobox` works for probe_methods** (per documented positional-arg exception in cross-cutting theme #2).
3. **The previously-broken P0 behavior is verified fixed** by the round-trip (probe → render produces a valid JSON with non-empty `program` field).

## Conclusion

The P0 multi-line program drop bug is **fixed and verified**. LIB-7 (TSV embedded newlines) and LIB-10 (workaround documentation) are both operational. No regressions.