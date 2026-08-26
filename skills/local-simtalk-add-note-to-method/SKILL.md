---
name: local-simtalk-add-note-to-method
description: Add comment lines (single-line `-- ...` or block `{...}`) to a single Method object's `program` attribute in a loaded Plant Simulation model, via the `local-simtalk-execution` TCP transport. Use when the user wants to "add a comment to `<method-path>`", "document this method", "annotate the start of this SimTalk routine", "prepend a header comment", "append a footer comment", "add a trailing `-- note:` after a specific line". This skill targets **one Method at a time** and **preserves the original executable code** — it only inserts comment lines, never rewrites logic. It is the lightweight sibling of `local-simtalk-simtalk-note-adder` (which generates structured annotation blocks across many Methods). This skill depends on `local-simtalk-execution` for transport and never writes inside `.SimtalkClaude.*`.
---

# local-simtalk-add-note-to-method

Insert `(--)` comment lines into a single Method object's `program`
attribute on the running Plant Simulation server. The original executable
code is preserved byte-for-byte — only comment lines are added before,
after, or beside the existing code.

> **Scope.** One Method at a time. Use `local-simtalk-simtalk-note-adder`
> when you want a structured annotation pipeline across many Methods.

## When to use

- "Add a header comment to `<method-path>` explaining what it does"
- "Prepend `Author: ..., Date: ...` to this Method"
- "Append a `-- TODO: ...` line to `.CTU.Frame.Program`"
- "Add a trailing `-- note:` after a specific line"
- "Document a Method I just wrote"

Do **not** use this skill for:

- Batch-annotating many Methods (use `local-simtalk-simtalk-note-adder`)
- Changing executable code (this skill only inserts comments — use plain
  `simtalk_run` to rewrite logic, after backing up `program` first)
- Reading source without modifying it (use `local-simtalk-read-library`)
- Non-Method objects (the `program` attribute only exists on Method /
  Method-like objects)
- Writing inside `.SimtalkClaude.*` (off-limits by user convention)

## How it works

The skill is a thin wrapper around `simtalk_send.py run` that enforces
**type-check → read → backup → insert → write → readback → verify**
discipline so the original executable code is never lost and the change
is reversible.

### The 4 modes

| Mode | What it does | When to use |
|---|---|---|
| `prepend` | Insert comments **before** the existing code | Header / author / purpose block |
| `append` | Insert comments **after** the existing code | Footer / TODO / changelog |
| `replace` | Overwrite the entire `program` with new content | Full rewrite (use cautiously) |
| `trailing` | Append a trailing `-- ...` comment to the **last line** | Quick inline annotation |

All modes use `chr(10)` for real newlines. Direct `"\n"` inside a string
literal is interpreted as the two characters `\` and `n` by Plant
Simulation — see Quirk #1 below.

### Workflow

1. **Resolve the object** — `str_to_obj(<path>)` must not return `void`,
   and `obj.internalclasstype` must equal `"Method"`. Abort if either
   fails — the path is wrong or not loaded.
2. **Read current `program`** — store in `before`. This is your rollback
   target.
3. **Backup** — write `before` to `log/<path-sanitized>_original.txt`.
   Mandatory before any write.
4. **Compose the new program** — concatenate `before` with the new
   comment lines using `chr(10)` separators.
5. **Write** — `obj.program := <newProgram>` via `simtalk_run`.
6. **Readback** — read `obj.program` back; assert it equals what you
   wrote (modulo whitespace). If not, immediately restore from backup.
7. **Verify** — call `obj.execute` (or `simtalk_syntax` on the source)
   to confirm the new code compiles and still runs.

### Workflow: prepend example

```bash
python3 scripts/add_note.py \
    --path .CTU.Frame.Program \
    --mode prepend \
    --note "-- ============================================" \
            "-- Program method of .CTU.Frame" \
            "-- Modified on 2026-08-26 via simtalk_run" \
            "-- Purpose: declare a local counter variable" \
            "-- ============================================"
```

Result on `.CTU.Frame.Program`:

```
-- ============================================
-- Program method of .CTU.Frame
-- Modified on 2026-08-26 via simtalk_run
-- Purpose: declare a local counter variable
-- ============================================
var i := 1  -- local counter, starting at 1
```

## Usage

The helper script automates the read/backup/write/readback/verify loop:

```bash
# Prepend a header comment block to a Method
python3 scripts/add_note.py \
    --path .CTU.Frame.Program \
    --mode prepend \
    --note "-- header line 1" "-- header line 2"

