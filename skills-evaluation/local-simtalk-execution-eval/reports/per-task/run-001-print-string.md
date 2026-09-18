# `run-001-print-string` — run print() of a string literal

- **Category**: run
- **Type**: `simtalk_run`
- **Tags**: happy-path
- **Timeout**: 15s
- **Iterations**: 3
- **Wall-time budget** (info-only): 8000ms

## Code

```simtalk
print("hello from SimTalk")
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
| 1 | 0 | 414 | pass | `pass` | — | — |
| 2 | 0 | 468 | pass | `pass` | — | — |
| 3 | 0 | 447 | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
{ "type": "simtalk_run", "action_id": "bdf5bef06811459c824e7f2d170646da", "result": "success", "log": "execute success" }

```

**stderr** (first 500 chars):

```

```
