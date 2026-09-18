# `list-002-length-unknown-identifier` — list.length — Unknown identifier 'Length' → Quirk #7 soft fail (exit 11)

- **Category**: list-api
- **Type**: `simtalk_run`
- **Tags**: quirk-7, list-api, lifelines-§10
- **Timeout**: 15s
- **Iterations**: 3
- **Wall-time budget** (info-only): 8000ms

## Code

```simtalk
var l: list
l := getFilesOfFolder(".")
print l.length
```

## Expected

```json
{
  "exit_code": 11,
  "result_includes": [
    "success"
  ],
  "log_starts_with": "code execute failed",
  "wall_time_max_ms": 8000
}
```

## Raw runs

| # | Exit | Wall ms | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|
| 1 | 11 | 431 | pass | `pass` | — | — |
| 2 | 11 | 383 | pass | `pass` | — | — |
| 3 | 11 | 396 | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
{ "type": "simtalk_run", "action_id": "876311fe0be54299b656e26bbd0911e3", "result": "success", "log": "code execute failed. error msg:Unknown identifier 'Length', in code 'var l: list\nl := getFilesOfFolder(\".\")\nprint l.length'" }

```

**stderr** (first 500 chars):

```

```
