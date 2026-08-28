# Protocol Notes — Class Management Write Side

> **Status:** v1 scaffold. To be filled in after the first end-to-end
> session against the running server. The notes below document the
> protocol-level constraints inherited from
> `local-simtalk-execution/references/lifelines.md` plus a small number
> of write-side quirks specific to class mutations.

## Inherited from `local-simtalk-execution`

These rules apply unchanged to every `class_ops.py` invocation. Refer
to the source skill for the canonical wording — they are summarised
here only as a checklist.

| # | Rule | Source |
|---|---|---|
| L1 | Default target is `host.docker.internal:50007` (WSL2 → host) | lifelines §1 |
| L2 | All payloads are framed with `\|\|END\|\|` | lifelines §2 |
| L3 | `type` is one of `ping` / `simtalk_syntax` / `simtalk_run` / `readlog` | lifelines §3 |
| L4 | No `prompt` / modal `infoBox` / undeclared global attrs | lifelines §4 |
| L5 | `readlog` v15+ is unreliable (feedback-loop bug, captures no print output) | lifelines §5 |
| L6 | `simtalk_run` returns `result:"success"` even on runtime exceptions; double-check `log` starts with `code execute failed` | lifelines §6 / team memory |
| L7 | `data` field of `simtalk_run` reply is always empty | lifelines §6 |

The dispatcher surfaces L6 by mapping the exit code returned from
`simtalk_send.py run`:

| Exit | Meaning |
|---|---|
| 0 | semantic success — `data` block parsed |
| 10 | compile / non-success `result` — server rejected the code |
| 11 | Quirk #7 soft failure — `result=success` but `log` starts with `code execute failed` (runtime exception) |
| 12 | bad JSON from server (rare; usually means schema violation) |
| 1 / 2 / 3 | socket-level failure (timeout / cannot connect / mid-flight disconnect) |

## Write-side quirks specific to this skill

> These will be filled in as we exercise each subcommand against the
> real server. Initial scaffolded expectations based on the SimTalk
> documentation:

### CM-1 — `derive` silently picks a unique name suffix on collision

The `derive` SimTalk method takes a `Name:string` parameter but
**returns a non-void object even when the requested name is already
taken** — Plant Simulation appends `_2`, `_3`, etc. (This matches the
behavior described in `common-methods.md`.)

The dispatcher records the **actual** returned `AFTER_NAME` rather than
the requested name, so the envelope always reflects reality. If you ask
for `MyStation` and Plant Simulation assigns `MyStation_2`, the
envelope reports `AFTER_NAME: "MyStation_2"` and `AFTER_PATH:
".UserObjects.MyStation_2"`. To avoid this, use
`local-simtalk-get-class-inheritance` (or `inspect`) first to confirm
the name is unique.

### CM-2 — Folder/Frame cannot be derived

The dispatcher does **not** validate that `<parent>` is a class (vs.
a Folder/Frame). Plant Simulation's `derive` will compile against any
object, but on a Folder/Frame it produces a runtime exception. The
exception surfaces as Quirk #7 (exit 11) with the SimTalk error in
the `log` field.

**Workaround:** always pre-check the parent with
`class_ops.py inspect <path>` and confirm `NUMATTRIBUTES > 0` or
`InternalClassType` is not `"Folder"`/`"Frame"` before issuing
`derive`.

### CM-3 — `setName` rejects `EventController` and `Connector`

Plant Simulation reserves these two names. Calling `setName` on them
returns `false` (the dispatcher reports
`ERR:setName_returned_false:name_not_unique_or_reserved`). You cannot
work around this — it is by design.

### CM-4 — `deleteObject` returns false when live instances exist

A class with one or more instances in any Frame cannot be deleted.
The SimTalk method returns `false` and the class remains. To find the
blocking instances, use `local-simtalk-get-class-inheritance` or call
`Show Inheritance` in the GUI.

### CM-5 — `moveToFolder` requires an existing Folder

The destination path must resolve to an existing Folder. Passing a
class path or a non-existent path raises a runtime exception. The
dispatcher pre-validates with `str_to_obj` and returns
`ERR:dest_folder_does_not_resolve:<path>` before sending the move
call.

