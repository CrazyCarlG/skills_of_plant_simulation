# local-window-com-start-plant-simulation — Evaluation Summary

- **Timestamp**: `2026-09-18T05:43:50Z`
- **Iterations per task**: 5
- **Overall weighted pass rate**: **100.0%** (205/205) (threshold 95%)
- **Flaky tasks**: 0
- **Slow tasks**: 0
- **Over-budget tasks** (median > per-task wall_time_max_ms, info-only): 0
- **Hard-gate regressions** (lifeline / exit-code): 0
- **CI gate**: exit code **0** (PASS)

## Failure bucket histogram

| Bucket | Count |
|---|---:|
| _(no failures)_ | 0 |

## Per-task pass rates

| Task ID | Category | N | Pass | Pass rate | Median ms | Budget ms | Over | CI95 | Flag |
|---|---|--:|--:|--:|--:|--:|:-:|---|---|
| `cli-001-missing-model` | cli-validation | 5 | 5 | 100% | 236 | 400 | no | [57%, 100%] | — |
| `cli-002-missing-simtalkclaudefile` | cli-validation | 5 | 5 | 100% | 224 | 400 | no | [57%, 100%] | — |
| `cli-003-port-zero` | cli-validation | 5 | 5 | 100% | 227 | 400 | no | [57%, 100%] | — |
| `cli-004-port-65536` | cli-validation | 5 | 5 | 100% | 220 | 400 | no | [57%, 100%] | — |
| `cli-005-port-abc` | cli-validation | 5 | 5 | 100% | 221 | 400 | no | [57%, 100%] | — |
| `cli-006-model-not-found` | cli-validation | 5 | 5 | 100% | 219 | 400 | no | [57%, 100%] | — |
| `cli-007-simtalkclaudefile-not-found` | cli-validation | 5 | 5 | 100% | 219 | 400 | no | [57%, 100%] | — |
| `com-001-hresult-class-not-registered` | com-errors | 5 | 5 | 100% | 240 | 350 | no | [57%, 100%] | — |
| `com-002-hresult-singleton-held` | com-errors | 5 | 5 | 100% | 247 | 350 | no | [57%, 100%] | — |
| `com-003-hresult-disp-e-exception` | com-errors | 5 | 5 | 100% | 219 | 350 | no | [57%, 100%] | — |
| `com-004-unknown-hresult` | com-errors | 5 | 5 | 100% | 222 | 350 | no | [57%, 100%] | — |
| `model-001-loadmodel-called` | model-load | 5 | 5 | 100% | 223 | 350 | no | [57%, 100%] | — |
| `model-002-settrustmodels-called` | model-load | 5 | 5 | 100% | 215 | 350 | no | [57%, 100%] | — |
| `model-003-setvisible-called` | model-load | 5 | 5 | 100% | 219 | 350 | no | [57%, 100%] | — |
| `model-004-abspath-applied` | model-load | 5 | 5 | 100% | 218 | 350 | no | [57%, 100%] | — |
| `inject-001-loadobjectas-called` | injection | 5 | 5 | 100% | 215 | 350 | no | [57%, 100%] | — |
| `inject-002-loadobjectas-before-port` | injection | 5 | 5 | 100% | 216 | 350 | no | [57%, 100%] | — |
| `inject-003-quote-escaping` | injection | 5 | 5 | 100% | 220 | 350 | no | [57%, 100%] | — |
| `port-001-default-50007` | port-change | 5 | 5 | 100% | 227 | 400 | no | [57%, 100%] | — |
| `port-002-custom-port` | port-change | 5 | 5 | 100% | 216 | 400 | no | [57%, 100%] | — |
| `port-003-executesimtalk-called-twice` | port-change | 5 | 5 | 100% | 226 | 400 | no | [57%, 100%] | — |
| `wait-001-default-skipped` | wait-ready | 5 | 5 | 100% | 227 | 350 | no | [57%, 100%] | — |
| `wait-002-wait-ready-1-busy-port` | wait-ready | 5 | 5 | 100% | 2241 | 2700 | no | [57%, 100%] | — |
| `wait-003-wait-ready-0-explicit` | wait-ready | 5 | 5 | 100% | 231 | 350 | no | [57%, 100%] | — |
| `wait-004-wait-ready-negative-skipped` | wait-ready | 5 | 5 | 100% | 214 | 350 | no | [57%, 100%] | — |
| `wait-005-progress-on-stderr` | wait-ready | 5 | 5 | 100% | 2247 | 5000 | no | [57%, 100%] | — |
| `pid-001-flag-printed` | print-pid | 5 | 5 | 100% | 780 | 1000 | no | [57%, 100%] | — |
| `pid-002-warning-when-no-ps` | print-pid | 5 | 5 | 100% | 728 | 1000 | no | [57%, 100%] | — |
| `pid-003-not-requested` | print-pid | 5 | 5 | 100% | 226 | 1000 | no | [57%, 100%] | — |
| `lifeline-L1-inject-before-port` | lifelines | 5 | 5 | 100% | 227 | 400 | no | [57%, 100%] | — |
| `lifeline-L3-no-message-box-default` | lifelines | 5 | 5 | 100% | 235 | 400 | no | [57%, 100%] | — |
| `lifeline-L3-allow-message-box` | lifelines | 5 | 5 | 100% | 222 | 400 | no | [57%, 100%] | — |
| `lifeline-L4-abspath-applied` | lifelines | 5 | 5 | 100% | 230 | 400 | no | [57%, 100%] | — |
| `lifeline-L4-abspath-pslib` | lifelines | 5 | 5 | 100% | 237 | 400 | no | [57%, 100%] | — |
| `lifeline-L6-pywin32-required` | lifelines | 5 | 5 | 100% | 245 | 400 | no | [57%, 100%] | — |
| `exit-code-0-happy-mock` | exit-codes | 5 | 5 | 100% | 247 | 350 | no | [57%, 100%] | — |
| `exit-code-2-bad-args` | exit-codes | 5 | 5 | 100% | 263 | 350 | no | [57%, 100%] | — |
| `exit-code-3-com-error` | exit-codes | 5 | 5 | 100% | 249 | 350 | no | [57%, 100%] | — |
| `exit-code-3-socket-timeout` | exit-codes | 5 | 5 | 100% | 2256 | 2700 | no | [57%, 100%] | — |
| `exit-code-4-file-not-found` | exit-codes | 5 | 5 | 100% | 214 | 350 | no | [57%, 100%] | — |
| `exit-code-5-uncaught` | exit-codes | 5 | 5 | 100% | 228 | 350 | no | [57%, 100%] | — |

## Per-task details

See `per-task/<task-id>.md` for raw runs and verdict reasoning.
