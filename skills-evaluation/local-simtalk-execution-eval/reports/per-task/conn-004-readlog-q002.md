# `conn-004-readlog-q002` — readlog — v15+ may exit 20 with valid stdout (Q-002)

- **Category**: connection
- **Type**: `readlog`
- **Tags**: smoke, v15, lifelines-§5
- **Timeout**: 10s
- **Iterations**: 3
- **Wall-time budget** (info-only): 5000ms

## Code

```simtalk
_(none)_
```

## Expected

```json
{
  "exit_code_in": [
    0,
    20
  ],
  "wall_time_max_ms": 5000
}
```

## Raw runs

| # | Exit | Wall ms | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|
| 1 | 20 | 444 | pass | `pass` | — | — |
| 2 | 10 | 395 | fail | `compile_error` | exit_code_in: expected one of [0, 20], got 10 | — |
| 3 | 10 | 404 | fail | `compile_error` | exit_code_in: expected one of [0, 20], got 10 | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
{ "type": "readlog", "action_id": "928cdc3fa4f54e87b079cdd8201453b9", "result": "", "log": "Index is out of range." }

```

**stderr** (first 500 chars):

```

```
