# `wait-004-wait-ready-negative-skipped` — --wait-ready -1 → script treats as 'skip' (only > 0 triggers poll), exit 0

- **Category**: wait-ready
- **Mock mode**: True
- **Tags**: hermetic, edge-case, cli-args-§wait-ready, regression
- **Timeout**: 10s
- **Wall-time budget**: 350ms (info-only; not a CI gate)
- **Iterations**: 5

## Args

```
'--wait-ready' '-1'
```

## Expected

```json
{
  "exit_code": 0,
  "stderr_excludes": [
    "Waiting for socket"
  ],
  "wall_time_max_ms": 350
}
```

## Raw runs

| # | Exit | Wall ms | Mock calls | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|---|
| 1 | 0 | 227 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 2 | 0 | 211 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 3 | 0 | 214 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 4 | 0 | 211 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 5 | 0 | 251 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |

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
