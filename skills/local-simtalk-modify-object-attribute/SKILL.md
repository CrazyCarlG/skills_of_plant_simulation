---
name: local-simtalk-modify-object-attribute
description: Read and modify attributes on Plant Simulation model objects by sending SimTalk snippets through the `local-simtalk-execution` TCP transport. Use when the user wants to set an attribute (boolean / integer / real / string / dateTime / time / object ref) on an instance under `.Models.Model.*` (or any other non-simtalkclaude path), verify the new value stuck, and restore the original value afterwards. Triggers include: "change this property", "set attribute X to value Y", "modify the EventController's RealtimeScale", "tweak a Buffer capacity", "flip SkipLongEventIntervals", "what value does <Path>.<Attr> have right now". This skill depends on `local-simtalk-execution` for transport — it only authors the SimTalk patterns and verification script. It does NOT touch anything inside `.SimtalkClaude`.
---

# local-simtalk-modify-object-attribute

Read / modify / verify / restore a single attribute on a Plant Simulation model
object. Composes SimTalk snippets and ships them through the
`local-simtalk-execution` skill's `simtalk_send.py run` subcommand. After every
write, captures the post-write value back via `print` + `readlog` so you can
confirm the change actually persisted on the server (not just compiled).

> **Scope.** This skill is for modifying attributes on real model objects
> (anything reachable by `str_to_obj(<path>)`) and verifying the change. It
> **never** writes inside `.SimtalkClaude.*` — that folder is off-limits by
> user convention.

## When to use

- "Change `<path>.<attr>` from X to Y, then tell me if it stuck"
- "Read the current value of `<attr>` on `<obj>`"
- "Flip a boolean attribute on the EventController"
- "Bump a numeric parameter (RealtimeScale, RandomNumbersVariant, etc.) and
  restore it when you're done"

Do **not** use this skill for:

- Adding new attributes to an object (modal dialog trap — see §4 of
  `local-simtalk-execution/references/lifelines.md`)
- Modifying `.SimtalkClaude.*` (off-limits)
- Calling methods (use `simtalk_run` directly with the method body — this skill
  only handles attribute reads/writes)
- Editing the `.spp` / `.psfm` file on disk (use the file-format skills instead)

## How it works

The skill is a thin wrapper around `simtalk_send.py run` that enforces a
**read → write → read → restore** discipline so every attribute change is
verifiable and reversible.

### The 3-pattern protocol

Every modification uses one of these three SimTalk patterns, chosen by attribute
type:

```simtalk
-- Boolean attribute
var obj: object := str_to_obj("<path>")
var before: boolean := obj.<attr>
obj.<attr> := <new boolean>
var after: boolean := obj.<attr>
print "###MARKER###"
print "<attr>: " + to_str(before) + " -> " + to_str(after)
print "###END###"
```

```simtalk
-- Numeric (integer / real) attribute
var obj: object := str_to_obj("<path>")
var before: real := obj.<attr>
obj.<attr> := <new number>
var after: real := obj.<attr>
print "###MARKER###"
print "<attr>: " + to_str(before) + " -> " + to_str(after)
print "###END###"
```

```simtalk
-- String / dateTime / time attribute
var obj: object := str_to_obj("<path>")
var before: string := obj.<attr>
obj.<attr> := <new value>
var after: string := obj.<attr>
print "###MARKER###"
print "<attr>: " + before + " -> " + after
print "###END###"
```

After every `simtalk_run`, immediately follow with a `readlog` and grep for
the `###MARKER###` ... `###END###` block to recover the actual before/after
values. The socket itself never carries the value (Quirk #6 —
`local-simtalk-execution/references/lifelines.md` §6), so `print + readlog`
is the only feedback path.

### Workflow

1. **Resolve the object** — confirm `str_to_obj("<path>")` does not return
   `void`. If it does, abort; the path is wrong or not loaded.
2. **Pick the attribute** — look up `<attr>` in the Plant Simulation knowledge
   base (`01-plantsimulation-knowledge/01-plant-simulation-help/objects/<type>/attributes/`)
   to confirm it exists and learn its data type. Don't guess — undeclared
   attribute writes hit the modal trap (lifelines §4).
3. **Read first** — capture the current value into a `before` local var, then
   write the new value into the attribute, then read again into `after`. Print
   both with markers.
4. **Verify** — `readlog` and grep for `###MARKER###`. The change is confirmed
   only if the printed `after` matches what you wrote.
5. **Restore** — at the end of the session, set the attribute back to
   `before`. The `attr_modify.py --restore` helper automates this.

## Usage

The helper script automates the read/write/readback loop:

```bash
# Single-attribute read + write + readback (prints before/after to stdout)
python3 scripts/attr_modify.py \
    --path .Models.Model.EventController \
    --attr SkipLongEventIntervals \
    --value false \
    --type boolean

# Just read the current value
python3 scripts/attr_modify.py --path .Models.Model.EventController --attr SkipLongEventIntervals --read-only

# Note: in --read-only mode, the per-attribute section header prints `(None)` for the
# type slot (e.g. `=== .Models.Model.EventController.SkipLongEventIntervals (None) ===`)
# because `--type` is intentionally not required for read-only runs. Cosmetic only —
# the read still works; ignore the `(None)` slot.

# Modify, then auto-restore on exit
python3 scripts/attr_modify.py \
    --path .Models.Model.EventController \
    --attr RealtimeScale \
    --value 5.0 \
    --type real \
    --restore

# Atomic batch: modify three attrs, restore all on exit
python3 scripts/attr_modify.py \
    --path .Models.Model.EventController \
    --batch SkipLongEventIntervals=false:boolean RealtimeScale=5:real RandomNumbersVariant=7:integer \
    --restore
```

