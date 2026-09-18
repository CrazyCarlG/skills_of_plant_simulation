# `port-003-executesimtalk-called-twice` — two ExecuteSimTalk calls (inject + changeport) — full L1 order check

- **Category**: port-change
- **Mock mode**: True
- **Tags**: hermetic, lifecycle, lifeline-L1, regression
- **Timeout**: 10s
- **Wall-time budget**: 400ms (info-only; not a CI gate)
- **Iterations**: 5

## Args

```
'-p' '50008'
```

## Expected

```json
{
  "exit_code": 0,
  "stdout_includes": [
    "socket port set to 50008"
  ],
  "wall_time_max_ms": 400
}
```

## Raw runs

| # | Exit | Wall ms | Mock calls | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|---|
| 1 | 0 | 213 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 2 | 0 | 230 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 3 | 0 | 290 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 4 | 0 | 226 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 5 | 0 | 222 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```
Plant Simulation launched, model loaded, socket port set to 50008.

```

**stderr** (first 500 chars):

```
C:\Users\z004bjuu\Documents\skills_of_plant_simulation\skills\local-window-com-start-plant-simulation\scripts\start_plant_simulation.py:26: SyntaxWarning: invalid escape sequence '\M'
  -m "C:\Models\MyModel.spp" ^

```
