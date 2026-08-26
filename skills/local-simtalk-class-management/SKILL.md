---
name: local-simtalk-class-management
description: Manage and derive/inherit Plant Simulation classes — list classes inside a folder, inspect a class's inheritance metadata (Origin / OriginRoot / Class / InternalClassType / attributes / methods), **derive a subclass** (preserves inheritance from the parent), **duplicate a class** (copies and cuts inheritance), rename a class (setName), delete a class (deleteObject), move a class to another folder (moveToFolder), and manage user-defined attributes on a class (createAttr / deleteAttr / setAttribute / inheritAttribute). The skill wraps one SimTalk operation per call and sends it through `local-simtalk-execution` so the change is reflected immediately on the running server. Triggers: "derive a class", "create a subclass of `<path>`", "duplicate `<path>` into `<folder>`", "rename class `<old>` to `<new>`", "delete class `<path>`", "move `<path>` to `<folder>`", "add a user-defined attribute to `<path>`", "what classes are in `<folder>`", "show me the full details of `<path>`". Read-only inspection of the inheritance map is the sibling `local-simtalk-get-class-inheritance`; read-only folder enumeration is `local-simtalk-get-folder-tree`.
---

# local-simtalk-class-management

**Write-side** companion to `local-simtalk-get-class-inheritance` (which only
reads). This skill lets Claude create, rename, delete, move, derive, and
duplicate classes in the Plant Simulation **Class Library**, and manage
user-defined attributes on those classes — each operation goes straight to
the running server via `local-simtalk-execution/scripts/simtalk_send.py`.

This skill does **not** maintain its own TCP transport; it composes a single
SimTalk snippet per operation and dispatches it through `simtalk_send.py`.

## When to use

- "Derive a subclass of `<parent>` named `<child>`"
- "Duplicate `.MaterialFlow.Conveyor` into `UserObjects` as `MyConveyor`"
- "Rename `.UserObjects.MyConveyor` to `Belt5m`"
- "Delete `.UserObjects.OldClass`"
- "Move `.UserObjects.NewClass` into `.Models.Model`"
- "Add a user-defined attribute `lotsize: integer` to `.Models.Model`"
- "Set the value of `.Models.Model.lotsize` to 50"
- "Make `.Models.Model.lotsize` inherit again from its parent class"
- "List every class inside `.UserObjects`"
- "Show me Origin / OriginRoot / Class / attributes / methods of `<path>`"

Do **not** use this skill for:

- Read-only inspection of the inheritance map (use `local-simtalk-get-class-inheritance`)
- Walking the model folder structure (use `local-simtalk-get-folder-tree`)
- Inserting an *instance* of a class into a Frame — that's `class.create(parent)`
  inside a SimTalk script, not a class-library operation
- Renaming the `EventController` or `Connector` (Plant Simulation rejects it)
- Modifying built-in objects in place — derive a subclass first

## How it works

The skill ships a single dispatcher script, `scripts/class_ops.py`, that
takes a subcommand + arguments, composes the matching SimTalk snippet,
sends it via `simtalk_send.py run`, and returns a JSON envelope on stdout.

```text
class_ops.py <subcommand> [args...] [--no-infobox]
```

Subcommands map 1:1 to Plant Simulation SimTalk methods documented in
`01-plantsimulation-knowledge/01-plant-simulation-help/objects/common-methods/common-methods.md`:

| Subcommand | SimTalk | What it does |
|---|---|---|
| `list <folder>` | walk `folder.numNodes` + `node(i).InternalClassType` | List class candidates in a folder |
| `inspect <path>` | `o.Origin`, `o.OriginRoot`, `o.Class`, `o.numAttributes`, `o.numMethods`, etc. | Read one class's full inheritance + size metadata |
| `derive <parent> [dest] [name]` | `<parent>.derive([dest], [name])` | **Create a subclass** that inherits from `<parent>` |
| `duplicate <source> [dest] [name]` | `<source>.duplicate([dest], [name])` | **Copy a class**, cutting the inheritance link |
| `rename <path> <new_name>` | `<path>.setName(<new_name>)` | Rename a class (returns `true`/`false`) |
| `delete <path>` | `<path>.deleteObject` | Delete a class (returns `true`/`false`) |
| `move <path> <folder>` | `<path>.moveToFolder(<folder>)` | Move a class to another folder |
| `add-attr <path> <name> <type>` | `<path>.createAttr(<name>, <type>)` | Add a user-defined attribute to a class |
| `del-attr <path> <name>` | `<path>.deleteAttr(<name>)` | Delete a user-defined attribute |
| `set-attr <path> <name> <value>` | `<path>.<name>.setAttribute(<value>)` | Set a UDA's value on a class (cuts inheritance) |
| `inherit-attr <path> <name>` | `<path>.<name>.inheritAttribute` | Restore inheritance on a UDA |

