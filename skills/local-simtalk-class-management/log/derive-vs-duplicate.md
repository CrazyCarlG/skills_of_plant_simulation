# `derive` vs `duplicate` — Reference

> **Status:** Verified against Plant Simulation 2606.0002 (server
> `host.docker.internal:50007`, August 2026). All server-reply
> quotations in this doc are taken from `session-20260826.md` Parts D,
> E, and F.

This document captures the definitive distinction between `derive` and
`duplicate` in Plant Simulation's SimTalk API, and the related
class-vs-instance question. It is the reference companion to the
chronological session log.

---

## TL;DR — Decision matrix

| You want | Use | Example |
|---|---|---|
| **Subclass** that inherits from source (can override parent attributes/methods) | `derive(folder, name)` | `.MaterialFlow.Station.derive(.Models, "MyStation")` |
| **Subclass** next to the source (no destination arg) | `derive` (no args) | `.MaterialFlow.Station.derive` → `.MaterialFlow.Station2` |
| **Standalone class** with no parent (inheritance cut) | `duplicate(folder, name)` | `.MaterialFlow.Station.duplicate(.Models, "MyCopy")` |
| **Runtime instance** placed in a Frame | `duplicate(frame, name)` | `.MaterialFlow.Station.duplicate(.Models.Model, "MyInst")` |
| **Runtime instance** via inheritance-style API | `derive(frame, name)` | `.MaterialFlow.Station.derive(.Models.Model, "MyInst2")` |

The last two are equivalent — both produce an instance. Prefer
`duplicate(frame, name)` because the name "duplicate" maps directly
to the "copy an existing class definition into a Frame as an instance"
intent.

---

## Concepts

### Class vs Instance

Plant Simulation distinguishes two kinds of objects at any given path:

- **Class** — a *template* / *definition* in the Class Library. Lives
  inside a **Folder** (e.g. `.MaterialFlow.Station`).
- **Instance** — a *runtime object* placed inside a **Frame** (e.g.
  the Station you drag from the toolbox into a Frame's 2D view).

Both have the same `InternalClassType` (e.g. `Station`). They are
distinguished by their **`Origin` / `Class` / `OriginRoot` triple**.

### The Origin / Class / OriginRoot triple

This is the **definitive class-vs-instance test**. `NumChildren`,
`InternalClassType`, and the path string are all ambiguous.

| Attribute | Class | Instance | Root class (built-in) |
|---|---|---|---|
| `Origin` | `VOID` | the source class | `VOID` |
| `Class` | `VOID` | the source class | `VOID` |
| `OriginRoot` | the class's own path | the source's `OriginRoot` | the class's own path |

**Rule:** both `Origin` AND `Class` `VOID` ⇒ **class**.
Both non-`VOID` ⇒ **instance**.

---

## `derive` — creates a subclass (inheritance always preserved)

```simtalk
<source>.derive([destination:object, name:string, seed:integer]) → object
```

- **Always** creates a class. Destination type does not matter for
  the class-vs-instance question; what matters is whether the result
  is meant to be a class definition or an instance.
- **Origin** = the source class (inheritance preserved, can override).
- **Class** = `VOID` (no separate class definition).
- **OriginRoot** = the source's `OriginRoot` (i.e. the original root
  class in the inheritance chain).
- With no args, places the new class **next to the source** in the
  class library tree; auto-suffixes with `_2` if the source name is
  already taken (e.g. `.MaterialFlow.Station.derive` →
  `.MaterialFlow.Station2`).
- Documents: `common-methods.md` line 129.

### Examples

```simtalk
-- A) Default placement (next to source, auto-suffix on conflict)
.MaterialFlow.Station.derive
-- Result: .MaterialFlow.Station2
-- Origin=.MaterialFlow.Station, Class=VOID, OriginRoot=.MaterialFlow.Station

-- B) Explicit folder destination
.MaterialFlow.Station.derive(.Models, "DerivedStation")
-- Result: .Models.DerivedStation
-- Origin=.MaterialFlow.Station, Class=VOID, OriginRoot=.MaterialFlow.Station

-- C) Frame destination — creates an INSTANCE (uncommon; equivalent to duplicate(Frame))
.MaterialFlow.Station.derive(.Models.Model, "DerivedInFrame")
-- Result: .Models.Model.DerivedInFrame
-- Origin=.MaterialFlow.Station, Class=.MaterialFlow.Station
--             ↑ both non-VOID → instance
```

---

## `duplicate` — creates a copy; behavior depends on destination type

```simtalk
<source>.duplicate([destination:object, name:string]) → object
```

**Destination type determines the result:**

| Destination | Result | Origin | Class | OriginRoot |
|---|---|---|---|---|
| **Folder** | **Class** (standalone) | `VOID` | `VOID` | self path |
| **Frame**  | **Instance** (inherits) | source | source | source's OriginRoot |

