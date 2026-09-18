# `syntax-004-invalid-byval` — param byval — explicit byval is illegal (byval is default)

- **Category**: syntax
- **Type**: `simtalk_syntax`
- **Tags**: negative, param, v10
- **Timeout**: 10s
- **Iterations**: 3
- **Wall-time budget** (info-only): 3000ms

## Code

```simtalk
param byval str:string
print str
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
| 1 | 12 | 435 | fail | `syntax_error` | result_includes: missing 'hasError' in result '' | — |
| 2 | 12 | 407 | fail | `syntax_error` | result_includes: missing 'hasError' in result '' | — |
| 3 | 12 | 426 | fail | `syntax_error` | result_includes: missing 'hasError' in result '' | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```


```

**stderr** (first 500 chars):

```
[simtalk_send.cmd_syntax] socket error: code=1 reply=''

```
