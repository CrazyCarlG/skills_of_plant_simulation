# `run-003-quirk7-runtime-unknown-identifier` — Quirk #7 — unknown identifier triggers soft fail (exit 11)

- **Category**: run
- **Type**: `simtalk_run`
- **Tags**: quirk-7, runtime-error, lifelines-§6
- **Timeout**: 15s
- **Iterations**: 3
- **Wall-time budget** (info-only): 8000ms

## Code

```simtalk
print nonExistentVariable
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
| 1 | 11 | 410 | pass | `pass` | — | — |
| 2 | 11 | 431 | pass | `pass` | — | — |
| 3 | 11 | 415 | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
{ "type": "simtalk_run", "action_id": "a3523ae1062d45cc822e3f0b8f4cc9c9", "result": "success", "log": "code execute failed. error msg:Unknown identifier 'nonExistentVariable', in code 'print nonExistentVariable'" }

```

**stderr** (first 500 chars):

```

```
