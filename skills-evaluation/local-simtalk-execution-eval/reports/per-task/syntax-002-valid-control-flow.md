# `syntax-002-valid-control-flow` — valid while loop with multi-line body

- **Category**: syntax
- **Type**: `simtalk_syntax`
- **Tags**: happy-path, control-flow
- **Timeout**: 10s
- **Iterations**: 3
- **Wall-time budget** (info-only): 3000ms

## Code

```simtalk
var n: integer := 3
while n > 0
  print n
  n -= 1
end
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
| 1 | 0 | 483 | pass | `pass` | — | — |
| 2 | 0 | 426 | pass | `pass` | — | — |
| 3 | 0 | 435 | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
{ "type": "simtalk_syntax", "action_id": "453cefb1453f42f4b4ea483fd94e5836", "result": "has no Error", "log": "" }

```

**stderr** (first 500 chars):

```

```
