# Contributing to the eval suite

> How to add a new task, new grader predicate, or new category.
> Read `METHODOLOGY.md` first — it defines the contracts.

## Adding a new task

1. **Pick the right category file** under `tasks/`. If your task covers a
   new dimension (e.g., a new exit code trigger or a new mock fault
   type), create a new file `NN-<name>.json` and update
   `METHODOLOGY.md` §3.1.

2. **Write the task JSON** per the schema (`METHODOLOGY.md` §3.2).

   Quick checklist:
   - `id` is unique across the whole suite
   - `args` is a list (use `[]` for `--help`-style tasks)
   - `mock: true` for hermetic tasks; `mock: false` only when you need
     real COM (and only after confirming the CI env has PS installed)
   - `timeout` is realistic (validation: 3-5s; integration: 30s+;
     `--wait-ready` must be ≤ `timeout`)
   - `expected` declares at least one predicate
   - `tags` includes at least one of: `smoke`, `regression`,
     `lifeline-L1`...`lifeline-L6`, `exit-2`, `exit-3`, `exit-4`,
     `hermetic`, `integration`, `com-error-0x80040154`, etc.
   - Cite the source in `tags` (e.g., `cli-args-§exit-codes`,
     `lifelines-§3`)

3. **Be specific in `expected`** — `stderr_includes: ["regsvr32"]`
   survives refactors better than `exit_code: 3` alone. The grader
   combines predicates with AND.

4. **For integration tasks**, include a `mock_setup` block ONLY IF you need
   the mock to inject a fault. Default mock setup returns success for
   everything. Tasks that need a fault should set `mock: true` and
   describe the fault in `expected.mock_call_sequence` or via
   `mock_setup` (TBD in §3.4 once implemented).

5. **Run the suite** locally before opening a PR:
   ```bash
   python3 scripts/run_eval.py --tag <your-new-tag> --mock
   python3 scripts/run_eval.py --tag <your-new-tag> --iterations 3
   ```
   The `--mock` run confirms the JSON parses and the grader logic is
   right. The real run confirms real PS behaves as expected (if
   applicable).

6. **Confirm pass rate ≥ 95%** for the new task across N=3 runs.

## Adding a new grader predicate

1. Add the field to `eval/task.py::Expected` dataclass.
2. Add a `from_dict` mapping for it.
3. Add the predicate check in `eval/grader.py::grade()`.
4. Add at least one task in the suite that exercises it.
5. Update `METHODOLOGY.md` §3.3.

## Adding a new failure bucket

1. Add a constant in `eval/grader.py` (e.g., `BUCKET_NEW_FAILURE`).
2. Add a clause in `_bucket_for()`.
3. Update `METHODOLOGY.md` §5.

## Schema validation

A task JSON that fails to load raises `ValueError` at `Task.from_dict`
time. Common mistakes:
- Missing `expected` predicate → "must declare at least one predicate"
- `args` not a list → "must be a list of strings"
- `mock: true` but no `mock_call_sequence` and no fault expected → runner
  warns (mock call sequence empty is OK; it just won't be checked)
- `timeout` < 1 → "must be ≥ 1"

## PR checklist

- [ ] Task loads (no `ValueError` on load)
- [ ] `--mock` run: pass rate ≥ 95% with `--tag <new>`
- [ ] Real run (if integration): pass rate ≥ 95% with `--tag <new> --iterations 3`
- [ ] `expected` is specific (not just `exit_code: N` alone)
- [ ] `tags` cites the source (cli-args / lifelines / log entry)
- [ ] `METHODOLOGY.md` updated if you added a new dimension
- [ ] Lifeline-related tasks weighted ≥ 2.0 (so regressions hurt the gate)

## Don't

- **Don't** add integration tasks that depend on a specific model
  state. The suite is hermetic by default. Only mark `mock: false` if the
  test is specifically about COM wire behavior.
- **Don't** rely on `wall_time_max_ms` as the *primary* success signal —
  it's a flake magnet. Use it as a tiebreaker.
- **Don't** add tasks that mutate global state without documenting it in
  `tags` (e.g., `tags: ["side-effect", "launches-ps-process"]`).
- **Don't** add tasks with `mock: false` if the host has no PS installed
  — the runner will mark the task `inconclusive` and skip it, polluting
  the pass rate.
