# local-window-com-start-plant-simulation-eval

Evaluation framework for the
[`local-window-com-start-plant-simulation`](../../skills/local-window-com-start-plant-simulation/SKILL.md)
skill.

## What it does

Runs a **golden task suite** (≥ 40 cases × N iterations) against the
`start_plant_simulation.py` CLI. The runner spawns the script as a subprocess
and grades each invocation against the contract documented in
[`references/lifelines.md`](../../skills/local-window-com-start-plant-simulation/references/lifelines.md)
and [`references/cli-args.md`](../../skills/local-window-com-start-plant-simulation/references/cli-args.md).
Produces a Markdown report + JSON snapshot.

Unlike `local-simtalk-execution-eval` (which tests an in-process TCP client),
this suite tests a **subprocess** with **side effects on the host machine**
(launches a real `Plant Simulation.exe`). The 7 evaluation dimensions are
adapted accordingly (see [`METHODOLOGY.md`](./METHODOLOGY.md) §2).

## Quick start

```bash
# 1. Pick a model + SimtalkClaude.pslib (any real files you have).
#    Use absolute paths — see references/lifelines.md §4.

# 2. Run the full suite. Most tasks are hermetic (don't touch COM);
#    only the happy-path integration cases need real PS installed.
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
local-window-com-start-plant-simulation-eval/
├── METHODOLOGY.md                # the 7 evaluation dimensions (read first)
├── README.md                     # you are here
├── .eval-config.yaml             # script path / model / pslib / N-iterations
├── CONTRIBUTING.md               # how to add a task / grader
├── eval/
│   ├── __init__.py
│   ├── task.py                   # Task dataclass + JSON loader
│   ├── grader.py                 # predicate-based auto-grader
│   ├── stats.py                  # pass rate, σ, CI95
│   ├── runner.py                 # executes each task N times
│   └── reporter.py               # Markdown + JSON report writer
├── tasks/                        # golden task suite
│   ├── 01-cli-validation.json    # argparse / file-existence / port-range
│   ├── 02-com-errors.json        # 0x80040154 / 0x80080005 / 0x80020009 hints
│   ├── 03-model-load.json        # LoadModel + SetTrustModels + path abs
│   ├── 04-injection.json         # basis.loadObjectAs + quoting
│   ├── 05-port-change.json       # changeport_command + port-set
│   ├── 06-wait-ready.json        # TCP poll, timeout, ConnectionRefusedError
│   ├── 07-print-pid.json         # tasklist parsing
│   ├── 08-lifelines.json         # L1-L6 hard-rule compliance
│   └── 09-exit-codes.json        # full exit-code matrix
├── scripts/
│   └── run_eval.py               # CLI entry
└── tests/
    └── test_smoke.py             # self-test of the framework itself
```

## CLI

```text
python3 scripts/run_eval.py [--suite <path>] [--config <path>] [--out <path>]
                            [--tag <tag>] [--task-id <substr>]
                            [--iterations N] [--mock]
                            [--compare old.json new.json] [--verbose]
```

| Flag | Meaning |
|---|---|
| `--suite` | override `tasks/` dir (default: `./tasks`) |
| `--config` | override `.eval-config.yaml` path |
| `--out` | output dir for reports (default: `./reports`) |
| `--tag` | filter tasks by tag (e.g. `--tag smoke` or `--tag lifeline-L1`) |
| `--task-id` | filter tasks by id substring |
| `--iterations` | N per task (default: from config = 3) |
| `--mock` | use a fake `win32com.client` (no real PS needed) |
| `--compare` | diff two snapshots; produce regression report |
| `--verbose` | per-iteration progress output |

## Evaluation dimensions

See [`METHODOLOGY.md`](./METHODOLOGY.md) §2 for the full list. Short version:

1. **CLI Validation Precision** — right exit code (2/4) + right error message
2. **Exit Code Compliance** — every documented code (0/2/3/4/5) reachable
3. **COM Error Hint Fidelity** — known HRESULTs print the right hint
4. **Path Normalization** — `os.path.abspath` behavior, error message shape
5. **stdout/stderr Discipline** — success lines on stdout, progress/errors on stderr
6. **--wait-ready Protocol** — TCP poll, timeout, ConnectionRefusedError → exit 3
7. **Lifelines L1–L6 Compliance** — every hard-rule in `lifelines.md` enforced

## CI integration

Suggested gate (insert into your CI):

```bash
python3 scripts/run_eval.py --mock --iterations 3
python3 -c "
import json, sys
r = json.load(open('reports/summary.json'))
if r['weighted_pass_rate'] < 0.95: sys.exit(1)
if r['new_flaky'] > 0: sys.exit(2)
if any(t['id'].startswith('lifeline-') and t['pass_rate'] < 1.0 for t in r['tasks']):
    sys.exit(3)
"
```

Exit codes:
- `0` — all gates pass
- `1` — overall pass rate < 95%
- `2` — new flaky task
- `3` — Lifeline regression
- `4` — CLI / task / config error
- `5` — unexpected exception

## Limitations

See `METHODOLOGY.md` §6. Headline:

1. **Real PS is required for integration tasks.** The hermetic tasks (CLI
   validation, exit code matrix, COM error hints) run fine under `--mock`,
   but the happy-path integration case (load model + inject + change port)
   needs a real `Plant Simulation.exe` to validate end-to-end.
2. **Global state: COM singleton.** Plant Simulation is a COM singleton;
   the runner cannot run two integration tasks in parallel. See
   `lifelines.md` §2. The runner serializes integration cases by default.
3. **Side effects.** A successful integration run leaves a `Plant Simulation.exe`
   process running. The runner does NOT auto-kill it — the calling agent
   decides when to tear down. CI must do this explicitly.
4. **`--mock` covers validation tasks only.** The mock replaces
   `win32com.client.Dispatch` with a recorder. It validates the CLI
   surface and exit-code logic, not the COM wire protocol.

## Related

- Skill under test: [`skills/local-window-com-start-plant-simulation/`](../../skills/local-window-com-start-plant-simulation/)
- Hard rules (the contract): [`skills/local-window-com-start-plant-simulation/references/lifelines.md`](../../skills/local-window-com-start-plant-simulation/references/lifelines.md)
- CLI flag spec: [`skills/local-window-com-start-plant-simulation/references/cli-args.md`](../../skills/local-window-com-start-plant-simulation/references/cli-args.md)
- Sibling eval (downstream consumer of this skill):
  [`skills-evaluation/local-simtalk-execution-eval/`](../local-simtalk-execution-eval/)