## Hard rules (subset of `local-simtalk-execution/references/lifelines.md`)

| Rule | Why this skill cares |
|---|---|
| `type` field must be `simtalk_run` (whitelist — Quirk #13) | Every modification is a `simtalk_run`; never `simtalk_syntax` (which doesn't execute) |
| `--resp-mode delimiter --resp-delimiter '\|\|END\|\|'` | Server never closes the socket; `eof` mode hangs to timeout |
| `simtalk_run` `data` field is **always** empty (Quirk #6) | Don't trust `data` — use `print` + `readlog` to extract values |
| Runtime errors return `result:"success"` with `log:"code execute failed..."` (Quirk #7) | Double-check both fields in every reply |
| Avoid `prompt` / `infoBox` / writing undeclared global attrs | Modal trap — server blocks until GUI click (lifelines §4) |
| `str_to_obj` may return `void` if path is wrong | Always check before dereferencing — dereferencing `void` triggers Quirk #7 |
| `readlog` is degraded in v15+ — may not capture `print` | Test on a single read first; if the marker doesn't appear, fall back to the GUI console (Window ribbon → Console) |
| Don't write inside `.SimtalkClaude.*` | User convention — out of scope for this skill |

## Attribute type reference (cheat sheet)

Plant Simulation attribute types and the assignment syntax used in SimTalk:

| Type | Decl syntax | Example assignment |
|---|---|---|
| `boolean` | `var x: boolean := obj.<attr>` | `obj.<attr> := true` |
| `integer` | `var x: integer := obj.<attr>` | `obj.<attr> := 42` |
| `real` | `var x: real := obj.<attr>` | `obj.<attr> := 3.14` |
| `string` | `var x: string := obj.<attr>` | `obj.<attr> := "hello"` |
| `dateTime` | `var x: dateTime := obj.<attr>` | `obj.<attr> := str_to_dateTime("2026/01/02 14:00:00")` |
| `time` | `var x: time := obj.<attr>` | `obj.<attr> := str_to_time("40:00.00")` |
| `object` / `method` | `var x: object := obj.<attr>` | `obj.<attr> := &myMethod` (method ref) / `obj.<attr> := str_to_obj(".path")` (object ref) |
| `length` | `var x: length := obj.<attr>` | `obj.<attr> := 10` (numeric, with unit suffix optional) |

> **Caveat on `void`**: if `str_to_obj` returns `void` and you dereference
> `<void>.<attr>`, the server returns `result:"success"` with
> `log:"code execute failed. error msg:Unknown identifier ..."` (Quirk #7).
> Always test the return value of `str_to_obj` before assigning.

## Path resolution

`str_to_obj(<path>)` accepts Plant Simulation dotted paths:

| Path | Resolves to |
|---|---|
| `.Models.Model` | The model Frame |
| `.Models.Model.EventController` | The EventController instance in the loaded model |
| `.MaterialFlow.Source` | The Source **class** in the class library (for type introspection) |
| `.SimtalkClaude.*` | **Off-limits** — refuse and tell them to use a different skill or do it manually |

Anonymous paths (`""`, the basis root) cannot be passed directly to
`str_to_obj`; navigate via the parent and use `.node(i)` if you need to walk
the basis.

## Limitations

- **One attribute at a time** per `simtalk_run`. To modify multiple attributes,
  use the `--batch` flag (comma-separated) — each attribute still requires its
  own read/write/readback transaction to be reliable.
- **`readlog` reliability** — per lifelines §5, v15+ has a regression where
  `readlog` may not capture `print` output, may show stale entries, or may
  exhibit buffer-explosion feedback loops. If a marker is missing, retry
  once; if still missing, fall back to manual inspection in the GUI.
- **No transaction rollback.** If you set three attributes and the second one
  fails, the first stays changed. Use `--restore` only after all writes
  succeeded.
- **No creation of new attributes** — out of scope (modal trap).
- **Cannot write to method/control attributes** (`InitCtrl`, `ResetCtrl`,
  `StartStopCtrl`) — those require `&methodRef` syntax and need careful
  verification of the method's signature before binding. Use plain
  `simtalk_run` for those, not this skill.

## Key files

- `scripts/attr_modify.py` — CLI wrapper implementing read / write / readback
  / restore for one or more attributes.
- `examples/example.md` — the 2026-08-26 verification run on `.Models.Model.EventController`
  that originally motivated this skill.
- `references/code-templates.md` — copy-paste SimTalk snippets for every
  attribute type.
- `references/quirks.md` — gotchas discovered during testing (Quirk #6/7
  interplay, str_to_obj returning void, etc.).

## Related skills

- `local-simtalk-execution` — the underlying TCP transport; consult its
  `references/lifelines.md` before doing anything non-standard.
- `local-simtalk-get-folder-tree` — read-only exploration to find which
  objects exist under a given path before trying to modify them.
- `local-simtalk-get-class-inheritance` — figure out an object's class
  hierarchy to look up its attributes in the knowledge base.