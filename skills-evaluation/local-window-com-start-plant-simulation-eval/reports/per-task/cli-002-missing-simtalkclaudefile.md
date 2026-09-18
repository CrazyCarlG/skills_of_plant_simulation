# `cli-002-missing-simtalkclaudefile` — missing --simtalkclaudefile → exit 2 + argparse error

- **Category**: cli-validation
- **Mock mode**: True
- **Tags**: smoke, hermetic, exit-2, cli-args-§exit-codes, lifeline-L1, regression
- **Timeout**: 5s
- **Wall-time budget**: 400ms (info-only; not a CI gate)
- **Iterations**: 5

## Args

```

```

## Expected

```json
{
  "exit_code": 2,
  "stderr_includes": [
    "required",
    "--simtalkclaudefile"
  ],
  "stdout_empty": true,
  "wall_time_max_ms": 400
}
```

## Raw runs

| # | Exit | Wall ms | Mock calls | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|---|
| 1 | 2 | 210 | — | pass | `pass` | — | — |
| 2 | 2 | 224 | — | pass | `pass` | — | — |
| 3 | 2 | 224 | — | pass | `pass` | — | — |
| 4 | 2 | 215 | — | pass | `pass` | — | — |
| 5 | 2 | 249 | — | pass | `pass` | — | — |

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
