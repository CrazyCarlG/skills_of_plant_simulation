# `syntax-006-invalid-name-clash` — var + param name-clash pattern (v9 regression case)

- **Category**: syntax
- **Type**: `simtalk_syntax`
- **Tags**: negative, v9-regression
- **Timeout**: 10s
- **Iterations**: 3
- **Wall-time budget** (info-only): 3000ms

## Code

```simtalk
var a,b: integer
param x: real := 1.0
return x+a
```

## Expected

```json
{
  "exit_code": 12,
  "result_includes": [
    "hasError"
  ],
  "result_excludes": [
    "has no Error"
  ],
  "wall_time_max_ms": 3000
}
```

## Raw runs

| # | Exit | Wall ms | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|
| 1 | 12 | 446 | fail | `syntax_error` | result_includes: missing 'hasError' in result '' | — |
| 2 | 12 | 437 | fail | `syntax_error` | result_includes: missing 'hasError' in result '' | — |
| 3 | 12 | 466 | fail | `syntax_error` | result_includes: missing 'hasError' in result '' | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```


```

**stderr** (first 500 chars):

```
[simtalk_send.cmd_syntax] socket error: code=1 reply=''

```
