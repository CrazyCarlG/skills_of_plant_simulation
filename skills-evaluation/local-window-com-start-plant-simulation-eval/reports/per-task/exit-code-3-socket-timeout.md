# `exit-code-3-socket-timeout` — exit 3 — --wait-ready socket timeout

- **Category**: exit-codes
- **Mock mode**: True
- **Tags**: hermetic, exit-3, exit-code-matrix, hard-gate, regression
- **Timeout**: 15s
- **Wall-time budget**: 2700ms (info-only; not a CI gate)
- **Iterations**: 5

## Args

```
'-p' '51113' '--wait-ready' '1'
```

## Expected

```json
{
  "exit_code": 3,
  "stderr_includes": [
    "socket readiness check failed"
  ],
  "wall_time_max_ms": 2700
}
```

## Raw runs

| # | Exit | Wall ms | Mock calls | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|---|
| 1 | 3 | 2256 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 2 | 3 | 2271 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 3 | 3 | 2260 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 4 | 3 | 2240 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 5 | 3 | 2226 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```

```

**stderr** (first 500 chars):

```
C:\Users\z004bjuu\Documents\skills_of_plant_simulation\skills\local-window-com-start-plant-simulation\scripts\start_plant_simulation.py:26: SyntaxWarning: invalid escape sequence '\M'
  -m "C:\Models\MyModel.spp" ^
Waiting for socket on 127.0.0.1:51113 ...
Error: socket readiness check failed: Socket on 127.0.0.1:51113 not ready after 1s. Verify SimtalkClaude is loaded and the port change took effect (see references/lifelines.md §1).

```
