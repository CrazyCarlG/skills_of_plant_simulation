# `quirk-005-retsult-stale` — Quirk #5 — retsult field is always stale; runner must pass on result (not retsult)

- **Category**: quirks
- **Type**: `simtalk_syntax`
- **Tags**: quirk-5, regression
- **Timeout**: 10s
- **Iterations**: 3
- **Wall-time budget** (info-only): 3000ms

## Code

```simtalk
var x: integer := 1
```

## Expected

```json
{
  "exit_code": 0,
  "result_includes": [
    "has no Error"
  ],
  "result_excludes": [
    "hasError"
  ],
  "wall_time_max_ms": 3000
}
```

## Raw runs

| # | Exit | Wall ms | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|
| 1 | 0 | 404 | pass | `pass` | — | — |
| 2 | 0 | 397 | pass | `pass` | — | — |
| 3 | 0 | 384 | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
{ "type": "simtalk_syntax", "action_id": "678980ca08674229bb5f21219c753c4d", "result": "has no Error", "log": "" }

```

**stderr** (first 500 chars):

```

```
