# `wait-005-progress-on-stderr` — --wait-ready poll → 'Waiting for socket' progress on stderr (not stdout)

- **Category**: wait-ready
- **Mock mode**: True
- **Tags**: hermetic, stdout-stderr-discipline, cli-args-§output, regression
- **Timeout**: 15s
- **Wall-time budget**: 5000ms (info-only; not a CI gate)
- **Iterations**: 5

## Args

```
'-p' '51112' '--wait-ready' '2'
```

## Expected

```json
{
  "exit_code": 3,
  "stderr_includes": [
    "Waiting for socket on 127.0.0.1:51112"
  ],
  "stdout_excludes": [
    "Waiting for socket"
  ],
  "wall_time_max_ms": 5000
}
```

## Raw runs

| # | Exit | Wall ms | Mock calls | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|---|
| 1 | 3 | 2245 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 2 | 3 | 2247 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 3 | 3 | 2252 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 4 | 3 | 2249 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |
| 5 | 3 | 2232 | Dispatch('Tecnomatix.PlantSimulation.Re… | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```

```

**stderr** (first 500 chars):

```
C:\Users\z004bjuu\Documents\skills_of_plant_simulation\skills\local-window-com-start-plant-simulation\scripts\start_plant_simulation.py:26: SyntaxWarning: invalid escape sequence '\M'
  -m "C:\Models\MyModel.spp" ^
Waiting for socket on 127.0.0.1:51112 ...
Error: socket readiness check failed: Socket on 127.0.0.1:51112 not ready after 2s. Verify SimtalkClaude is loaded and the port change took effect (see references/lifelines.md §1).

```
