---
name: local-simtalk-add-note-to-method
description: Add comment lines (single-line `-- ...` / `//`, or block `/* ... */`) to a single Method object's `program` attribute in a loaded Plant Simulation model, via the `local-simtalk-execution` TCP transport. Use when the user wants to "add a comment to `<method-path>`", "document this method", "annotate the start of this SimTalk routine", "prepend a header comment", "append a footer comment", "add a trailing `-- note:` after a specific line". This skill targets **one Method at a time** and **preserves the original executable code** — it only inserts comment lines, never rewrites logic. It is the lightweight sibling of `local-simtalk-simtalk-note-adder` (which generates structured annotation blocks across many Methods). This skill depends on `local-simtalk-execution` for transport and never writes inside `.SimtalkClaude.*`.
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

## Note language (match the user)

The NOTE block's language must match the language of the user's request:

- **English request** → English NOTE block
- **Chinese request** → Chinese NOTE block
- **Mixed request** → mirror the user's mix
- **Explicit override** ("用英文" / "用中文注释" / "in English please")
  wins over the default matching
- **Don't translate an existing NOTE** without an explicit ask — only
  the new lines you are adding follow the language-matching rule
- **Code identifiers stay verbatim** — method paths (e.g.
  `simtalk_hasError`), socket fields (`action_result.result`), SimTalk
  keywords (`if`, `return`), and quoted contract literals (`' hasError ：'`,
  `'has no Error'`, `success`, `failed`) are **never** translated
- **Section headers / metadata lines** (e.g. `-- Method path :`,
  `-- Purpose`, `-- Parameters`, `-- Side effects`) may be written
  bilingual when the user mixes languages or asks for both, but pick
  one side cleanly when the request is single-language

This rule was added after the user requested:

> 如果用户用英文发文，就通过英文注释，如果用中文，则用中文注释

## Pre-annotation workflow (read context first)

Before composing a NOTE block for any Method, build context. Annotating
without library context produces NOTE blocks that describe the function
**signature** but miss the actual call graph, side-effect consumers, and
literal-contract strings — making the NOTE decorative rather than useful
for debugging.

**Required pre-steps:**

1. **Read the Plant Simulation knowledge base** at
   `/root/skills_of_plant_simulation/01-plantsimulation-knowledge/01-plant-simulation-help/`
   for the relevant domain — SimTalk comment syntax (`--`/`//`/`/* */`),
   Method object attributes (`Program` / `HasSyntaxError` / `Encrypted`
   / `NumInExecution`), `str_to_obj` / `obj.execute` lifecycle, etc.
