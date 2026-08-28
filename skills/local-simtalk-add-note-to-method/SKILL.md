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

- **English request** → English NOTE block
- **Chinese request** → Chinese NOTE block
- **Mixed request** → mirror the user's mix
- **Explicit override** ("用英文" / "用中文注释" / "in English please") wins
- **Don't translate an existing NOTE** without an explicit ask
- **Code identifiers stay verbatim** — method paths, socket fields,
  SimTalk keywords, and quoted contract literals are never translated

This rule was added after the user requested:

> 如果用户用英文发文，就通过英文注释，如果用中文，则用中文注释

## Pre-annotation workflow (read context first)

Before composing a NOTE block:

1. **Read the Plant Simulation knowledge base** at
   `01-plantsimulation-knowledge/01-plant-simulation-help/` for the
   relevant domain — SimTalk comment syntax, Method attributes,
   `str_to_obj` / `obj.execute` lifecycle.
2. **Run `local-simtalk-read-library`** to dump the current model's
   Method inventory + verbatim source. Use it to verify the original
   body is preserved byte-for-byte and to find direct callers.
3. **Identify direct callers** of the target method (grep the dump).
   Read their bodies to see how they consume the return value and
   which shared dictionaries they read.
4. **Read the target's original `program`** from the dump — you'll
   re-append it byte-for-byte after the NOTE.
5. **Compose the NOTE** mentioning: actual caller chain, actual
   return-value contract (literal strings downstream matches against),
   actual side-effect consumers.

**Why:** prior annotations described the function signature but missed
the actual call graph and side-effect consumers — making the NOTE
decorative rather than useful. The user pointed this out:
"你缺乏一些plant simulation的知识和当前对library的了解".

## Usage

`scripts/annotate.py` is the canonical driver. It captures the original
program via markers + `readlog()`, encodes the NOTE block via
`encode_for_simtalk()` (Pitfall P-1), chunks writes at ~10 lines
(default — drop to 6-8 for Chinese-heavy NOTEs since each Chinese char
expands ~6 bytes via `chr()`), retries each chunk 5× with 1 s sleep
(Quirk #21), syntax-checks via `simtalk_hasError`, and verifies via
readback of the modified program.

```bash
python3 scripts/annotate.py \
    --path .P4_CTU.AdvancedObject.Software.RCS.m_addBinStateInTable \
    --note-file notes/m_addBinStateInTable.md \
    --backup code_log/P4_CTU_AdvancedObject_Software_RCS_m_addBinStateInTable_original.txt
```

For a worked end-to-end example (capture → write → verify → readback
output), see `examples/example.md`.

## The 4 modes

| Mode | What it does | When to use |
|---|---|---|
| `prepend` | Insert comments **before** the existing code | Header / author / purpose block |
| `append` | Insert comments **after** the existing code | Footer / TODO / changelog |
| `replace` | Overwrite the entire `program` with new content | Full rewrite (use cautiously) |
| `trailing` | Append a trailing `-- ...` comment to the **last line** | Quick inline annotation |

`prepend` and `append` are the only ones that preserve the original
executable code; `replace` discards it (caller must keep their own
backup). All modes use `chr(10)` for real newlines — see Quirk #1.

## Hard rules

- **Full Quirk list (Q1–Q11)** with reproducers: `references/quirks.md`
- **Full Pitfall list (P-1–P-7)** with reproducers: `references/pitfalls.md`

The five most critical rules, in one line each:

1. **Q1** — Use `chr(10)` for newlines; never `"\n"`. SimTalk has no string-escape sequences.
2. **Q3** — Always backup `program` to `code_log/<safe-name>_original.txt` before writing.
3. **Q4** — Verify `obj.internalclasstype == "Method"` before touching `program`.
4. **P-1** — Assemble RHS via `encode_for_simtalk()` (every `"` / `\` / `|` / non-ASCII goes through `chr(N)`); never apply Python-side `quote()`.
5. **P-3** — Single payload must stay ≤ ~2 KB. Use `annotate.py` for anything bigger (it chunks automatically).

## Recovery workflow (when the backup is corrupt)

If `code_log/<path>_original.txt` is polluted with timestamps or stale
console traces, don't trust the backup. Build the source string in
SimTalk directly using `chr(10)` for newlines and `chr(<codepoint>)`
for non-ASCII (e.g., `chr(8212)` for em-dash, `chr(20013)` for `中`),
then `obj.program := <built string>`. The Python-side `\"` for outer
JSON escaping is fine — only the SimTalk parser sees what Python
unescapes, and SimTalk requires `chr()` for special chars.

## Limitations

- **One Method at a time.** Loop the script or use
  `local-simtalk-simtalk-note-adder` for batch annotation.
- **No transaction rollback.** Prepend/append/replace in three runs =
  no atomic rollback; re-load from the on-disk backup if a step fails.
- **Inheritance is silent** — `.main.X` and `.connection.X` may share
  `program` text but are separate instances. Always probe `obj.Class` /
  `obj.Origin` before writing (Pitfall P-7).
- **Method body size** — `program` is a string; multi-MB sources are
  technically writable but TCP packet size is the practical limit
  (chunked writes help — Quirk #13).
- **Cannot create new attributes** (modal trap — see
  `local-simtalk-execution/references/lifelines.md` §4).

## Key files

- `scripts/annotate.py` — chunked-write driver (capture + write +
  syntax-check + smoke + readback for one Method's `program`).
- `scripts/simtalk_string_utils.py` — `encode_for_simtalk`,
  `scan_note_lines`, `chunk_lines`, `estimate_payload_bytes` utilities.
- `references/quirks.md` — Q1–Q11 with minimal reproducers.
- `references/pitfalls.md` — P-1–P-7 with reproducers and fixes.
- `references/comment-syntax-reference.md` — authoritative locations
  for SimTalk comment syntax in the help docs.
- `examples/example.md` — the 2026-08-26 verification run on
  `.CTU.Frame.Program` that originally motivated this skill.

## Related skills

- `local-simtalk-execution` — TCP transport; consult its
  `references/lifelines.md` before doing anything non-standard.
- `local-simtalk-modify-object-attribute` — for non-`program` attribute
  reads/writes (boolean / integer / real / string / dateTime / etc.).
- `local-simtalk-simtalk-note-adder` — batch structured annotation.
- `local-simtalk-read-library` — read-only exploration.
- `local-simtalk-get-class-inheritance` — figure out a Method's class
  hierarchy before assuming it has a `program` attribute.
