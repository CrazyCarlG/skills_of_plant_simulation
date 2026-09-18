# `exit-code-5-uncaught` — exit 5 — uncaught RuntimeError from non-COM fault

- **Category**: exit-codes
- **Mock mode**: True
- **Tags**: hermetic, exit-5, exit-code-matrix, hard-gate, regression
- **Timeout**: 10s
- **Wall-time budget**: 350ms (info-only; not a CI gate)
- **Iterations**: 5

## Args

```

```

## Expected

```json
{
  "exit_code": 5,
  "stderr_includes": [
    "synthetic non-com fault"
  ],
  "wall_time_max_ms": 350
}
```

## Raw runs

| # | Exit | Wall ms | Mock calls | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|---|
| 1 | 5 | 217 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 2 | 5 | 228 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 3 | 5 | 233 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 4 | 5 | 263 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 5 | 5 | 226 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```

```

**stderr** (first 500 chars):

```
C:\Users\z004bjuu\Documents\skills_of_plant_simulation\skills\local-window-com-start-plant-simulation\scripts\start_plant_simulation.py:26: SyntaxWarning: invalid escape sequence '\M'
  -m "C:\Models\MyModel.spp" ^
Error: synthetic non-com fault for exit-5 matrix

```