### CM-6 — `createAttr` types must match Plant Simulation's type vocabulary

The type literal is passed verbatim. The known-good list (as of
Plant Simulation Help 2606) is: `integer`, `real`, `boolean`,
`string`, `length`, `time`, `speed`, `acceleration`, `weight`,
`currency`, `object`, `method`, `list`, `table`, `stack`, `queue`,
`dataList`, `dataTable`, `any`. Anything else returns
`ERR:createAttr_returned_false:name_collision_or_invalid_type`.

### CM-7 — UDA names are case-sensitive and unique per object

`<path>.createAttr("Foo", ...)` then `createAttr("foo", ...)` succeeds
with two distinct UDAs. Renaming one to the other's name later is
rejected by `setName` for the UDA itself (CM-3 doesn't apply here,
but the principle does — `isNameUnique` is the way to check).

### CM-8 — `set-attr` heuristic for value types

The dispatcher parses simple types from the CLI string (integer,
real, boolean, string). Anything else is emitted as a string literal
which will fail at runtime if the UDA's declared type disagrees. For
complex values (lists, tables, object refs), write the SimTalk by hand
and send via `local-simtalk-execution`.

### CM-9 — `infoBox` is idempotent but the open call is non-atomic

The dispatcher opens the infoBox on entry and closes it twice on
exit. If the SimTalk call hangs (network timeout), the infoBox stays
up until the Plant Simulation GUI is interacted with. There is no
guaranteed close on timeout — operators should keep an eye on the GUI
during long-running sessions.

### CM-10 — `duplicate()` behavior depends on destination type (revised Q-B7)

`<Class>.duplicate(parent, name)` produces **different outputs** depending
on the type of `<parent>`:

- **Folder destination** (e.g. `<Class>.duplicate(.UserObjects, "MyClass")`)
  → creates a **new top-level class** with `Origin = VOID` and `Class = VOID`
  — inheritance is **cut** from the source. The new class is independent.
- **Frame destination** (e.g. `<Class>.duplicate(.Models.Model, "MyStation")`)
  → creates a **runtime instance** of `<Class>` placed inside the Frame.
  `Origin` / `Class` both point to the source class — inheritance is
  **preserved**.

The `common-methods.md` docs say "creates a new class" — this is **only
true for Folder destinations**. Frame destinations produce instances,
not classes. If you wanted an instance, that's the right call; if you
wanted a sibling class, you actually wanted a Folder destination.

**Source:** `log/session-20260826.md` Part D lines 354-372.

### CM-11 — `Frame.NumChildren` does NOT enumerate placed-in-Frame objects (revised Q-B8)

`Frame.NumChildren` and `Frame.node(i)` enumerate **structural** children
only — sub-Frames and sub-Folders that exist as part of the Frame's
definition. They do **not** enumerate **placed** instances (objects dropped
into the Frame at edit-time as instances of some class).

To detect whether an instance is placed in a Frame, use:
```simtalk
var found: object
found := <frame>.extendPath(<name>)   -- returns the object or VOID
```

`extendPath(name)` returns the object reference if `<name` is present as
either a structural child or a placed instance, and `VOID` otherwise. This
is the only reliable check for instance presence.

**Source:** `log/session-20260826.md` Part E lines 515-535.

### CM-12 — Definitive class-vs-instance test is `Origin` / `Class` (revised Q-B9)

Both `Origin` and `Class` are checked together:

- **Class** (top-level in class library): `Origin = VOID` **and** `Class =
  VOID` (OriginRoot = self). The object IS the class definition; nothing
  inherits from it via this object.
- **Instance** (placed in a Frame): `Origin != VOID` **and** `Class != VOID`,
  with both pointing back to the source class. The instance inherits
  everything from its source.

This is the canonical test. Other heuristics (e.g. `InternalClassType`
matching a known class name, path starting with `.UserObjects.`) are
ambiguous — a Frame placed inside a user Folder looks the same as a class
on those heuristics.

**Source:** `log/session-20260826.md` Part F lines 666-672.

### CM-13 — `setPosition` is a method call, NOT an LVALUE attribute (revised Q-B10)

