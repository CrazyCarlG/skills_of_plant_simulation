# `model-005-happy-integration` — happy path — real PS loads real .spp (integration, requires PS)

- **Category**: model-load
- **Mock mode**: False
- **Tags**: integration, smoke, skip-in-mock
- **Timeout**: 60s
- **Iterations**: 1

## Args

```

```

## Expected

```json
{
  "exit_code": 0,
  "stdout_includes": [
    "Plant Simulation launched, model loaded, socket port set to"
  ]
}
```

## Raw runs

| # | Exit | Wall ms | Mock calls | Verdict | Bucket | Failed predicates | Notes |
|---:|---:|--:|---|---|---|---|---|
| 1 | 0 | 23630 | — | pass | `pass` | — | — |

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
