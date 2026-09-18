# `com-003-hresult-disp-e-exception` — 0x80020009 (DISP_E_EXCEPTION) → exit 3 + lifelines/allow-message-box hint

- **Category**: com-errors
- **Mock mode**: True
- **Tags**: hermetic, exit-3, com-error-0x80020009, lifelines-§1, regression
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
    "0x80020009"
  ],
  "stdout_empty": true,
  "wall_time_max_ms": 350
}
```

## Raw runs

| # | Exit | Wall ms | Mock calls | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|---|
| 1 | 3 | 219 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 2 | 3 | 216 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 3 | 3 | 215 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 4 | 3 | 221 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 5 | 3 | 230 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```

```

**stderr** (first 500 chars):

```
C:\Users\z004bjuu\Documents\skills_of_plant_simulation\skills\local-window-com-start-plant-simulation\scripts\start_plant_simulation.py:26: SyntaxWarning: invalid escape sequence '\M'
  -m "C:\Models\MyModel.spp" ^
COMError: SimTalk execution failed (hresult=0x80020009)
Hint: see references/lifelines.md, or re-run with --allow-message-box to surface dialogs.

```
