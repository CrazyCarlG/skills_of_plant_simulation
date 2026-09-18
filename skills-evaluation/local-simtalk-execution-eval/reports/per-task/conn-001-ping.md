# `conn-001-ping` — ping a healthy server

- **Category**: connection
- **Type**: `ping`
- **Tags**: smoke, happy-path, lifelines-§6
- **Timeout**: 5s
- **Iterations**: 3
- **Wall-time budget** (info-only): 2000ms

## Code

```simtalk
_(none)_
```

## Expected

```json
{
  "exit_code": 0,
  "result_includes": [
    "success"
  ],
  "result_excludes": [
    "hasError"
  ],
  "json_field": {
    "type": "ping",
    "result": "success"
  },
  "wall_time_max_ms": 2000
}
```

## Raw runs

| # | Exit | Wall ms | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|
| 1 | 0 | 413 | pass | `pass` | — | — |
| 2 | 0 | 415 | pass | `pass` | — | — |
| 3 | 0 | 409 | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
{ "type": "ping", "result": "success" }

```

**stderr** (first 500 chars):

```

```
