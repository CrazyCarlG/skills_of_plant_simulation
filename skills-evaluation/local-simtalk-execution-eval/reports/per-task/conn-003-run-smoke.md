# `conn-003-run-smoke` — simtalk_run smoke (print literal)

- **Category**: connection
- **Type**: `simtalk_run`
- **Tags**: smoke, happy-path, lifelines-§6
- **Timeout**: 15s
- **Iterations**: 3
- **Wall-time budget** (info-only): 5000ms

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
  "wall_time_max_ms": 5000
}
```

## Raw runs

| # | Exit | Wall ms | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|
| 1 | 0 | 451 | pass | `pass` | — | — |
| 2 | 0 | 418 | pass | `pass` | — | — |
| 3 | 0 | 427 | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
{ "type": "simtalk_run", "action_id": "00709f3c91f548f9af694178b3e276a1", "result": "success", "log": "execute success" }

```

**stderr** (first 500 chars):

```

```
