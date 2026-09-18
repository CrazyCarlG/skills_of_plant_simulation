# `exit-code-4-file-not-found` — exit 4 — model file not found

- **Category**: exit-codes
- **Mock mode**: True
- **Tags**: hermetic, exit-4, exit-code-matrix, hard-gate, regression
- **Timeout**: 5s
- **Wall-time budget**: 350ms (info-only; not a CI gate)
- **Iterations**: 5

## Args

```
'-m' 'C:/no/such/file.spp'
```

## Expected

```json
{
  "exit_code": 4,
  "stderr_includes": [
    "Model file not found"
  ],
  "wall_time_max_ms": 350
}
```

## Raw runs

| # | Exit | Wall ms | Mock calls | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|---|
| 1 | 4 | 227 | — | pass | `pass` | — | — |
| 2 | 4 | 212 | — | pass | `pass` | — | — |
| 3 | 4 | 200 | — | pass | `pass` | — | — |
| 4 | 4 | 232 | — | pass | `pass` | — | — |
| 5 | 4 | 214 | — | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```

```

**stderr** (first 500 chars):

```
C:\Users\z004bjuu\Documents\skills_of_plant_simulation\skills\local-window-com-start-plant-simulation\scripts\start_plant_simulation.py:26: SyntaxWarning: invalid escape sequence '\M'
  -m "C:\Models\MyModel.spp" ^
Error: Model file not found: C:\no\such\file.spp

```
