# `modal-003-undeclared-attr` — writing an attribute that doesn't exist triggers modal 'create attribute?' dialog

- **Category**: modal-traps
- **Type**: `simtalk_run`
- **Tags**: expected_timeout, modal-trap, lifelines-§4, v9-R5
- **Timeout**: 8s
- **Iterations**: 3
- **Wall-time budget** (info-only): 10000ms

## Code

```simtalk
MyNotYetExistingAttr := 99
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
| 1 | 10 | 8447 | fail | `compile_error` | exit_code: expected 1, got 10 | — |
| 2 | 10 | 8455 | fail | `compile_error` | exit_code: expected 1, got 10 | — |
| 3 | 10 | 8421 | fail | `compile_error` | exit_code: expected 1, got 10 | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```


```

**stderr** (first 500 chars):

```
[simtalk_send.cmd_run] socket error: code=1 reply=''

```
