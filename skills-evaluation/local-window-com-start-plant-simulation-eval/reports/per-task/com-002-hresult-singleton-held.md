# `com-002-hresult-singleton-held` — 0x80080005 (singleton held) → exit 3 + taskkill hint

- **Category**: com-errors
- **Mock mode**: True
- **Tags**: hermetic, exit-3, com-error-0x80080005, lifelines-§2, regression
- **Timeout**: 10s
- **Wall-time budget**: 350ms (info-only; not a CI gate)
- **Iterations**: 5

## Args

```
'-p' '50007'
```

## Expected

```json
{
  "exit_code": 3,
  "stderr_includes": [
    "taskkill",
    "Plant Simulation.exe",
    "0x80080005"
  ],
  "stdout_empty": true,
  "wall_time_max_ms": 350
}
```

## Raw runs

| # | Exit | Wall ms | Mock calls | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|---|
| 1 | 3 | 262 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 2 | 3 | 247 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 3 | 3 | 259 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 4 | 3 | 224 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 5 | 3 | 213 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```

```

**stderr** (first 500 chars):

```
C:\Users\z004bjuu\Documents\skills_of_plant_simulation\skills\local-window-com-start-plant-simulation\scripts\start_plant_simulation.py:26: SyntaxWarning: invalid escape sequence '\M'
  -m "C:\Models\MyModel.spp" ^
COMError: COM server execution failed (hresult=0x80080005)
Hint: COM server launch failed. Another Plant Simulation instance may be
  holding the singleton. Try:  taskkill /IM "Plant Simulation.exe" /F

```
