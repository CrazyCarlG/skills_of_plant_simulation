# `run-004-compile-error-division-by-zero` — Q-001 — literal 1/0 is compile-time, NOT Quirk #7 (exit 10)

- **Category**: run
- **Type**: `simtalk_run`
- **Tags**: compile-error, Q-001, lifelines-§6
- **Timeout**: 15s
- **Iterations**: 3
- **Wall-time budget** (info-only): 8000ms

## Code

```simtalk
print 1/0
```

## Expected

```json
{
  "exit_code": 10,
  "result_includes": [
    "failed"
  ],
  "log_starts_with": " hasError",
  "wall_time_max_ms": 8000
}
```

## Raw runs

| # | Exit | Wall ms | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|
| 1 | 10 | 429 | fail | `compile_error` | result_includes: missing 'failed' in result ''; log_starts_with: expected prefi… | — |
| 2 | 10 | 430 | fail | `compile_error` | result_includes: missing 'failed' in result ''; log_starts_with: expected prefi… | — |
| 3 | 10 | 453 | fail | `compile_error` | result_includes: missing 'failed' in result ''; log_starts_with: expected prefi… | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```


```

**stderr** (first 500 chars):

```
[simtalk_send.cmd_run] socket error: code=1 reply=''

```
