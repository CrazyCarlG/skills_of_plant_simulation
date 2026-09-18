# `wait-002-wait-ready-1-busy-port` — --wait-ready 1 with assumed-busy port 51111 → exit 3 + TimeoutError

- **Category**: wait-ready
- **Mock mode**: True
- **Tags**: hermetic, exit-3, cli-args-§wait-ready, lifeline-L5, regression
- **Timeout**: 15s
- **Wall-time budget**: 2700ms (info-only; not a CI gate)
- **Iterations**: 5

## Args

```
'-p' '51111' '--wait-ready' '1'
```

## Expected

```json
{
  "exit_code": 3,
  "stderr_includes": [
    "socket readiness check failed",
    "51111"
  ],
  "stdout_excludes": [
    "Plant Simulation launched"
  ],
  "wall_time_max_ms": 2700
}
```

## Raw runs

| # | Exit | Wall ms | Mock calls | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|---|
| 1 | 3 | 2241 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 2 | 3 | 2270 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 3 | 3 | 2246 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 4 | 3 | 2224 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 5 | 3 | 2211 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```

```

**stderr** (first 500 chars):

```
C:\Users\z004bjuu\Documents\skills_of_plant_simulation\skills\local-window-com-start-plant-simulation\scripts\start_plant_simulation.py:26: SyntaxWarning: invalid escape sequence '\M'
  -m "C:\Models\MyModel.spp" ^
Waiting for socket on 127.0.0.1:51111 ...
Error: socket readiness check failed: Socket on 127.0.0.1:51111 not ready after 1s. Verify SimtalkClaude is loaded and the port change took effect (see references/lifelines.md §1).

```