`<path>` follows the Class Library path convention (`.` per depth level —
e.g. `.MaterialFlow.Station`, `.UserObjects.MyConveyor`). Folder paths use
the same convention.

> **Hard rule:** the `<dest>` argument to `derive` / `duplicate` is a
> **folder path**, not a class path. The new class is added as a child of
> that folder. If you omit `dest`, Plant Simulation places the new class
> in the same folder as the parent.

### Skill convention: always announce with `infoBox`

Per the `local-simtalk-execution` v18 → v19 convention, every **mutating**
operation (everything except `list` / `inspect`) opens a non-modal
`infoBox(text, false)` on the Plant Simulation GUI before doing the
work, and closes it (defensively twice) on exit. The text tells the
operator what the skill is currently mutating.

| Stage | What the script does |
|---|---|
| Entry | `infoBox("[class_ops] start: <subcommand> <args>", false)` |
| Exit (success or failure) | `infoBox("", false)` **twice** — defensive double-close |
| Headless / batch runs | Pass `--no-infobox` as the **last** argument to suppress the open/close cycle entirely |

The second argument `false` is the modal flag — non-modal so it never
freezes the GUI while the request is in flight. Quirk: do **not** swap to
`infoBox(text, true)` (modal) — that would block the server waiting for a
GUI click (lifelines §4).

## Usage

All subcommands print a JSON envelope on stdout:

```json
{
  "ok": true,
  "subcommand": "derive",
  "args": {"parent": ".MaterialFlow.Station", "dest": ".UserObjects", "name": "MyStation"},
  "before": {"path": ".MaterialFlow.Station", "name": "Station", "type": "Station"},
  "after":  {"path": ".UserObjects.MyStation", "name": "MyStation", "type": "Station",
             "origin": ".MaterialFlow.Station", "originroot": ".MaterialFlow.Station",
             "class": ".MaterialFlow.Station"},
  "log_tail": "...last 200 chars of the server log..."
}
```

On failure `ok` is `false` and `error` carries the reason
(e.g. `"name not unique"`, `"path does not resolve"`).

```bash
# 1) List every class candidate inside .UserObjects
python3 scripts/class_ops.py list .UserObjects

# 2) Inspect one class (Origin / OriginRoot / Class / size)
python3 scripts/class_ops.py inspect .MaterialFlow.Station

# 3) Derive a subclass — kept in the same folder, default name "Station"
python3 scripts/class_ops.py derive .MaterialFlow.Station
python3 scripts/class_ops.py derive .MaterialFlow.Station .UserObjects MyStation

# 4) Duplicate (copy + cut inheritance) into .Models.Model
python3 scripts/class_ops.py duplicate .MaterialFlow.Conveyor .Models.Model MyConveyor

# 5) Rename a class
python3 scripts/class_ops.py rename .UserObjects.MyConveyor Belt5m

# 6) Delete a class
python3 scripts/class_ops.py delete .UserObjects.OldClass

# 7) Move a class into another folder
python3 scripts/class_ops.py move .UserObjects.NewClass .Models.Model

# 8) Manage user-defined attributes on a class
python3 scripts/class_ops.py add-attr  .Models.Model lotsize integer
python3 scripts/class_ops.py set-attr  .Models.Model lotsize 50
python3 scripts/class_ops.py inherit-attr .Models.Model lotsize
python3 scripts/class_ops.py del-attr  .Models.Model lotsize

# 9) Headless / CI runs (suppress infoBox)
python3 scripts/class_ops.py --no-infobox derive .MaterialFlow.Station .UserObjects MyStation
```

The script runs on the **WSL2 / Docker container** that hosts the bridge
to Plant Simulation. Default target is `host.docker.internal:50007`
(matches `local-simtalk-execution`'s default).

## Output shape

Every subcommand emits a JSON object on stdout (see example above) and a
human-readable summary on stderr. The `before` field is the source
object's identity for write ops; the `after` field is the freshly
created / moved / renamed object's identity (including its new Origin
triple for derive/duplicate so you can verify the inheritance link).

`list <folder>` output:

```json
{
  "ok": true,
  "subcommand": "list",
  "args": {"folder": ".UserObjects"},
  "children": [
    {"i": 1, "name": "MyConveyor", "type": "Conveyor", "path": ".UserObjects.MyConveyor"},
    {"i": 2, "name": "MyStation",  "type": "Station",  "path": ".UserObjects.MyStation"},
    ...
  ]
}
```

`inspect <path>` output (full read-only metadata for one class):

```json
{
  "ok": true,
  "subcommand": "inspect",
  "args": {"path": ".UserObjects.MyStation"},
  "path": ".UserObjects.MyStation",
  "name": "MyStation",
  "type": "Station",
  "origin": ".MaterialFlow.Station",
  "originroot": ".MaterialFlow.Station",
  "class": ".MaterialFlow.Station",
  "internalclasstype": "Station",
  "num_attributes": 0,
  "num_methods": 0,
  "num_nodes": 0
}
```

