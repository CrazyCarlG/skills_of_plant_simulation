# `quirk-006-data-field-ignored` — Quirk #6 — data field is always absent on simtalk_run; return_value:true is a no-op

- **Category**: quirks
- **Type**: `simtalk_run`
- **Tags**: quirk-6, regression
- **Timeout**: 15s
- **Iterations**: 3
- **Wall-time budget** (info-only): 8000ms

## Code

```simtalk
-> integer
return 42
```

## Expected

```json
{
  "exit_code": 0,
  "result_includes": [
    "success"
  ],
  "log_not_starts_with": "code execute failed",
  "wall_time_max_ms": 8000
}
```

## Raw runs

| # | Exit | Wall ms | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|
| 1 | 0 | 405 | pass | `pass` | — | — |
| 2 | 0 | 426 | pass | `pass` | — | — |
| 3 | 0 | 422 | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
{ "type": "simtalk_run", "action_id": "16c09318951047fdaeeff756c9fd41c4", "result": "success", "log": "execute success" }

```

**stderr** (first 500 chars):

```

```
