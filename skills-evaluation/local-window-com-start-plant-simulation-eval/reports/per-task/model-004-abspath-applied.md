# `model-004-abspath-applied` — relative model path → error message uses the abspath form

- **Category**: model-load
- **Mock mode**: True
- **Tags**: hermetic, exit-4, lifeline-L4, cli-args-§abspath, regression
- **Timeout**: 5s
- **Wall-time budget**: 350ms (info-only; not a CI gate)
- **Iterations**: 5

## Args

```
'-m' 'this_file_definitely_does_not_exist_relative.spp'
```

## Expected

```json
{
  "exit_code": 4,
  "stderr_includes": [
    "Model file not found"
  ],
  "stdout_empty": true,
  "wall_time_max_ms": 350
}
```

## Raw runs

| # | Exit | Wall ms | Mock calls | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|---|
| 1 | 4 | 247 | — | pass | `pass` | — | — |
| 2 | 4 | 239 | — | pass | `pass` | — | — |
| 3 | 4 | 208 | — | pass | `pass` | — | — |
| 4 | 4 | 218 | — | pass | `pass` | — | — |
| 5 | 4 | 218 | — | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```

```

**stderr** (first 500 chars):

```
C:\Users\z004bjuu\Documents\skills_of_plant_simulation\skills\local-window-com-start-plant-simulation\scripts\start_plant_simulation.py:26: SyntaxWarning: invalid escape sequence '\M'
  -m "C:\Models\MyModel.spp" ^
Error: Model file not found: C:\Users\z004bjuu\Documents\skills_of_plant_simulation\skills-evaluation\local-window-com-start-plant-simulation-eval\this_file_definitely_does_not_exist_relative.spp

```