## Inheritance semantics (Plant Simulation)

From `01-plantsimulation-knowledge/.../common-read-only-attributes.md`:

| Attribute | Meaning |
|---|---|
| `Origin` | The object from which `<Path>` was derived **most recently** (immediate parent) |
| `OriginRoot` | The **root** of the inheritance chain (built-in class library root) |
| `Class` | The class in the Class Library from which `<Path>` was derived, possibly over several levels |
| `InternalClassType` | The unique built-in English object name describing the type of `<Path>` |

`derive` preserves `Origin`, `OriginRoot`, and `Class` (the new class
inherits from the source). `duplicate` severs the inheritance link —
`Origin` becomes the duplicated copy itself, not the original. If you
want a child that picks up future parent changes, use `derive`. If you
want a one-off snapshot, use `duplicate`.

> The Plant Simulation Help §13 recommendation: **do not change built-in
> object standard settings; derive instead.** Derived/duplicated objects
> land in `UserObjects` (the Plant Simulation default) or wherever
> `dest` points.

## Pre-flight rule — build the inheritance map before mutating

Before invoking **any** mutating subcommand (`derive` / `duplicate` /
`rename` / `delete` / `move` / `add-attr` / `set-attr` / `del-attr` /
`inherit-attr`), first call the sibling skill
`local-simtalk-get-class-inheritance` to understand the inheritance
relationships between the candidate classes. Read-only ops (`list`,
`inspect`) do **not** require this step.

Why the inheritance map must come first:

1. **Confirm the right parent.** `derive` and `duplicate` produce
   different outcomes depending on whether the parent is a built-in
   (`.MaterialFlow.Station`) or a user-derived class
   (`.UserObjects.MyStation`). The map tells you exactly which one is
   being targeted, with its `Origin` / `OriginRoot` / `Class` triple.
2. **Detect name collisions up front.** The map exposes existing
   siblings (e.g. `.UserObjects.MyConveyor_2`) so you don't have to wait
   for Plant Simulation to silently suffix your new class with `_2`
   (Quirk CM-1).
3. **Spot live instances before delete / rename.** A `delete` on a
   class with instances in any Frame silently returns `false`
   (Quirk CM-4); `rename` of a class whose instances still exist is
   legal but risky. The inheritance map surfaces both situations.
4. **Don't sever the wrong chain.** `duplicate` cuts the inheritance
   link entirely — `Origin` becomes the copy itself. Confirm the
   parent is the one you intended before issuing the call.
5. **Avoid mutating built-ins directly.** Plant Simulation Help §13
   recommends *deriving* rather than editing built-in objects. The map
   shows which classes are built-ins (chain rooted at
   `.MaterialFlow.*` / `.WorkerPool.*` / etc.) so you know to derive
   first.

### Recommended workflow

```text
┌────────────────────────────────────────────────────────────────┐
│ 1. local-simtalk-get-folder-tree       → locate candidates    │
│ 2. local-simtalk-get-class-inheritance  → inheritance map      │
│ 3. local-simtalk-class-management       → derive / duplicate … │
└────────────────────────────────────────────────────────────────┘
```

`inspect <path>` (this skill) is fine to interleave — it's the
single-class read-only view. The model-wide **map** comes from the
sibling skill.

## Hard rules / Quirks (subset of `local-simtalk-execution/references/lifelines.md`)

