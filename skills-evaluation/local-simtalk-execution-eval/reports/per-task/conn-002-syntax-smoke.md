# `conn-002-syntax-smoke` — simtalk_syntax smoke (valid var decl)

- **Category**: connection
- **Type**: `simtalk_syntax`
- **Tags**: smoke, happy-path, lifelines-§6
- **Timeout**: 10s
- **Iterations**: 3
- **Wall-time budget** (info-only): 3000ms

## Code

```simtalk
var x: integer := 42
```

## Expected

```json
{
  "exit_code": 0,
  "result_includes": [
    "has no Error"
  ],
  "result_excludes": [
    "hasError"
  ],
  "wall_time_max_ms": 3000
}
```

## Raw runs

| # | Exit | Wall ms | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|
| 1 | 0 | 445 | pass | `pass` | — | — |
| 2 | 0 | 394 | pass | `pass` | — | — |
| 3 | 0 | 430 | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
{ "type": "simtalk_syntax", "action_id": "bf1da5ddb1ea4ea3838ea1bc8e38d7c7", "result": "has no Error", "log": "" }

```

**stderr** (first 500 chars):

```

```
