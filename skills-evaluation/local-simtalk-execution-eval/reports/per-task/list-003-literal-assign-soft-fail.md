# `list-003-literal-assign-soft-fail` — var l: list; l := [1,2,3] — incompatible assignment → Quirk #7

- **Category**: list-api
- **Type**: `simtalk_run`
- **Tags**: quirk-7, list-api, lifelines-§10
- **Timeout**: 15s
- **Iterations**: 3
- **Wall-time budget** (info-only): 8000ms

## Code

```simtalk
var l: list
l := [1,2,3]
```

## Expected

```json
{
  "exit_code": 11,
  "log_starts_with": "code execute failed",
  "wall_time_max_ms": 8000
}
```

## Raw runs

| # | Exit | Wall ms | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|
| 1 | 11 | 422 | pass | `pass` | — | — |
| 2 | 11 | 395 | pass | `pass` | — | — |
| 3 | 11 | 407 | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
{ "type": "simtalk_run", "action_id": "6486dc12a43c4e9c8220d8fab9291f52", "result": "success", "log": "code execute failed. error msg:Left and right sides of the assignment are incompatible., in code 'var l: list\nl := [1,2,3]'" }

```

**stderr** (first 500 chars):

```

```
