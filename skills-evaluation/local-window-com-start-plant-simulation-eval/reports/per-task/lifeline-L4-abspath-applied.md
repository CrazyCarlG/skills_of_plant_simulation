# `lifeline-L4-abspath-applied` — L4: relative --model path is abspath-ified before os.path.isfile

- **Category**: lifelines
- **Mock mode**: True
- **Tags**: hermetic, lifeline-L4, exit-4, hard-gate, regression
- **Timeout**: 5s
- **Wall-time budget**: 400ms (info-only; not a CI gate)
- **Iterations**: 5

## Args

```
'-m' 'no_such_relative.spp'
```

## Expected

```json
{
  "exit_code": 4,
  "stderr_includes": [
    "Model file not found"
  ],
  "wall_time_max_ms": 400
}
```

## Raw runs

| # | Exit | Wall ms | Mock calls | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|---|
| 1 | 4 | 254 | — | pass | `pass` | — | — |
| 2 | 4 | 230 | — | pass | `pass` | — | — |
| 3 | 4 | 220 | — | pass | `pass` | — | — |
| 4 | 4 | 262 | — | pass | `pass` | — | — |
| 5 | 4 | 213 | — | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```

```

**stderr** (first 500 chars):

```
C:\Users\z004bjuu\Documents\skills_of_plant_simulation\skills\local-window-com-start-plant-simulation\scripts\start_plant_simulation.py:26: SyntaxWarning: invalid escape sequence '\M'
  -m "C:\Models\MyModel.spp" ^
Error: Model file not found: C:\Users\z004bjuu\Documents\skills_of_plant_simulation\skills-evaluation\local-window-com-start-plant-simulation-eval\no_such_relative.spp

```
