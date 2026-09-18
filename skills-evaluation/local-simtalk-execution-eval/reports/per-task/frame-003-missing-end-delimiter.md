# `frame-003-missing-end-delimiter` — missing trailing ||END|| — client can't find frame end → timeout

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
| 1 | 0 | 204 | fail | `unexpected_success` | exit_code: expected 1, got 0 | — |
| 2 | 0 | 183 | fail | `unexpected_success` | exit_code: expected 1, got 0 | — |
| 3 | 0 | 185 | fail | `unexpected_success` | exit_code: expected 1, got 0 | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
{ "type": "simtalk_syntax", "action_id": "noend", "result": "has no Error", "log": "" }||END||

```

**stderr** (first 500 chars):

```

```
