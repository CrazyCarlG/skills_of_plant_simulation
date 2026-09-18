# `pid-002-warning-when-no-ps` — --print-pid + no PS in tasklist → warning on stderr, exit 0

- **Category**: print-pid
- **Mock mode**: True
- **Tags**: hermetic, lifecycle, cli-args-§print-pid, regression
- **Timeout**: 10s
- **Wall-time budget**: 1000ms (info-only; not a CI gate)
- **Iterations**: 5

## Args

```
'--print-pid'
```

## Expected

```json
{
  "exit_code": 0,
  "stderr_includes": [
    "--print-pid requested",
    "Plant Simulation.exe not found"
  ],
  "wall_time_max_ms": 1000
}
```

## Raw runs

| # | Exit | Wall ms | Mock calls | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|---|
| 1 | 0 | 709 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 2 | 0 | 728 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 3 | 0 | 766 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 4 | 0 | 696 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 5 | 0 | 744 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
Plant Simulation launched, model loaded, socket port set to 50007.

```

**stderr** (first 500 chars):

```
C:\Users\z004bjuu\Documents\skills_of_plant_simulation\skills\local-window-com-start-plant-simulation\scripts\start_plant_simulation.py:26: SyntaxWarning: invalid escape sequence '\M'
  -m "C:\Models\MyModel.spp" ^
Warning: --print-pid requested but Plant Simulation.exe not found via tasklist.

```
