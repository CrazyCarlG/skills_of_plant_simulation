# `run-006-list-dim` — list.dim is the only correct length query (lifelines §10.1)

- **Category**: run
- **Type**: `simtalk_run`
- **Tags**: happy-path, list-api, lifelines-§10
- **Timeout**: 15s
- **Iterations**: 3
- **Wall-time budget** (info-only): 10000ms

## Code

```simtalk
var l: list
l := getFilesOfFolder(".")
print l.dim
```

## Expected

```json
{
  "exit_code": 0,
  "result_includes": [
    "success"
  ],
  "log_not_starts_with": "code execute failed",
  "wall_time_max_ms": 10000
}
```

## Raw runs

| # | Exit | Wall ms | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|
| 1 | 0 | 445 | pass | `pass` | — | — |
| 2 | 0 | 424 | pass | `pass` | — | — |
| 3 | 0 | 389 | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
{ "type": "simtalk_run", "action_id": "6624c56d2aa248fc9d19995df889ee1f", "result": "success", "log": "execute success" }

```

**stderr** (first 500 chars):

```

```