2. **Run `local-simtalk-read-library`** to dump the current model's
   Method inventory + verbatim source:
   ```bash
   python3 ../local-simtalk-read-library/scripts/read_library.py \
     --no-infobox --tree-depth 5 \
     --out /tmp/anno_prelude_library.json
   ```
   This tells you which methods exist, what the original bodies look
   like (so you can verify they're preserved verbatim), which methods
   have syntax errors or are encrypted, and the cross-method call graph.
3. **Identify direct callers** of the target method (grep the dump for
   the target's name — every method whose `program` contains it is a
   direct caller). Read those callers' bodies to see how they consume
   the return value and which shared dictionaries (`action_result`,
   `&simtalkcode`, `current.~.SocketServer/SocketClient`) they read.
4. **Read the target's original `program`** from the dump — you'll
   re-append it byte-for-byte after the NOTE, so every byte of the
   original must be preserved.
5. **Compose the NOTE** mentioning: actual caller chain (not generic
   "called by Run_Simutalk" if Run_Simutalk isn't actually a caller),
   actual return-value contract (literal strings downstream matches
   against), and actual side-effect consumers.

**Why:** prior annotations lacked context — describing
`simtalk_hasError` as a free-standing syntax checker when in fact it is
**only** called from `get_simtalk_hasError` (a wrapper dispatched by
`SocketServer.m_callback`), and its `action_result` writes are read by
sibling methods in `SimtalkAction`. The user pointed this out:
"你缺乏一些plant simulation的知识和当前对library的了解". Reading the
library first lets the NOTE mention real callers, real side-effect
consumers, and the exact dispatch protocol — making the doc useful for
future debugging.

**How to apply:** every time a new annotation request lands on
`.SimtalkClaude2.*` (or any other model path), run the 5-step workflow
above before composing the NOTE. For the payload size constraint that
often hits during step 5, see "Hard rules (Quirks)" #11 below — single
NOTE payload must stay ≤ ~2 KB, otherwise split into chunked writes.

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
3. **Backup** — write `before` to `code_log/<path-sanitized>_original.txt`.
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
    --note "/*" \
            "============================================" \
            "-- Program method of .CTU.Frame" \
            "-- Modified on 2026-08-26 via simtalk_run" \
            "-- Purpose: declare a local counter variable" \
            "============================================" \
            "*/"
```

Result on `.CTU.Frame.Program`:

```
/*
============================================
-- Program method of .CTU.Frame
-- Modified on 2026-08-26 via simtalk_run
-- Purpose: declare a local counter variable
============================================
*/
var i := 1  -- local counter, starting at 1
```

> **Note**: lines that begin with `--` inside `add_note.py --note` still
> trip argparse (Quirk #10) — `--note "-- foo"` works because `--` here
> is preceded by a literal space, but `--note "-- foo" "-- bar"` may
> confuse the parser. For notes containing `--` lines, use the
> `/* ... */` pattern above (only the literal tokens `/*` and `*/` are
> passed, no `--` tokens needed) or bypass `add_note.py` and write the
> SimTalk payload directly via `socket_client.py` as shown in
> `examples/example.md`.

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
    --backup code_log/ctu_frame_program_original.txt \
    --path .CTU.Frame.Program
```

## Hard rules (Quirks)

| # | Rule | Why this skill cares |
|---|---|---|
| 1 | Use `chr(10)` for real newlines, not `"\n"` | Plant Simulation string literals interpret `"\n"` as two chars (`\` + `n`); only `chr(10)` produces a real line break |
| 2 | Always read `program` before writing — store in `before` | Without `before`, you cannot roll back |
| 3 | Write `before` to `code_log/<sanitized-path>_original.txt` before any mutation | Disk backup survives process restarts; in-memory only is not enough |
| 4 | `internalclasstype` must equal `"Method"` | Other object types may not have a writable `program` attribute |
| 5 | `simtalk_run` `result:"success"` with `log:"code execute failed..."` = soft failure | Double-check both fields (Quirk #7 from `local-simtalk-execution`) |
| 6 | After every write, read `obj.program` back | Socket never carries the value — `print + readlog` is the only feedback path |
| 7 | Always finish with `obj.execute` to verify the modified code still runs | A readback that "looks right" can still fail at runtime |
| 8 | Don't write inside `.SimtalkClaude.*` | User convention — out of scope |
| 9 | Decoration lines in a NOTE block (e.g. `=====`, `-----`) MUST either start with `--` / `//` or sit **inside** a `/* ... */` block | SimTalk's lexer tokenizes a bare `==` as the equality operator even on lines that look like comments. Mixing decorated and commented lines in a NOTE causes `Syntax error near line 1 at '=='`. Wrap the whole NOTE in `/* ... */` to avoid the trap entirely — see "Block-comment NOTE pattern" below. |
| 10 | `add_note.py --note` uses `argparse nargs="+"` which **stops** at any token starting with `--` (treated as a flag) | Multi-line notes whose lines begin with `--` cannot be passed through `--note`. Workaround: bypass `add_note.py` and write a small Python driver that builds the SimTalk payload directly via `socket_client.py`, the same way `add_note.py` does internally. |
| 11 | `result` is a reserved identifier in SimTalk (the implicit function-return variable) | Don't name a local `var result`. Doing so yields `Syntax error near line 1 at 'result'`. Use `synOut`, `res`, etc. |
| 12 | `simtalk_hasError(<source>)` returns a `string` (not `boolean`) | Assign to `var s: string`, not `var b: boolean` — otherwise you get `Left and right sides of the assignment are incompatible.` |
| 13 | Single `obj.program := ...` payload must stay ≤ ~2 KB | Server-side JSON parser truncates payloads > ~2 KB and returns `Error in line 1: Unexpected end of string`. 5 retries don't recover (this is **not** a transient). For long NOTE blocks, split into chunks of 25-30 lines each (~1.5-2 KB payload), first chunk via `obj.program := chunk_1`, subsequent chunks via `obj.program := obj.program + chr(10) + chunk_N`. The original body is appended as the last chunk the same way. |

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

## Block-comment NOTE pattern (recommended for header blocks)

When a header NOTE includes decoration lines like `=====`, `-----`,
`*****`, or any line whose first non-blank characters are NOT `--` /
`//`, prefer wrapping the **entire** NOTE in `/* ... */`:

```simtalk
/*
================================================================
-- Method path : .CTU.Frame.Program
-- Method type : Method   (something)
----------------------------------------------------------------
-- Purpose
--   one-line description
================================================================
*/
-- (original executable code starts here, byte-for-byte preserved)
var i := 1
```

Why this matters (Quirk #9): SimTalk's lexer tokenizes a bare `==` as
the equality operator **before** it decides whether the line is a
comment. A NOTE block that mixes `-- ...` lines with bare `=====`
decoration lines throws:

```
Syntax error near line 1 at '=='. (in row :1)
```

even when the very next line is a valid `--` comment. Wrapping in
`/* ... */` puts every character inside the block-comment scanner,
which doesn't tokenize, so `==`, `--`, `//`, `{`, `"` are all safe.

This is also the safest way to write a long NOTE that you plan to
copy into many Methods (consistent look, no per-line `--` to forget).

## Limitations

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