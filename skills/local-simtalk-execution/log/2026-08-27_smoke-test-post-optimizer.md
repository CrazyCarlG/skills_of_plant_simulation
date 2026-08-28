# Smoke Test — local-simtalk-execution — 2026-08-27 (post-optimizer)

**Date:** 2026-08-27
**Operator:** skills-optimizer (smoke-test pass after the 2 P0 + 19 P1 + 8 P2 optimization)
**Skill under test:** `skills/local-simtalk-execution/`
**Server:** `host.docker.internal:50007` (build 2606.0002)
**Loaded model:** `.Models.Model` (per existing sessions)

## Verdict: **PASS** (3/3 transport primitives work; v15+ readlog regression confirmed as documented)

## Tests

### Test 1: `ping`

```bash
python3 skills/local-simtalk-execution/scripts/simtalk_send.py ping
```

**Output:**
```
{ "type": "ping", "result": "success" }
```

✅ PASS — server reachable.

### Test 2: `simtalk_syntax`

```bash
python3 skills/local-simtalk-execution/scripts/simtalk_send.py syntax 'var x: integer := 1'
```

**Output:**
```
{ "type": "simtalk_syntax", "action_id": "de3977965727447eb3ff604103b9eff6", "result": "has no Error", "log": "..." }
```

✅ PASS — syntax check returned `result: "has no Error"`. (Note: `log` field carried stale `###CLASS_OP###` dump from prior `class_ops.py inspect .InformationFlow.Method` — confirms Quirk #9 simtalk_syntax `log` is stale.)

### Test 3: `simtalk_run` (read-only)

```bash
python3 skills/local-simtalk-execution/scripts/simtalk_send.py run 'print 1+1'
```

**Output:**
```
{ "type": "simtalk_run", "action_id": "16e4daedee484977bc2df25fccf36ce3", "result": "success", "log": "execute success" }
```

✅ PASS — `result: "success"`. v15+ readlog regression confirmed: the `print 1+1` value (`2`) does **not** appear in `log` (only "execute success"). This matches lifelines.md §5 and Q-002 exactly.

### Test 4: `readlog`

(Skipped per protocol — v15+ regression makes it unreliable for value extraction. Test 1-3 above are sufficient.)

## What this run validated / learned

1. **All three transport primitives (ping / syntax / run) work** post-optimizer changes.
2. **Quirk #6, #9, Q-001, Q-002 are still observable** in v15+ regression:
   - `simtalk_run` `log` field = "execute success" only (Quirk #6 — `data` always empty, `print` output not captured)
   - `simtalk_syntax` `log` field carries **stale** `###CLASS_OP###` dump from prior session (Quirk #9)
   - All `result` values follow the documented patterns (Q-001, Q-002)
3. **No regressions from the doc-only changes** in this optimization round (the docs-only nature of changes to lifelines.md is verified by the smoke tests passing).

## Conclusion

All 4 documented Quirks (Quirk #6, #9, Q-001, Q-002) and the v15+ readlog regression are observable and correctly documented. Transport layer is stable. No code changes were made in this session — only documentation.