# `quirk-007-soft-failure-detected` — Quirk #7 — runtime exception returns exit 11, not exit 0

- **Category**: quirks
- **Type**: `simtalk_run`
- **Tags**: quirk-7, regression, lifelines-§6
- **Timeout**: 15s
- **Iterations**: 3
- **Wall-time budget** (info-only): 8000ms

## Code

```simtalk
print undeclared_identifier_here
```

## Expected

```json
{
  "exit_code": 11,
  "log_starts_with": "code execute failed",
  "wall_time_max_ms": 8000
}
```

## Raw runs

| # | Exit | Wall ms | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|
| 1 | 11 | 437 | pass | `pass` | — | — |
| 2 | 11 | 420 | pass | `pass` | — | — |
| 3 | 11 | 397 | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
{ "type": "simtalk_run", "action_id": "5072cb49e2cc48829435ac25e95ca5bf", "result": "success", "log": "code execute failed. error msg:Unknown identifier 'undeclared_identifier_here', in code 'print undeclared_identifier_here'" }

```

**stderr** (first 500 chars):

```

```