### Examples

```simtalk
-- A) Folder destination — standalone class (inheritance cut)
.MaterialFlow.Station.duplicate(.Models, "ClassStation")
-- Result: .Models.ClassStation
-- Origin=VOID, Class=VOID, OriginRoot=.Models.ClassStation
-- → new top-level class with NO parent

-- B) Frame destination — runtime instance (inheritance preserved)
.MaterialFlow.Station.duplicate(.Models.Model, "InstStation")
-- Result: .Models.Model.InstStation
-- Origin=.MaterialFlow.Station, Class=.MaterialFlow.Station
--             ↑ both non-VOID → instance
```

### Instance-specific operations on a Frame-destination duplicate

Once you have an instance via `duplicate(frame, name)`, you can:

```simtalk
var s := .MaterialFlow.Station.duplicate(.Models.Model, "MyInst")

-- Position the icon in the Frame (instance-only)
s.setPosition(100, 200)

-- Set runtime attributes
s.ProcTime := 5.0

-- Find it again via extendPath
.Models.Model.extendPath("MyInst")   -- returns `s`, or VOID if deleted
```

`setPosition` is a **method call** `setPosition(X:integer, Y:integer)`,
NOT an LVALUE. The docs example
`MyConveyor.setPosition := [100, 100]` (`common-methods.md` line 167)
is **wrong** — the server rejects that syntax. Use the method-call
form (line 419).

---

## Common pitfalls

| Symptom | Cause | Fix |
|---|---|---|
| `Unknown identifier 'X'` on `cls.create(frame)` for a non-MU class | `create` is MU-only (Transporter, Container, Box, Part, …) and Worker / DataTable. Not defined on Station / Conveyor / Source / Drain / Buffer / etc. | Use `duplicate(frame, name)` instead. |
| `Unknown identifier 'X'` on `.ParentFrame.X` (path navigation) | Plant Simulation does **not** auto-create instances from a class-library class of the same name when the path is missing. | Use `duplicate` first, then navigate. |
| `Wrong number of parameters in setPosition: 1 passed` when calling `setPosition([100, 100])` | `setPosition` takes **two integer args** `(X, Y)`, not a single array. | Use `setPosition(100, 200)`. |
| `You cannot assign a value to the expression on the left hand side of the assignment` on `<obj>.setPosition := [...]` | `setPosition` is a method, not an LVALUE attribute. | Use method-call form `setPosition(100, 200)`. |
| `Frame.NumChildren = 0` after placing instances in the Frame | `Frame.NumChildren` only counts **structural** sub-children (sub-Frames, sub-Folders). It does **not** enumerate placed-in-Frame objects. | Use `Frame.extendPath(name)` to detect specific instances. |
| Got a `class` (Origin=VOID) when I expected an `instance` | Used `duplicate(folder, name)` instead of `duplicate(frame, name)`. The destination was a Folder, so the result is registered into the class library tree, not placed as a runtime instance. | Use a Frame as the destination. |

---

## Verification matrix (server-confirmed, Aug 2026)

```
SOURCE: .MaterialFlow.Station (built-in root class, Origin=VOID, Class=VOID)

METHOD                  DEST                 RESULT                          ORIGIN                       CLASS                        ORIGINROOT
─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
derive                  (no args)            .MaterialFlow.Station2          .MaterialFlow.Station         VOID                         .MaterialFlow.Station
derive(.Models, ...)    Folder               .Models.DerivedStation          .MaterialFlow.Station         VOID                         .MaterialFlow.Station
derive(.Models.Model)    Frame                .Models.Model.DerivedInFrame    .MaterialFlow.Station         .MaterialFlow.Station        .MaterialFlow.Station   ← instance
duplicate(.Models, ...) Folder               .Models.ClassStation            VOID                          VOID                         .Models.ClassStation
duplicate(.Models.Model) Frame               .Models.Model.InstStation       .MaterialFlow.Station         .MaterialFlow.Station        .MaterialFlow.Station   ← instance
```

The `Origin/Class/OriginRoot` triple is the **only reliable test**.
The class-vs-instance split is the same for `derive` and `duplicate`:
both VOID = class, both non-VOID = instance.

---

## See also

- `session-20260826.md` — full chronological log of the probes that
  produced this reference (Parts A → F).
- `01-plantsimulation-knowledge/01-plant-simulation-help/objects/common-methods/common-methods.md`
  lines 129-170 — official `derive` / `duplicate` definitions (note:
  the `setPosition` example at line 167 contradicts runtime behavior).
- `01-plantsimulation-knowledge/01-plant-simulation-help/objects/common-read-only-attributes/`
  — Origin / Class / OriginRoot / InternalClassType definitions.
