# `frame-001-delimiter-default` — default delimiter framing — happy path

- **Category**: framing-and-namespace
- **Type**: `ping`
- **Tags**: smoke, happy-path, lifelines-§2
- **Timeout**: 5s
- **Iterations**: 3
- **Wall-time budget** (info-only): 2000ms

## Code

```simtalk
_(none)_
```

## Expected

```json
{
  "exit_code": 0,
  "result_includes": [
    "success"
  ],
  "wall_time_max_ms": 2000
}
```

## Raw runs

| # | Exit | Wall ms | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|
| 1 | 0 | 468 | pass | `pass` | — | — |
| 2 | 0 | 452 | pass | `pass` | — | — |
| 3 | 0 | 416 | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
{ "type": "ping", "result": "success" }

```

**stderr** (first 500 chars):

```

```
