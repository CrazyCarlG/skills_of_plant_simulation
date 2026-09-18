# `lifeline-L3-allow-message-box` — L3: --allow-message-box still calls SetNoMessageBox (with False)

- **Category**: lifelines
- **Mock mode**: True
- **Tags**: hermetic, lifeline-L3, regression
- **Timeout**: 10s
- **Wall-time budget**: 400ms (info-only; not a CI gate)
- **Iterations**: 5

## Args

```
'--allow-message-box'
```

## Expected

```json
{
  "exit_code": 0,
  "wall_time_max_ms": 400,
  "mock_call_sequence_includes": [
    "Tecnomatix.PlantSimulation.RemoteControl.26.6.SetNoMessageBox"
  ]
}
```

## Raw runs

| # | Exit | Wall ms | Mock calls | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|---|
| 1 | 0 | 221 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 2 | 0 | 236 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 3 | 0 | 224 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 4 | 0 | 216 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 5 | 0 | 222 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |

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
