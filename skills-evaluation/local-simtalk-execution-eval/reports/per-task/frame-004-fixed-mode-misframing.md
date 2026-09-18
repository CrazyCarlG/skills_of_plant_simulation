# `frame-004-fixed-mode-misframing` — --resp-mode fixed with wrong byte count → hangs (no fixed mode in current protocol)

- **Category**: framing-and-namespace
- **Type**: `simtalk_syntax`
- **Tags**: expected_timeout, framing, lifelines-§2
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
| 1 | 1 | 5238 | pass | `pass` | — | — |
| 2 | 1 | 5231 | pass | `pass` | — | — |
| 3 | 1 | 5208 | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```

```

**stderr** (first 500 chars):

```
TIMEOUT: no reply within 5.0s

```
