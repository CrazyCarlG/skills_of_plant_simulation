# `lifeline-L4-abspath-pslib` — L4: relative --simtalkclaudefile path is abspath-ified

- **Category**: lifelines
- **Mock mode**: True
- **Tags**: hermetic, lifeline-L4, exit-4, hard-gate, regression
- **Timeout**: 5s
- **Wall-time budget**: 400ms (info-only; not a CI gate)
- **Iterations**: 5

## Args

```
'-s' 'no_such_relative.pslib'
```

## Expected

```json
{
  "exit_code": 4,
  "stderr_includes": [
    "SimtalkClaude library not found"
  ],
  "wall_time_max_ms": 400
}
```

## Raw runs

| # | Exit | Wall ms | Mock calls | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|---|
| 1 | 4 | 240 | — | pass | `pass` | — | — |
| 2 | 4 | 278 | — | pass | `pass` | — | — |
| 3 | 4 | 237 | — | pass | `pass` | — | — |
| 4 | 4 | 218 | — | pass | `pass` | — | — |
| 5 | 4 | 228 | — | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```

```

**stderr** (first 500 chars):

```
C:\Users\z004bjuu\Documents\skills_of_plant_simulation\skills\local-window-com-start-plant-simulation\scripts\start_plant_simulation.py:26: SyntaxWarning: invalid escape sequence '\M'
  -m "C:\Models\MyModel.spp" ^
Error: SimtalkClaude library not found: C:\Users\z004bjuu\Documents\skills_of_plant_simulation\skills-evaluation\local-window-com-start-plant-simulation-eval\no_such_relative.pslib

```
