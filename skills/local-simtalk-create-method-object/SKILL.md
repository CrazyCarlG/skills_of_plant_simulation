---
name: local-simtalk-create-method-object
description: Insert a new Method instance into a Plant Simulation Frame. Use this skill whenever the user (or a downstream skill like `local-simtalk-write-simtalk`) needs to create an empty Method container at `<frame>.<name>` so that source code can later be written into it. The skill validates the Frame path, parent class (default `.InformationFlow.Method`), and method name (rejects SimTalk reserved words and name collisions) before delegating to `local-simtalk-class-management/scripts/class_ops.py duplicate` which wraps the canonical `.InformationFlow.&Method.duplicate(<frame>, <name>)` SimTalk call. This skill **does NOT write code** — only creates the container. Triggers: "create a new method", "在 `.Models.Model` 下加一个 method 叫 `count_parts`", "insert an empty Method object at `<frame>.<name>`", "I need to add a method to the model first", "write_simtalk" (when the user did not specify a target Method, this skill runs first).
---

# local-simtalk-create-method-object

Insert a new Method instance into a Plant Simulation Frame. **Only creates the
empty container** — does NOT write code. To write code into the newly-created
Method, follow up with `local-simtalk-write-simtalk --path <method_path> ...`.

The actual `duplicate()` SimTalk call is delegated to
`local-simtalk-class-management/scripts/class_ops.py duplicate`, which
already wraps the canonical `.InformationFlow.&Method.duplicate(<frame>, <name>)`
pattern correctly (using `srcObj.duplicate(...)` via `str_to_obj` to avoid the
`Method` data-type collision in dot-path literals).

> **When to trigger this skill.** Any time a new Method container is needed:
> the user explicitly asks for one ("add a method called X"), or a downstream
> skill (currently `local-simtalk-write-simtalk`) detects that no Method path
> was provided and needs one to be created first.

## When to use

- "在 `.Models.Model` 下加一个叫 `count_parts` 的 method"
- "Add a brand-new Method named `log_warn` under `.CTU.Frame`"
- "`local-simtalk-write-simtalk` was called without `--path` and needs an
  empty Method container created first."
- "I need to put code in `<frame>.<name>` but `<name>` doesn't exist yet"

## Do NOT use for

- **Writing code** — use `local-simtalk-write-simtalk` after this skill
  produces the path. This skill ONLY creates the empty container.
- **Creating classes in the Class Library** (Folders, not Frames) — use
  `local-simtalk-class-management` directly with `derive` / `duplicate`.
- **Deriving / inheriting a new Method subclass** — use
  `local-simtalk-class-management derive <parent> [<dest>] [<name>]`.
- **Renaming / deleting / moving an existing Method** — use
  `local-simtalk-class-management rename / delete / move`.
- **Listing Methods under a Frame** — use `local-simtalk-get-folder-tree`.

## Choosing a target Frame

The skill requires `--frame`. Recommended defaults:

| Frame | When to use |
|---|---|
| `.Models.Model` | Plant Simulation's standard root Frame — the safe default if the user says "anywhere" or doesn't specify |
| `.CTU.Frame` (or other project-specific root) | When the user has named their own root Frame |
| Nested `.Models.Model.<SubFrame>` | When the user wants the Method scoped to a sub-model |

The skill does NOT auto-default — the human user (or the orchestrating skill)
must pass `--frame` explicitly. This is by design: silent defaults produce
"where did my method end up?" surprises.

## Choosing a parent class

