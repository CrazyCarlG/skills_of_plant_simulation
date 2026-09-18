# `exit-code-2-bad-args` — exit 2 — bad CLI args (missing --simtalkclaudefile)

- **Category**: exit-codes
- **Mock mode**: True
- **Tags**: hermetic, exit-2, exit-code-matrix, hard-gate, regression
- **Timeout**: 5s
- **Wall-time budget**: 350ms (info-only; not a CI gate)
- **Iterations**: 5

## Args

```

```

## Expected

```json
{
  "exit_code": 2,
  "stderr_includes": [
    "required"
  ],
  "wall_time_max_ms": 350
}
```

## Raw runs

| # | Exit | Wall ms | Mock calls | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|---|
| 1 | 2 | 246 | — | pass | `pass` | — | — |
| 2 | 2 | 262 | — | pass | `pass` | — | — |
| 3 | 2 | 275 | — | pass | `pass` | — | — |
| 4 | 2 | 263 | — | pass | `pass` | — | — |
| 5 | 2 | 309 | — | pass | `pass` | — | — |

## Last raw stdout/stderr

**stdout** (first 500 chars):

```

```

**stderr** (first 500 chars):

```
C:\Users\z004bjuu\Documents\skills_of_plant_simulation\skills\local-window-com-start-plant-simulation\scripts\start_plant_simulation.py:26: SyntaxWarning: invalid escape sequence '\M'
  -m "C:\Models\MyModel.spp" ^
usage: start_plant_simulation.py [-h] -m MODEL [--no-visible]
                                 [--allow-message-box] -s SIMTALKCLAUDEFILE
                                 [-p PORT] [--wait-ready SECONDS]
                                 [--print-pid]
start_plant_simulation.py: error:…
```
