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