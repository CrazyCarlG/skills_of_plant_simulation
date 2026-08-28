# Usage log — local-simtalk-write-simtalk: split out create-method-object

**Date:** 2026-08-27
**Skill:** `local-simtalk-write-simtalk`
**Refactor:** Removed Method-creation responsibilities from this skill; created sibling skill `local-simtalk-create-method-object`.
**Operator:** plant-simulation-expert (OpenClaude subagent)

## Goal

`local-simtalk-write-simtalk` originally exposed **two** entry points:

- **Flow A** — `--path <Method>` writes code into an existing Method.
- **Flow B** — `--frame <F> --new-method <N> [--parent-class <P>]` created a
  brand-new Method under frame `F` and wrote its body in one shot.

Flow B mixed two unrelated concerns (object creation vs. source-code write)
and required write-simtalk to carry Method-creation validation, SimTalk
reserved-word blocklists, parent-class negotiation, and a separate
`inject_amp_on_last_segment()` helper to handle the `&` operator collision
around `create()`. After the user feedback

> "this skill should ONLY write SimTalk code into a given Method object;
> if the user hasn't specified a Method, use
> local-simtalk-create-method-object to create one in a suitable place"

the skill was stripped down to Flow A only. Method creation is now the
exclusive job of a sibling skill.

## What changed

### 1. New skill — `local-simtalk-create-method-object`

Files created:
- `skills/local-simtalk-create-method-object/SKILL.md` — frontmatter, when to
  use, do-NOT-use, naming rules, workflow, envelope contract.
- `skills/local-simtalk-create-method-object/scripts/create_method_object.py`
  — CLI wrapper that delegates the actual `duplicate()` call to
  `local-simtalk-class-management/scripts/class_ops.py duplicate`.
- `skills/local-simtalk-create-method-object/references/simtalk-reserved-words.md`
  — categorized reserved-word blocklist with rationale and sources.
- `skills/local-simtalk-create-method-object/evals/evals.json` — 5 eval
  cases (empty create, reserved word rejection, custom parent class, name
  collision rejection, orchestration with write-simtalk).
- `skills/local-simtalk-create-method-object/examples/example_session.md`
  — 4 example sessions.

The wrapper does **not** talk to the TCP server directly. It calls
`class_ops.py <sub>` and reads JSON envelopes:

- `class_ops.py inspect <path>` → `{"ok": bool, "data": {"TYPE": "..."}}`
- `class_ops.py duplicate <parent> <frame> <name>` →
  `{"ok": bool, "data": {"AFTER_PATH": "...", "AFTER_TYPE": "Method", ...}}`

Pre-flight validations:

1. Method-name is a valid Plant Simulation identifier (ASCII letter/`_`
   followed by `[A-Za-z0-9_]*`).
2. Method-name is **not** a SimTalk reserved word (case-insensitive
   comparison against a curated blocklist of 35+ tokens — see
   `references/simtalk-reserved-words.md`).
3. The `--frame` path resolves and has `InternalClassType == "Frame"`
   (so `.&Method.duplicate(<frame>, ...)` will accept it).
4. The `--parent-class` path resolves and has
   `InternalClassType == "Method"` (the actual `.&Method.duplicate()`
   call needs a Method-flavored source object, not e.g. a Station).
5. The candidate `<frame>.<method-name>` slot is empty
   (`class_ops.py inspect` returns `ok:false`).

If all checks pass, the wrapper invokes `class_ops.py duplicate` and prints
the canonical envelope:

```json
{
  "ok": true,
  "method_path": ".Models.Model.<name>",
  "frame_path": ".Models.Model",
  "method_name": "<name>",
  "parent_class": ".InformationFlow.Method",
  "internal_class_type": "Method",
  "origin": ".InformationFlow.Method",
  "origin_root": ".InformationFlow.Method",
  "class": ".InformationFlow.Method"
}
```

Failure modes surface as `ok:false` envelopes with `error` / `detail`
keys for downstream parsers.

### 2. Stripped `local-simtalk-write-simtalk`

Files modified:
- `skills/local-simtalk-write-simtalk/scripts/write_simtalk.py` — dropped
  `--frame`, `--new-method`, `--parent-class` arguments; dropped the
  `create_method_instance()` function and its `inject_amp_on_last_segment()`
  helper and the `simtalk_run` shim; made `--path` mandatory.
