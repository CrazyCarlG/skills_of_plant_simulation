# `syntax-003-valid-param-default` — valid param with default value (v10 safest form)

- **Category**: syntax
- **Type**: `simtalk_syntax`
- **Tags**: happy-path, param, v10
- **Timeout**: 10s
- **Iterations**: 3
- **Wall-time budget** (info-only): 3000ms

## Code

```simtalk
param str:string := "x"
print str
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
| 1 | 0 | 414 | pass | `pass` | — | — |
| 2 | 0 | 391 | pass | `pass` | — | — |
| 3 | 0 | 392 | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
{ "type": "simtalk_syntax", "action_id": "604d4ece95814466b27c611effbca2c4", "result": "has no Error", "log": "" }

```

**stderr** (first 500 chars):

```

```
