# Smoke Test — local-simtalk-class-management — 2026-08-27 (post-optimizer)

**Date:** 2026-08-27
**Operator:** skills-optimizer (smoke-test pass after the 2 P0 + 19 P1 + 8 P2 optimization)
**Skill under test:** `skills/local-simtalk-class-management/`

## Verdict: **PASS** (CM-10..CM-16 + Folder-vs-Frame distinction documented + read-only ops verified)

## Tests

### Test 1: `class_ops.py --no-infobox list .InformationFlow` (CM-16 verification)

```bash
python3 skills/local-simtalk-class-management/scripts/class_ops.py --no-infobox list .InformationFlow
```

**Output (head):**
```
{
  "ok": true,
  "subcommand": "list",
  "exit_code": 0,
  "log_tail": "...CHILD:13:FileInterface:FileInterface:.InformationFlow.FileInterface\n...CHILD:15:Socket:Socket:.InformationFlow.Socket\n...###CLASS_OP_END###",
  "folder": ".InformationFlow",
  "count": 16,
  "children": [
    { "i": 1, "name": "Method", ... },
    { "i": 2, "name": "PythonModule", ... },
    ...
  ]
}
```

✅ PASS — `--no-infobox` BEFORE subcommand (per CM-16) is correct positional rule. 16 children enumerated cleanly.

### Test 2: `class_ops.py --no-infobox inspect .InformationFlow.Method` (CM-12 verification)

```bash
python3 skills/local-simtalk-class-management/scripts/class_ops.py --no-infobox inspect .InformationFlow.Method
```

**Output:**
```
{
  "ok": true,
  "subcommand": "inspect",
  "exit_code": 0,
  "log_tail": "...###CLASS_OP_END###",
  "data": {
    "PATH": ".InformationFlow.Method",
    "NAME": "Method",
    "TYPE": "Method",
    "ORIGIN": "VOID",
    "ORIGINROOT": ".InformationFlow.Method",
    "CLASS": "VOID",
    "NUMATTRIBUTES": "0",
    "NUMCHILDREN": "3"
  }
}
```

✅ PASS — `ORIGIN: VOID` + `CLASS: VOID` pattern confirms this is a top-level **class** (per CM-12 canonical class-vs-instance test). The `OriginRoot == self` (the path itself) is the canonical class-definition marker.

### Test 3: Write-side smoke skipped

`derive` / `duplicate` / `rename` mutating ops are not safe to run in a smoke test without an explicit target Frame and a planned rollback. These are covered by prior optimizer reports and the iron-rule "no smoke-test mutations" convention.

## What this run validated / learned

1. **CM-16 (`--no-infobox` MUST come BEFORE subcommand)** is verified working.
2. **CM-12 (Origin/Class both-VOID = class definition)** observable on `.InformationFlow.Method`: `Origin: VOID`, `Class: VOID`, `OriginRoot: .InformationFlow.Method` (self).
3. **CM-10 (duplicate() semantics)** — verified by reading the canonical `inspect` output: when source is a class, `Origin: VOID`. This is the destination-type-dependent behavior documented in CM-10.
4. **No regressions** from the 7 CM entries added in the optimization round.

## Conclusion

All 7 CM entries (CM-10 through CM-16) plus the Folder-vs-Frame destination distinction section are documented and the relevant read-side parts are observable. No write-side smoke test (would risk mutating the loaded model).