Default: `.InformationFlow.Method` (Plant Simulation's basic Method class).
This is correct for ~95% of use cases. Override when:

- The user has a custom Method subclass with extra user-defined attributes
  (e.g. `.UserObjects.LoggingMethod` with `LogLevel: integer`). Use
  `--parent-class .UserObjects.LoggingMethod`.
- The user wants an existing project-specific Method class.

The skill validates that the parent class path resolves and is a Method
(or Method subclass); passing `.MaterialFlow.Station` (or any non-Method
class) is rejected with a clean error.

## Naming rules

The skill rejects names that would cause `duplicate()` to fail. See
`references/simtalk-reserved-words.md` for the full blocklist. Most common
failure:

- `method` (lowercase) — collides with the built-in `Method` data type. Use
  `myMethod`, `MethodImpl`, `do_method`, etc.

The skill also rejects:

- Names containing `.`, `/`, `-`, or other non-identifier characters.
- Names that already exist under the target Frame.

## Workflow

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. Read Plant Simulation knowledge base (simtalk-reserved-words.md) │
│ 2. Confirm target Frame path with the user (or orchestrating skill) │
│ 3. Confirm Method name (default `myMethod`)                          │
│ 4. Confirm parent class (default `.InformationFlow.Method`)          │
│ 5. Call `scripts/create_method_object.py` with the args above        │
│    - validates identifier shape                                     │
│    - validates reserved-word blocklist                              │
│    - validates Frame resolves (via class_ops.py inspect)             │
│    - validates parent class is a Method                             │
│    - validates no name collision                                    │
│    - delegates to class_ops.py duplicate                            │
│    - emits JSON envelope on stdout                                  │
│ 6. Take `method_path` from the envelope → pass to                   │
│    `local-simtalk-write-simtalk --path <method_path> --code-file ...` │
└─────────────────────────────────────────────────────────────────────┘
```

## Usage

```bash
# Minimal: insert Method `.Models.Model.myMethod` with default parent
python3 scripts/create_method_object.py \
    --frame .Models.Model \
    --method-name myMethod

# Custom parent class
python3 scripts/create_method_object.py \
    --frame .Models.Model \
    --method-name log_warn \
    --parent-class .UserObjects.LoggingMethod

# Validate inputs only — no server call
python3 scripts/create_method_object.py \
    --frame .Models.Model \
    --method-name myMethod \
    --dry-run
```

### Output shape

Success (always on stdout, JSON, machine-readable):

```json
{
  "ok": true,
  "method_path": ".Models.Model.myMethod",
  "frame_path": ".Models.Model",
  "method_name": "myMethod",
  "parent_class": ".InformationFlow.Method",
  "internal_class_type": "Method",
  "origin": ".InformationFlow.Method",
  "origin_root": ".InformationFlow.Method",
  "class": ".InformationFlow.Method"
}
```

Failure (also on stdout):

```json
{
  "ok": false,
  "error": "name_is_simtalk_reserved_word",
  "detail": "'method' collides with a SimTalk data type..."
}
```

`error` keys you may see:

| `error` | Cause |
|---|---|
| `invalid_method_name` | Contains non-identifier characters or starts with a digit |
| `name_is_simtalk_reserved_word` | See `references/simtalk-reserved-words.md` |
| `frame_invalid` | `--frame` doesn't resolve, or resolves to non-Frame |
| `parent_class_invalid` | `--parent-class` doesn't resolve, or isn't a Method class |
| `name_collision` | `<frame>.<method-name>` already exists |
| `duplicate_failed` | The actual `class_ops.py duplicate` call failed (runtime) |

## Integration with `local-simtalk-write-simtalk`

`local-simtalk-write-simtalk` requires `--path` to point at an existing Method
(this is its sole job: write code into a given Method). When a user calls
`write_simtalk` without `--path`, the orchestrating agent (or the skill's own
error message) should:

1. Invoke `local-simtalk-create-method-object` first to create the empty
   Method, OR
2. Ask the user where the Method should live, then invoke this skill, then
   invoke `write_simtalk --path <new_method_path>`.

The current `write_simtalk` does the second: it prints an error pointing at
this skill.

## Hard rules / Quirks

| # | Rule | Why |
|---|---|---|
| 1 | Use `class_ops.py duplicate`, NOT `<parent>.create(<frame>, <name>)` | `create` is a SimTalk keyword + List method — three `create()` patterns all fail (Quirk #15) |
| 2 | The Frame arg to `duplicate()` must be an object reference, not a string | Plant Simulation's `duplicate(<obj>, <name>)` rejects raw strings. `class_ops.py` wraps with `str_to_obj(...)` |
| 3 | Parent class name needs `&` ONLY in dot-path literals, not in `str_to_obj` refs | `class_ops.py` uses `srcObj := str_to_obj("..."); srcObj.duplicate(...)`, sidestepping the `Method` data-type collision |
| 4 | Method name must not be a SimTalk reserved word | See `references/simtalk-reserved-words.md` — Plant Simulation rejects with a runtime error that doesn't always name the offender |
| 5 | Method name must be a valid ASCII identifier | Plant Simulation identifiers do not allow `.` `/` `-` ` `, leading digits, or non-ASCII |
| 6 | One method per call | Each `duplicate()` triggers Plant Simulation events; combining is risky |
| 7 | `--frame` is required, not auto-default | Silent defaults produce "where did my method go?" confusion |

## Limitations

- **One Method per invocation.** No batching — each `duplicate()` is its own
  Plant Simulation round-trip.
- **No infoBox convention.** This is a thin wrapper; `class_ops.py` already
  emits / closes the non-modal infoBox per the v18→v19 skill convention.
- **No undo.** Plant Simulation has no per-edit undo over SimTalk; an
  accidental Method creation is permanent. Use `--dry-run` to validate
  before the real call.
- **Does NOT write code.** Strictly the empty-container creation. Use
  `local-simtalk-write-simtalk` afterwards.

## Key files

- `scripts/create_method_object.py` — main entry. Validates inputs, delegates
  to `class_ops.py duplicate`, emits JSON envelope.
- `references/simtalk-reserved-words.md` — blocklist with rationale and source
  references.
- `examples/example_session.md` — full end-to-end walk-through.
- `log/` — human-readable session logs.
- `usage_log/` — JSON envelopes from successful runs.

## Related skills

- **`local-simtalk-write-simtalk`** — writes code INTO a given Method. Always
  runs after this skill to fill the container.
- **`local-simtalk-class-management`** — provides the `duplicate` subcommand
  this skill delegates to. Also handles derive / rename / delete / move for
  Class Library objects.
- **`local-simtalk-get-folder-tree`** — find candidate Frames before invoking
  this skill. Recommended pre-flight.
- **`local-simtalk-execution`** — underlying TCP transport for all SimTalk
  calls.