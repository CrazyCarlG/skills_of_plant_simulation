# `lifeline-L6-pywin32-required` — L6: missing pywin32 → RuntimeError 'pywin32 (wincom) is required...'

- **Category**: lifelines
- **Mock mode**: True
- **Tags**: hermetic, lifeline-L6, regression
- **Timeout**: 5s
- **Wall-time budget**: 400ms (info-only; not a CI gate)
- **Iterations**: 5

## Args

```

```

## Expected

```json
{
  "exit_code_in": [
    3,
    5
  ],
  "stderr_includes": [
    "pywin32"
  ],
  "wall_time_max_ms": 400
}
```

## Raw runs

| # | Exit | Wall ms | Mock calls | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|---|
| 1 | 5 | 245 | — | pass | `pass` | — | — |
| 2 | 5 | 238 | — | pass | `pass` | — | — |
| 3 | 5 | 255 | — | pass | `pass` | — | — |
| 4 | 5 | 225 | — | pass | `pass` | — | — |
| 5 | 5 | 249 | — | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```

```

**stderr** (first 500 chars):

```
C:\Users\z004bjuu\Documents\skills_of_plant_simulation\skills\local-window-com-start-plant-simulation\scripts\start_plant_simulation.py:26: SyntaxWarning: invalid escape sequence '\M'
  -m "C:\Models\MyModel.spp" ^
Error: pywin32 (win32com) is required. Install with 'pip install pywin32'.

```
