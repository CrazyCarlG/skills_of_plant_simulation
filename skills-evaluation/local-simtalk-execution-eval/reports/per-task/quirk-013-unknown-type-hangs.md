# `quirk-013-unknown-type-hangs` — Quirk #13 — unknown type value → silent hang → runner must TIMEOUT (not exit 0)

- **Category**: quirks
- **Type**: `simtalk_run`
- **Tags**: quirk-13, regression, lifelines-§3
- **Timeout**: 5s
- **Iterations**: 3
- **Wall-time budget** (info-only): 6000ms

## Code

```simtalk
_(none)_
```

## Expected

```json
{
  "exit_code": 1,
  "wall_time_max_ms": 6000
}
```

## Raw runs

| # | Exit | Wall ms | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|
| 1 | 1 | 5240 | pass | `pass` | — | — |
| 2 | 1 | 5214 | pass | `pass` | — | — |
| 3 | 1 | 5199 | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```

```

**stderr** (first 500 chars):

```
TIMEOUT: no reply within 5.0s

```
