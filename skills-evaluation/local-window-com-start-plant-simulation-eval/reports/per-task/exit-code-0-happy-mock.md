# `exit-code-0-happy-mock` — exit 0 — happy path in mock mode (no --wait-ready)

- **Category**: exit-codes
- **Mock mode**: True
- **Tags**: hermetic, exit-0, smoke, exit-code-matrix, regression
- **Timeout**: 10s
- **Wall-time budget**: 350ms (info-only; not a CI gate)
- **Iterations**: 5

## Args

```

```

## Expected

```json
{
  "exit_code": 0,
  "stdout_includes": [
    "Plant Simulation launched"
  ],
  "wall_time_max_ms": 350
}
```

## Raw runs

| # | Exit | Wall ms | Mock calls | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|---|
| 1 | 0 | 226 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 2 | 0 | 213 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 3 | 0 | 247 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 4 | 0 | 253 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 5 | 0 | 281 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
Plant Simulation launched, model loaded, socket port set to 50007.

```

**stderr** (first 500 chars):

```
C:\Users\z004bjuu\Documents\skills_of_plant_simulation\skills\local-window-com-start-plant-simulation\scripts\start_plant_simulation.py:26: SyntaxWarning: invalid escape sequence '\M'
  -m "C:\Models\MyModel.spp" ^

```
