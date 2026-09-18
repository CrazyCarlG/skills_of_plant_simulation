# `quirk-readlog-q002-stdout-valid` — Q-002 — readlog exit 20 still has valid stdout (don't discard it)

- **Category**: quirks
- **Type**: `readlog`
- **Tags**: quirk-readlog, Q-002, lifelines-§5
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
| 1 | 20 | 426 | pass | `pass` | — | — |
| 2 | 10 | 457 | fail | `compile_error` | exit_code_in: expected one of [0, 20], got 10 | — |
| 3 | 10 | 446 | fail | `compile_error` | exit_code_in: expected one of [0, 20], got 10 | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
{ "type": "readlog", "action_id": "b81fbbe553a4413d82e6b1280a7eda9f", "result": "", "log": "Index is out of range." }

```

**stderr** (first 500 chars):

```

```
