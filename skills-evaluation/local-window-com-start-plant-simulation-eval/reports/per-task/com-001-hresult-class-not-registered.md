# `com-001-hresult-class-not-registered` — 0x80040154 (class not registered) → exit 3 + regsvr32 hint

- **Category**: com-errors
- **Mock mode**: True
- **Tags**: hermetic, exit-3, com-error-0x80040154, lifelines-§hint, regression
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
    "class not registered",
    "regsvr32",
    "0x80040154"
  ],
  "stdout_empty": true,
  "wall_time_max_ms": 350
}
```

## Raw runs

| # | Exit | Wall ms | Mock calls | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|---|
| 1 | 3 | 229 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 2 | 3 | 243 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 3 | 3 | 253 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 4 | 3 | 227 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 5 | 3 | 240 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```

```

**stderr** (first 500 chars):

```
C:\Users\z004bjuu\Documents\skills_of_plant_simulation\skills\local-window-com-start-plant-simulation\scripts\start_plant_simulation.py:26: SyntaxWarning: invalid escape sequence '\M'
  -m "C:\Models\MyModel.spp" ^
COMError: Class not registered (hresult=0x80040154)
Hint: class not registered. Install Plant Simulation 2606, or run:
  regsvr32 "<PS install dir>\Tecnomatix.PlantSimulation.RemoteControl.dll"

```
