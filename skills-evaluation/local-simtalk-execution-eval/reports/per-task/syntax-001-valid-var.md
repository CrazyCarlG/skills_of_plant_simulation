# `syntax-001-valid-var` — valid var declaration with init

- **Category**: syntax
- **Type**: `simtalk_syntax`
- **Tags**: smoke, happy-path
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
| 1 | 0 | 416 | pass | `pass` | — | — |
| 2 | 0 | 398 | pass | `pass` | — | — |
| 3 | 0 | 411 | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
{ "type": "simtalk_syntax", "action_id": "0d56d9ddc7e64ecaac889e5296884615", "result": "has no Error", "log": "" }

```

**stderr** (first 500 chars):

```

```
