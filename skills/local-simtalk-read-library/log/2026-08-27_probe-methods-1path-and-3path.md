# Usage log — local-simtalk-read-library: probe_methods (1 path + 3 paths)

**Date:** 2026-08-27
**Skill:** `local-simtalk-read-library`
**Target:** `.Models.Model.Method` (Method instance), `.MaterialFlow.EventController` (EventController class), `.InformationFlow.Method` (Method class)
**Mode / Action:** `probe_methods.py` (batch size 8, marker-tagged readlog extraction)
**Operator:** plant-simulation-expert (OpenClaude subagent)

## Goal

Verify the read-library skill can dump Method source code via `&o.Program` plus
metadata (`Encrypted` / `HasSyntaxError` / `NumInExecution`), and that it handles
non-Method objects gracefully (empty fields, no crash).

## Steps

### Test 1 — single Method instance

```bash
cat > /tmp/method_paths.txt <<'EOF'
.Models.Model.Method
EOF
python3 skills/local-simtalk-read-library/scripts/probe_methods.py \
  /tmp/method_paths.txt /tmp/methods_raw.tsv --no-infobox
```

Returned row:
```json
{
  "path": ".Models.Model.Method",
  "name": "Method",
  "type": "Method",
  "encrypted": "false",
  "has_syntax_error": "false",
  "num_in_execution": "0",
  "program_len": 70,
  "program": "-- method — prints 1..10\nfor var i := 1 to 10\n    print to_str(i)\nnext"
}
```

- `program` captured verbatim, with real newlines (`\n` = LF, not literal backslash-n) — confirms LIB-3 / Quirk 3 (`log.replace("\\n","\n")` decoder works).
- `program_len == 70` matches the string length: 70 chars including the embedded newlines.
- `encrypted=false`, `has_syntax_error=false`, `num_in_execution=0` — all consistent with a freshly-loaded model.

### Test 2 — three paths (Method instance + EventController class + Method class)

```bash
cat > /tmp/method_paths2.txt <<'EOF'
.Models.Model.Method
.MaterialFlow.EventController
.InformationFlow.Method
EOF
python3 skills/local-simtalk-read-library/scripts/probe_methods.py \
  /tmp/method_paths2.txt /tmp/methods_raw2.tsv --no-infobox
```

Returned rows:

| Path | name | type | encrypted | has_syntax_error | num_in_execution | program_len | program |
|---|---|---|---|---|---|---|---|
| `.Models.Model.Method` | `Method` | `Method` | `false` | `false` | `0` | 70 | full body |
| `.MaterialFlow.EventController` | `EventController` | `EventController` | `false` | `""` | `""` | 0 | `""` |
| `.InformationFlow.Method` | `""` | `""` | `""` | `""` | `""` | 0 | `""` |

Observations:
- `.MaterialFlow.EventController` is an **EventController class object**, not a Method.
  `&o.Encrypted` returns `false` (the attribute exists), but `HasSyntaxError` /
  `NumInExecution` / `Program` return empty strings — those attributes don't apply
  to non-Method objects. The probe captured the partial row instead of crashing.
- `.InformationFlow.Method` (the **class itself** rather than an instance) is even more
  bare — even `Name` and `InternalClassType` come back empty. The probe still
  completed cleanly without aborting.

## Result

Both runs wrote valid TSV with the documented 8-field schema. The Method instance's
source was captured byte-perfect. Non-Method objects degrade gracefully to empty
fields rather than throwing.

## Verdict

PASS — 2/2 calls clean. Skill is robust to mixed batches (real Methods + non-Methods).

## What this run validated / learned

- **`.Models.Model.Method` is the only real Method source in this minimal model.** Its body is a 70-char `for i := 1 to 10 print to_str(i)` — a sensible "demo placeholder". Downstream write-simtalk can safely overwrite this Method (or duplicate it elsewhere) without disrupting the model.
- **The probe gracefully returns empty fields for non-Method objects.** This is critical for batch use — if you accidentally feed `EventController` paths to `probe_methods.py`, it won't crash; you just get empty metadata. **Recommended pre-step**: filter `paths.txt` by `type == "Method"` (use `local-simtalk-get-folder-tree`'s JSON for this) to avoid noise rows like the second/third in Test 2.
- **Source code captured verbatim, LF-correct.** The program string has real newlines, confirming the JSON-unescape decoder (`log.replace("\\n", "\n")`) works as designed.
- **`encrypted=false` on the user Method** — safe to overwrite without `decrypt` first.
- **No syntax errors anywhere** — `has_syntax_error` is empty/`false` across all rows, so we can `obj.program := ...` safely.
- **`--no-infobox` (last arg) works.** No GUI chatter in either run.
