# local-simtalk-execution — Evaluation Summary

- **Timestamp**: `2026-09-18T06:57:05Z`
- **Iterations per task**: 3
- **Overall weighted pass rate**: **67.3%** (65/96)
- **Flaky tasks**: 11
- **Slow tasks** (info-only, type-budget-based): 2
- **Over-budget tasks** (info-only, per-task budget): 0
- **Quirk regressions**: 1
- **CI gate**: exit code **3** (FAIL)

## Failure bucket histogram

| Bucket | Count |
|---|---:|
| `compile_error` | 19 |
| `syntax_error` | 9 |
| `unexpected_success` | 3 |

## Per-task pass rates

| Task ID | Type | N | Pass | Pass rate | Median ms | Budget ms | Over | σ | CI95 | Flag |
|---|---|--:|--:|--:|--:|--:|:-:|--:|---|---|
| `conn-001-ping` | ping | 3 | 3 | 100% | 413 | 2000 | no | 3 | [44%, 100%] | — |
| `conn-002-syntax-smoke` | simtalk_syntax | 3 | 3 | 100% | 430 | 3000 | no | 26 | [44%, 100%] | — |
| `conn-003-run-smoke` | simtalk_run | 3 | 3 | 100% | 427 | 5000 | no | 17 | [44%, 100%] | — |
| `conn-004-readlog-q002` | readlog | 3 | 1 | 33% | 404 | 5000 | no | 26 | [6%, 79%] | flaky |
| `syntax-001-valid-var` | simtalk_syntax | 3 | 3 | 100% | 411 | 3000 | no | 9 | [44%, 100%] | — |
| `syntax-002-valid-control-flow` | simtalk_syntax | 3 | 3 | 100% | 435 | 3000 | no | 31 | [44%, 100%] | — |
| `syntax-003-valid-param-default` | simtalk_syntax | 3 | 3 | 100% | 392 | 3000 | no | 13 | [44%, 100%] | — |
| `syntax-004-invalid-byval` | simtalk_syntax | 3 | 0 | 0% | 426 | 3000 | no | 14 | [0%, 56%] | flaky |
| `syntax-005-invalid-byref-default` | simtalk_syntax | 3 | 0 | 0% | 439 | 3000 | no | 8 | [0%, 56%] | flaky |
| `syntax-006-invalid-name-clash` | simtalk_syntax | 3 | 0 | 0% | 446 | 3000 | no | 15 | [0%, 56%] | flaky |
| `run-001-print-string` | simtalk_run | 3 | 3 | 100% | 447 | 8000 | no | 27 | [44%, 100%] | — |
| `run-002-arithmetic` | simtalk_run | 3 | 3 | 100% | 416 | 8000 | no | 19 | [44%, 100%] | — |
| `run-003-quirk7-runtime-unknown-identifier` | simtalk_run | 3 | 3 | 100% | 415 | 8000 | no | 11 | [44%, 100%] | — |
| `run-004-compile-error-division-by-zero` | simtalk_run | 3 | 0 | 0% | 430 | 8000 | no | 14 | [0%, 56%] | flaky |
| `run-005-return-with-type` | simtalk_run | 3 | 3 | 100% | 404 | 8000 | no | 50 | [44%, 100%] | — |
| `run-006-list-dim` | simtalk_run | 3 | 3 | 100% | 424 | 10000 | no | 28 | [44%, 100%] | — |
| `quirk-005-retsult-stale` | simtalk_syntax | 3 | 3 | 100% | 397 | 3000 | no | 10 | [44%, 100%] | — |
| `quirk-006-data-field-ignored` | simtalk_run | 3 | 3 | 100% | 422 | 8000 | no | 11 | [44%, 100%] | — |
| `quirk-007-soft-failure-detected` | simtalk_run | 3 | 3 | 100% | 420 | 8000 | no | 20 | [44%, 100%] | — |
| `quirk-013-unknown-type-hangs` | simtalk_run | 3 | 3 | 100% | 5214 | 6000 | no | 21 | [44%, 100%] | — |
| `quirk-readlog-q002-stdout-valid` | readlog | 3 | 1 | 33% | 446 | 5000 | no | 16 | [6%, 79%] | flaky |
| `list-001-dim-correct` | simtalk_run | 3 | 3 | 100% | 410 | 10000 | no | 5 | [44%, 100%] | — |
| `list-002-length-unknown-identifier` | simtalk_run | 3 | 3 | 100% | 396 | 8000 | no | 25 | [44%, 100%] | — |
| `list-003-literal-assign-soft-fail` | simtalk_run | 3 | 3 | 100% | 407 | 8000 | no | 14 | [44%, 100%] | — |
| `frame-001-delimiter-default` | ping | 3 | 3 | 100% | 452 | 2000 | no | 27 | [44%, 100%] | — |
| `frame-002-eof-mode-hangs` | simtalk_syntax | 3 | 3 | 100% | 5204 | 6000 | no | 10 | [44%, 100%] | slow |
| `frame-003-missing-end-delimiter` | simtalk_syntax | 3 | 0 | 0% | 185 | 6000 | no | 12 | [0%, 56%] | flaky |
| `frame-004-fixed-mode-misframing` | simtalk_syntax | 3 | 3 | 100% | 5231 | 6000 | no | 16 | [44%, 100%] | slow |
| `modal-001-prompt` | simtalk_run | 3 | 0 | 0% | 8421 | 10000 | no | 26 | [0%, 56%] | flaky |
| `modal-002-infoBox` | simtalk_run | 3 | 0 | 0% | 8459 | 10000 | no | 15 | [0%, 56%] | flaky |
| `modal-003-undeclared-attr` | simtalk_run | 3 | 0 | 0% | 8447 | 10000 | no | 18 | [0%, 56%] | flaky |
| `modal-004-promptList1` | simtalk_run | 3 | 0 | 0% | 8438 | 10000 | no | 18 | [0%, 56%] | flaky |

## Per-task details

See `per-task/<task-id>.md` for raw runs and verdict reasoning.