# Append a footer / TODO
python3 scripts/add_note.py \
    --path .Models.Model.init \
    --mode append \
    --note "-- TODO: parameterize this in v2"

# Add a trailing comment to the last line of the Method
python3 scripts/add_note.py \
    --path .CTU.Frame.Program \
    --mode trailing \
    --note "  -- local counter, starting at 1"

# Replace mode (with automatic backup + verify)
python3 scripts/add_note.py \
    --path .CTU.Frame.Program \
    --mode replace \
    --note "-- full new body" "var i := 1"

# Restore the original program (un-do a previous edit)
python3 scripts/add_note.py --restore \
    --backup log/ctu_frame_program_original.txt \
    --path .CTU.Frame.Program
```

## Hard rules (Quirks)

| # | Rule | Why this skill cares |
|---|---|---|
| 1 | Use `chr(10)` for real newlines, not `"\n"` | Plant Simulation string literals interpret `"\n"` as two chars (`\` + `n`); only `chr(10)` produces a real line break |
| 2 | Always read `program` before writing — store in `before` | Without `before`, you cannot roll back |
| 3 | Write `before` to `log/<sanitized-path>_original.txt` before any mutation | Disk backup survives process restarts; in-memory only is not enough |
| 4 | `internalclasstype` must equal `"Method"` | Other object types may not have a writable `program` attribute |
| 5 | `simtalk_run` `result:"success"` with `log:"code execute failed..."` = soft failure | Double-check both fields (Quirk #7 from `local-simtalk-execution`) |
| 6 | After every write, read `obj.program` back | Socket never carries the value — `print + readlog` is the only feedback path |
| 7 | Always finish with `obj.execute` to verify the modified code still runs | A readback that "looks right" can still fail at runtime |
| 8 | Don't write inside `.SimtalkClaude.*` | User convention — out of scope |

## Why `chr(10)` instead of `"\n"`

This is the **single most common mistake** when first using this skill.
Plant Simulation's SimTalk parser treats double-quoted strings **literally**
— it does not interpret escape sequences. So:

```simtalk
-- WRONG: "\n" stays as the two characters '\' and 'n' inside the string
var s := "line1" + "\n" + "line2"
-- s == "line1\nline2"  (literal backslash-n, NOT a newline)

-- RIGHT: chr(10) is the actual newline character (ASCII 10)
var s := "line1" + chr(10) + "line2"
-- s == "line1" + LF + "line2"  (actual two-line string)
```

When `obj.program` is set to a string containing literal `\n`, the Plant
Simulation editor will show the source as one long line with `\` and `n`
characters visible — and the parser will see the `\n` as two separate
tokens (likely a syntax error).

## Limitations

- **One Method at a time.** To add notes to many Methods, run the script
  in a loop or use `local-simtalk-simtalk-note-adder` for structured
  batch annotation.
- **No transaction rollback.** If you prepend, append, and replace in
  three separate runs and the third fails, only the first two stick.
  Re-load from the on-disk backup.
- **`readlog` is degraded in v15+** — may not capture `print(...)`. If
  the marker doesn't appear after a write, fall back to the GUI Console
  (Window ribbon → Console).
- **Method body size** — `program` is a string, so multi-MB sources are
  technically writable but the TCP packet size becomes the practical
  limit. For large Methods, consider rewriting incrementally.
- **Cannot create new attributes** (modal trap — see
  `local-simtalk-execution/references/lifelines.md` §4).

## Key files

- `scripts/add_note.py` — CLI wrapper implementing read / backup /
  write / readback / verify / restore for one Method's `program`
  attribute.
- `examples/example.md` — the 2026-08-26 verification run on
  `.CTU.Frame.Program` that originally motivated this skill.
- `references/quirks.md` — full Quirk list with reproducible examples.

## Related skills

- `local-simtalk-execution` — the underlying TCP transport; consult its
  `references/lifelines.md` before doing anything non-standard.
- `local-simtalk-modify-object-atrribute` — for non-`program` attribute
  reads/writes (boolean / integer / real / string / dateTime / etc.).
- `local-simtalk-simtalk-note-adder` — for batch structured annotation
  of many Methods (heavier-weight pipeline).
- `local-simtalk-read-library` — read-only exploration to find which
  Methods exist under a given path before annotating them.
- `local-simtalk-get-class-inheritance` — figure out a Method's class
  hierarchy before assuming it has a `program` attribute.