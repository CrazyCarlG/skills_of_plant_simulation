# `run-002-arithmetic` — run arithmetic expression

- **Category**: run
- **Type**: `simtalk_run`
- **Tags**: happy-path
- **Timeout**: 15s
- **Iterations**: 3
- **Wall-time budget** (info-only): 8000ms

## Code

```simtalk
print 1+1
```

## Expected

```json
{
  "exit_code": 0,
  "result_includes": [
    "success"
  ],
  "log_not_starts_with": "code execute failed",
  "json_field": {
    "result": "success"
  },
  "wall_time_max_ms": 8000
}
```

## Raw runs

| # | Exit | Wall ms | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|
| 1 | 0 | 433 | pass | `pass` | — | — |
| 2 | 0 | 395 | pass | `pass` | — | — |
| 3 | 0 | 416 | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
{ "type": "simtalk_run", "action_id": "0c4fe9c5a2d844d69385a43e39235ada", "result": "success", "log": "execute success" }

```

**stderr** (first 500 chars):

```

```
