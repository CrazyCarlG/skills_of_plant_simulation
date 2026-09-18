# `modal-004-promptList1` — promptList1() — also modal

- **Category**: modal-traps
- **Type**: `simtalk_run`
- **Tags**: expected_timeout, modal-trap, lifelines-§4
- **Timeout**: 8s
- **Iterations**: 3
- **Wall-time budget** (info-only): 10000ms

## Code

```simtalk
promptList1("pick one", "a", "b")
```

## Expected

```json
{
  "exit_code": 1,
  "wall_time_max_ms": 10000
}
```

## Raw runs

| # | Exit | Wall ms | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|
| 1 | 10 | 8438 | fail | `compile_error` | exit_code: expected 1, got 10 | — |
| 2 | 10 | 8434 | fail | `compile_error` | exit_code: expected 1, got 10 | — |
| 3 | 10 | 8467 | fail | `compile_error` | exit_code: expected 1, got 10 | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```


```

**stderr** (first 500 chars):

```
[simtalk_send.cmd_run] socket error: code=1 reply=''

```
