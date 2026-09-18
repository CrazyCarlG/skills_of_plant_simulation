# local-simtalk-execution-eval

Evaluation framework for the [`local-simtalk-execution`](../../skills/local-simtalk-execution/SKILL.md) skill.

## What it does

Runs a **golden task suite** (32 cases × N iterations) against a live Plant
Simulation server and grades each response against the documented contract in
[`lifelines.md` §6](../../skills/local-simtalk-execution/references/lifelines.md).
Produces a Markdown report + JSON snapshot.

## Quick start

```bash
# 1. Make sure PS is running with SimtalkClaude listening on host:port
#    (default: host.docker.internal:50007)

# 2. Run the full suite
python3 scripts/run_eval.py

# 3. Read the report
cat reports/summary.md
```

## Output

```
reports/
├── summary.md          # human-readable pass rates + bucket histogram
├── summary.json        # machine-readable aggregate
├── per-task/<id>.md    # per-task raw runs + verdict reasoning
└── snapshot-<ts>.json  # for cross-version regression diff
```

## Directory layout

```
local-simtalk-execution-eval/
├── METHODOLOGY.md            # the 7 evaluation dimensions (read first)
├── README.md                 # you are here
├── .eval-config.yaml         # host/port/N-iterations/timeouts
├── CONTRIBUTING.md           # how to add a task / grader
├── eval/
│   ├── task.py               # Task dataclass + JSON loader
│   ├── grader.py             # predicate-based auto-grader
│   ├── stats.py              # pass rate, σ, CI95
│   ├── runner.py             # executes each task N times
│   └── reporter.py           # Markdown + JSON report writer
├── tasks/                    # golden task suite (32 cases)
│   ├── 01-connection.json
│   ├── 02-syntax.json
│   ├── 03-run.json
│   ├── 04-quirks.json
│   ├── 05-modal-traps.json
│   ├── 06-list-api.json
│   └── 07-framing-and-namespace.json
└── scripts/
    └── run_eval.py           # CLI entry
```

## CLI

```text
python3 scripts/run_eval.py [--suite <path>] [--tag <tag>] [--iterations N] [--mock] [--compare old.json new.json]
```

| Flag | Meaning |
|---|---|
| `--suite` | override tasks/ dir (default: `./tasks`) |
| `--tag` | filter tasks by tag (e.g., `--tag smoke` or `--tag quirk-7`) |
| `--iterations` | N per task (default: 5) |
| `--mock` | use fixture server responses (no real PS needed) |
| `--compare` | diff two snapshots; produce regression report |

## Evaluation dimensions

See [`METHODOLOGY.md`](./METHODOLOGY.md) §2 for the full list. Short version:

1. **Trigger Precision** — right `type`/`subcommand` used
2. **Semantic Completion** — exit code + `result`/`log` per `lifelines.md` §6
3. **Efficiency** — wall time vs budget
4. **Robustness** — bad JSON, missing field, unknown type
5. **Variance Stability** — N-run pass rate, σ
6. **Quirk Protocol Compliance** — Quirk #5/#6/#7/#13
7. **Failure Attribution** — 10-bucket histogram

## CI integration

Suggested gate (insert into your CI):

```bash
python3 scripts/run_eval.py --iterations 5
python3 -c "
import json, sys
r = json.load(open('reports/summary.json'))
if r['weighted_pass_rate'] < 0.95: sys.exit(1)
if r['new_flaky'] > 0: sys.exit(2)
if any(t['id'].startswith('quirk-') and t['pass_rate'] < 1.0 for t in r['tasks']):
    sys.exit(3)
"
```

Exit codes:
- `0` — all gates pass
- `1` — overall pass rate < 95%
- `2` — new flaky task
- `3` — Quirk regression

## Limitations

See `METHODOLOGY.md` §6. Headline: live server required for real run; mock mode
for offline development only.

## Related

- Skill under test: [`skills/local-simtalk-execution/`](../../skills/local-simtalk-execution/)
- Hard rules (the contract): [`skills/local-simtalk-execution/references/lifelines.md`](../../skills/local-simtalk-execution/references/lifelines.md)
- Skill logs: [`skills/local-simtalk-execution/log/`](../../skills/local-simtalk-execution/log/)