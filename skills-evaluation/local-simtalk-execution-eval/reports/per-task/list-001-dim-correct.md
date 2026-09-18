# `list-001-dim-correct` — list.dim — correct length query

- **Category**: list-api
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
| 1 | 0 | 404 | pass | `pass` | — | — |
| 2 | 0 | 413 | pass | `pass` | — | — |
| 3 | 0 | 410 | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
{ "type": "simtalk_run", "action_id": "e254de70aa8b4448912f95090adfeb70", "result": "success", "log": "execute success" }

```

**stderr** (first 500 chars):

```

```
