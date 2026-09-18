# Contributing to the eval suite

> How to add a new task, new grader predicate, or new category.
> Read `METHODOLOGY.md` first — it defines the contracts.

## Adding a new task

1. **Pick the right category file** under `tasks/`. If your task covers a new
   dimension (e.g., new `type` or new lifecycle phase), create a new file
   `NN-<name>.json` and update `METHODOLOGY.md` §3.1.

2. **Write the task JSON** per the schema (`METHODOLOGY.md` §3.2).

   Quick checklist:
   - `id` is unique across the whole suite
   - `type` is one of the whitelist (`ping` / `simtalk_syntax` / `simtalk_run` / `readlog`)
   - `code` is set for syntax/run tasks; use `\n` for line breaks
   - `timeout` is realistic (`simtalk_run` ≥ 10s; `simtalk_syntax` 5-10s; `ping` 3-5s)
   - `expected` declares at least one predicate
   - `tags` includes at least one of: `smoke`, `regression`, `quirk-N`,
     `expected_timeout`, `modal-trap`, `v15`, `v9-R5`, … (cite source)
   - If testing an off-whitelist `type` (Quirk #13), set `mode: "raw_socket"`
     and provide `raw_data` (must end in `||END||`)

3. **Be specific in `expected`** — `result_excludes: ["hasError"]` survives
   schema drift better than `exit_code: 0` alone. The grader combines
   predicates with AND.

4. **Cite the source** in `tags`. Examples:
   - `lifelines-§6` — references the hard-rules doc
   - `v9-R5` — references a specific iteration in `skills/.../log/`
   - `example.md-§3` — references the worked example

5. **Run the suite** locally before opening a PR:
   ```bash
   python3 scripts/run_eval.py --tag <your-new-tag> --mock
   python3 scripts/run_eval.py --tag <your-new-tag> --iterations 5
   ```
   The mock run confirms the JSON parses and the grader logic is right. The
   real run confirms the server behaves as expected.

6. **Confirm pass rate ≥ 95%** for the new task across N=5 runs.

## Adding a new grader predicate

1. Add the field to `eval/task.py::Expected` dataclass.
2. Add a `from_dict` mapping for it.
3. Add the predicate check in `eval/grader.py::grade()`.
4. Add at least one task in the suite that exercises it.
5. Update `METHODOLOGY.md` §3.3.

## Adding a new failure bucket

1. Add a constant in `eval/grader.py` (e.g., `BUCKET_NEW_FAILURE`).
2. Add a clause in `_bucket_for()`.
3. Update `METHODOLOGY.md` §2.7.

## Schema validation

A task JSON that fails to load raises `ValueError` at `Task.from_dict` time.
Common mistakes:
- Missing `expected` predicate → "must declare at least one predicate"
- `code` missing for syntax/run → "requires 'code' field"
- `type` outside whitelist → "not in whitelist"
- `mode: "raw_socket"` without `raw_data` → "requires 'raw_data'"

## PR checklist

- [ ] Task loads (no `ValueError` on load)
- [ ] Mock run: pass rate ≥ 95% with `--tag <new>`
- [ ] Real run: pass rate ≥ 95% with `--tag <new> --iterations 5`
- [ ] `expected` is specific (not just `exit_code: 0`)
- [ ] `tags` cites the source
- [ ] `METHODOLOGY.md` updated if you added a new dimension
- [ ] Quirk-related tasks weighted ≥ 3.0 (so regressions hurt the gate)

## Don't

- **Don't** add tasks that depend on stateful model setup (e.g., assume
  a specific `.Models.Model.M` exists). This suite is hermetic.
- **Don't** add tasks with `mock: false` and a `fixture` field — fixtures are
  for offline dev only.
- **Don't** rely on `wall_time_max_ms` as the *primary* success signal — it's
  a flake magnet. Use it as a tiebreaker.
- **Don't** add tasks that mutate global state without documenting it in `tags`
  (e.g., `tags: ["side-effect"]`).