| Rule | Why |
|---|---|
| `type` field must be one of `ping` / `simtalk_syntax` / `simtalk_run` / `readlog` | Unknown types cause silent server-side hang (Quirk #13) |
| Use `simtalk_send.py run` (it handles `\|\|END\|\|` framing + Quirk double-check) | Server never closes the socket (lifelines §2); `simtalk_run` returns `result:"success"` even on runtime errors (lifelines §6) |
| `simtalk_run` `data` field is **always** empty | Quirk #6 — server doesn't serialize return values. This skill `print`s the result and parses via the stdout / log envelope |
| Runtime errors return `result:"success"` with `log:"code execute failed..."` | Quirk #7 — `simtalk_send.py` returns exit code 11 for these; `class_ops.py` translates to `ok:false, error:"runtime"` |
| Avoid `prompt` / `infoBox(..., true)` / writing undeclared global attrs | Modal trap — server blocks until GUI click (lifelines §4) |
| **Always `infoBox(text, false)` on entry, close twice on exit** | Skill convention from `local-simtalk-execution` v18→v19 |
| Each script invocation runs **one** mutating op — no batching | Each `derive` / `duplicate` triggers Plant Simulation events; combining is risky |

### Skill-specific quirks

| # | Quirk | Workaround |
|---|---|---|
| CM-1 | `derive` without an explicit `name` may collide with an existing class and silently pick a unique suffix | Always pass `name` for production runs; the script warns on stdout when name is auto-generated |
| CM-2 | `derive` inside a Folder vs. on a class has different semantics — `<folder>.derive` makes no sense, only `<class>.derive` does | The script validates `parent.InternalClassType /= "Folder"` / `Frame` and rejects with a clear error |
| CM-3 | `setName` rejects renaming `EventController` or `Connector`; the rename call still succeeds at the SimTalk level but logs an error | The script reads the SimTalk return value; if it is `false` it returns `ok:false, error:"rename rejected"` |
| CM-4 | `deleteObject` on a class with live instances returns `false`; the class remains | The script surfaces the boolean; suggest the user run "Show Inheritance" to find instances |
| CM-5 | `moveToFolder` requires the destination folder to exist; passing a non-existent path raises a runtime exception | The script `str_to_obj`s `<dest>` first and rejects when the object is a class (not a Folder) |
| CM-6 | `createAttr` types must be Plant Simulation type names (`integer`, `string`, `boolean`, `real`, `length`, `time`, `speed`, `acceleration`, `weight`, `currency`, `object`, `method`, `list`, `table`, `any`, etc.) — passing `int` returns a runtime error | The script passes the literal through and surfaces the runtime error verbatim |
| CM-7 | `<path>.createAttr` declares a UDA whose *name* must not collide with existing attributes on that class | Caller's responsibility — script does not pre-check; the runtime error is reported if collision occurs |

## Path resolution

`str_to_obj(<path>)` is the SimTalk built-in that turns a string path into
an object reference. Paths follow the Plant Simulation convention (leading
`.` per depth level). Examples:

| Path string | Resolves to |
|---|---|
| `.` | the basis root (display name "Basis", anonymous path) |
| `.UserObjects` | the `UserObjects` folder under basis |
| `.MaterialFlow.Station` | the `Station` class under `MaterialFlow` |
| `.Models.Model` | the `Model` Frame under `Models` |

The basis identifier itself is **anonymous** — `obj_to_str(basis)` returns
the empty string. That is why folder paths in the docs always start with
a leading `.` for each depth level.

## Limitations

- **One operation per invocation.** No batching across multiple class
  mutations — each call is its own SimTalk round-trip so a partial
  failure leaves a clear before/after state. Use a shell loop for batch
  renames.
- **`infoBox` requires a GUI session.** The `infoBox(text, false)` call
  targets the Plant Simulation GUI window — if the server is running
  headless (no display), the call still returns success but no box
  appears. Use `--no-infobox` in CI / headless contexts.
- **No instance manipulation.** This skill manages **classes** in the
  Class Library. Inserting / deleting / moving *instances* inside a
  Frame uses different SimTalk (`class.create`, `instance.deleteObject`)
  and is out of scope; use `local-simtalk-execution` directly with
  bespoke SimTalk for instance-side work.
- **No type-aware UDA values.** `set-attr` accepts the value as a
  SimTalk literal string and substitutes it directly. Boolean / integer
  / string are trivial; complex types (lists, tables, objects) need
  bespoke SimTalk and should go through `local-simtalk-execution`
  directly.
- **No undo.** Plant Simulation has no per-edit undo over SimTalk; an
  accidental `delete` / `rename` is permanent. Always confirm with the
  user before running a mutating subcommand on a non-scratch model.
- **Read-only inspection still belongs in `local-simtalk-get-class-inheritance`.**
  This skill only inspects when needed for the `before`/`after` envelope
  on a write op. For a model-wide inheritance map, use the sibling
  skill.

## Key files

- `scripts/class_ops.py` — dispatcher: parses subcommand, composes
  SimTalk, sends via `simtalk_send.py`, returns JSON envelope
- `references/simtalk-recipes.md` — the exact SimTalk templates per
  subcommand, with parameter escaping rules
- `references/protocol-notes.md` — write-side quirks discovered during
  testing (a v1 will be filled in after the first end-to-end run)
- `data/` — JSON envelopes from successful runs (operational log)
- `log/` — human-readable session notes

## Related skills

- `local-simtalk-execution` — the underlying TCP transport skill;
  consult its `references/lifelines.md` for protocol details before
  modifying `class_ops.py`.
- `local-simtalk-get-folder-tree` — produces the model structure used to
  find candidate parent / destination paths before invoking this skill.
- `local-simtalk-get-class-inheritance` — **prerequisite for every
  mutating op.** Build the Origin / OriginRoot / Class map first to
  confirm the right parent, surface name collisions, and detect live
  instances before issuing any `derive` / `duplicate` / `rename` /
  `delete` / `move` / attribute-changing call. See the
  [Pre-flight rule](#pre-flight-rule--build-the-inheritance-map-before-mutating)
  section above.