`<obj>.setPosition` is a **method call**, not an attribute:

```simtalk
<obj>.setPosition(100, 100)            -- ✅ method call form
<obj>.setPosition(100, 100, true)      -- with optional CallMoveInFrameControl

<obj>.setPosition := [100, 100]        -- ❌ compile/runtime error
```

The `[100, 100]` array notation in `common-methods.md` is **wrong**;
follow the method-call form (lines 415+ in that doc, not the array
notation at the top).

### CM-14 — `derive` vs `duplicate` to same destination type produce different classes (revised Q-B11)

| Operation | Destination | Result |
|---|---|---|
| `<Class>.derive(<frame>, "X")` | any Frame | **subclass** (Origin = source) |
| `<Class>.duplicate(<folder>, "X")` | Folder | **standalone class** (Origin = VOID) |
| `<Class>.duplicate(<frame>, "X")` | Frame | **runtime instance** (Origin = source) |

All three are documented as "creates something new", but the inheritance
semantics differ. Pick by intent:

- "I want a subclass to override behavior" → `derive(<frame>, name)`
- "I want a sibling class with no inheritance" → `duplicate(<folder>, name)`
- "I want a runtime instance of this class in my model" → `duplicate(<frame>, name)`

**Source:** `log/session-20260826.md` Parts D-F summary.

### CM-15 — `derive` with no args auto-suffixes on collision (revised Q-B12)

`<Class>.derive(<frame>)` (no name arg) places the new class next to the
source in the class-library tree. If the source name is already taken at
that location, Plant Simulation auto-suffixes with `_2`, `_3`, etc. (same
as the `derive(<frame>, name)` collision behavior — see CM-1).

For the no-arg form, the returned object's `Name` attribute carries the
actual assigned name (with suffix if applicable). Capture and report it
to the caller so they don't get surprised by a `_2`-suffixed class they
didn't ask for.

**Source:** `log/session-20260826.md` Parts D-F summary.

### CM-16 — `class_ops.py --no-infobox` MUST come BEFORE the subcommand

argparse uses subparsers; `class_ops.py list .UserObjects --no-infobox`
errors with `unrecognized arguments: --no-infobox`. The **opposite** of
folder-tree / read-library / add-note scripts where `--no-infobox` was a
trailing positional arg.

**Correct:** `class_ops.py --no-infobox list .UserObjects`

**BAD:** `class_ops.py list .UserObjects --no-infobox`

**Source:** `log/2026-08-27_list-inspect-derive-delete.md` §"Steps Test 1a"
lines 22-46.

## Folder-vs-Frame destination distinction in `duplicate()`

While `<Class>.duplicate(<Frame>, <name>)` **can** place a runtime
instance into a Frame (per CM-10/CM-11/CM-12 above), that operation is
**outside this skill's class-library scope**. The skill targets class
definitions, not instances placed in simulation Frames. For instance-side
work, use raw `local-simtalk-execution` directly.

This clarifies the prior Limitations wording "No instance manipulation" —
true for `class.create` but misleadingly suggests `duplicate(frame,...)`
doesn't work. It does work; it's just not this skill's responsibility.

## Recommended pre-flight checklist

Before invoking a mutating op in a session:

1. Run `class_ops.py inspect <path>` to confirm the source exists and
   to capture the current `Origin` / `OriginRoot` / `Class`.
2. (Optional) Run `class_ops.py list <folder>` to verify the
   destination folder and avoid name collisions.
3. Run the mutating op (e.g. `derive` / `duplicate` / `rename`).
4. Inspect the result via `class_ops.py inspect <new_path>` to confirm
   the change.

For batch operations (renaming many classes), wrap the loop in a
shell `for` loop and parse each envelope — do **not** add a batch
mode to `class_ops.py` (each op must be its own SimTalk call so a
mid-batch failure leaves a clear state).

## Session log

Successful and failed runs should be appended to `log/session-YYYYMMDD.md`
after each session so the next operator can see what was tried and
what the server's actual responses were. The dispatcher itself does
not write to the log file — the calling skill (Claude) is responsible
for summarising and persisting the envelopes.