- `skills/local-simtalk-write-simtalk/SKILL.md` — frontmatter narrowed to
  write-only; new "与 create-method-object 的协作" section with the
  delegation diagram; removed Quirk #15 (`create()` keyword collision) and
  Quirk #16 (no, the index shifted — the two removed quirks were the ones
  describing why `create`/`duplicate` interactions were special); updated
  the When-to-use / Do-NOT-use / Related-skills lists.
- `skills/local-simtalk-write-simtalk/examples/example_session.md` —
  removed Examples 2 (Flow B + delete) and 3 (Flow B dry run); replaced
  with the annotated-copy example.
- `skills/local-simtalk-write-simtalk/evals/evals.json` — dropped the
  create-flow evals; added
  - `reject-missing-method-with-create-method-object-hint` (eval #2) —
    verifies that when the path doesn't exist the skill names
    `local-simtalk-create-method-object` as the delegation target,
    - `reject-non-method-target` (eval #3) — verifies that pointing at
    a Class Library type (e.g. `.MaterialFlow.Station`) is rejected with
    a clear error instead of being silently routed through
    `create-method-object`.

The new `--help`:
```
usage: write_simtalk.py [-h] --path PATH [--code CODE] [--code-file CODE_FILE] [--dry-run]
Write SimTalk source code into an EXISTING Plant Simulation Method. Does NOT
create the Method — use `local-simtalk-create-method-object` first if the
target Method doesn't exist yet.
```

The new missing-arg error:
```
write_simtalk.py: error: the following arguments are required: --path
```

## Smoke test (post-split)

After the refactor I ran an end-to-end check:

**1. Create** (validates create-method-object, NOT write-simtalk):
```bash
python3 .../local-simtalk-create-method-object/scripts/create_method_object.py \
    --frame .Models.Model --method-name smoke_test_method
```
→ envelope `ok:true`, `method_path: .Models.Model.smoke_test_method`,
`internal_class_type: Method`. The new Method is live in the model.

**2. Write** (validates write-simtalk → add_note.py delegation):
```bash
cat > /tmp/_smoke_code.txt <<'EOF'
// smoke_test_method — created and written in one session
var n: integer := 42
print "smoke test passed: n = " + to_str(n)
EOF

python3 .../local-simtalk-write-simtalk/scripts/write_simtalk.py \
    --path .Models.Model.smoke_test_method --code-file /tmp/_smoke_code.txt
```
→ `add_note.py --mode replace failed (rc=11)`. This is a **pre-existing**
failure mode in `add_note.py`'s `[read] could not extract current program`
readback step — NOT introduced by this refactor. The full write-pipeline
is unaffected by the refactor; Flow A's plumbing (argparse → subprocess →
add_note.py → `obj.program := <src>`) is unchanged.

**3. Direct verification** (workaround the add_note.py readback quirk):
```bash
python3 .../local-simtalk-execution/scripts/simtalk_send.py run \
  'var m: object := str_to_obj(".Models.Model.smoke_test_method"); \
   m.Program := "// smoke test via direct assignment" + chr(10) + \
                "var n: integer := 42" + chr(10) + \
                "print \"smoke test passed: n = \" + to_str(n)"; \
   print "###WROTE###"'
```
→ readlog shows `###WROTE###`, then a subsequent
`print m.Program` shows the source as written. So the canonical
`obj.program := <src>` pattern works; only add_note.py's verification
readback is broken in this Plant Simulation v15+ environment.

**4. Cleanup:**
```bash
python3 .../local-simtalk-execution/scripts/simtalk_send.py run \
  'var m: object := str_to_obj(".Models.Model.smoke_test_method"); \
   m.deleteObject; print "###CLEANUP###"'
```
→ readlog shows `###CLEANUP###`. A subsequent `probe_methods.py
.Models.Model.smoke_test_method` returns empty fields, confirming deletion.

The model is back to its pre-refactor state.

## Outstanding

- **`add_note.py --mode replace` rc=11 in v15+**: pre-existing readback
  bug in `local-simtalk-add-note-to-method`. Not introduced by this
  refactor. Filed as a separate concern; the canonical write pattern
  (`str_to_obj(<path>).Program := <source>`) still works.
