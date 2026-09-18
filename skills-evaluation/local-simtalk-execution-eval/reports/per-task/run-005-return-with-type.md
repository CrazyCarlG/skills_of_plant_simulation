# `run-005-return-with-type` — valid -> T + return (v8 fixed form)

- **Category**: run
- **Type**: `simtalk_run`
- **Tags**: happy-path, v8
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
| 1 | 0 | 385 | pass | `pass` | — | — |
| 2 | 0 | 404 | pass | `pass` | — | — |
| 3 | 0 | 479 | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
{ "type": "simtalk_run", "action_id": "6a2787c745a9409b83175e975afc46fc", "result": "success", "log": "execute success" }

```

**stderr** (first 500 chars):

```

```
