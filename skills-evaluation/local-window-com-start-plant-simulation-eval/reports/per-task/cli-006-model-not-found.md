# `cli-006-model-not-found` — model path does not exist → exit 4 + 'Model file not found'

- **Category**: cli-validation
- **Mock mode**: True
- **Tags**: hermetic, exit-4, cli-args-§exit-codes, regression
- **Timeout**: 5s
- **Wall-time budget**: 400ms (info-only; not a CI gate)
- **Iterations**: 5

## Args

```
'-m' 'C:/nonexistent/missing_model.spp'
```

## Expected

```json
{
  "exit_code": 4,
  "stderr_includes": [
    "Model file not found"
  ],
  "stdout_empty": true,
  "wall_time_max_ms": 400
}
```

## Raw runs

| # | Exit | Wall ms | Mock calls | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|---|
| 1 | 4 | 230 | — | pass | `pass` | — | — |
| 2 | 4 | 210 | — | pass | `pass` | — | — |
| 3 | 4 | 219 | — | pass | `pass` | — | — |
| 4 | 4 | 227 | — | pass | `pass` | — | — |
| 5 | 4 | 204 | — | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```

```

**stderr** (first 500 chars):

```
C:\Users\z004bjuu\Documents\skills_of_plant_simulation\skills\local-window-com-start-plant-simulation\scripts\start_plant_simulation.py:26: SyntaxWarning: invalid escape sequence '\M'
  -m "C:\Models\MyModel.spp" ^
Error: Model file not found: C:\nonexistent\missing_model.spp

```
