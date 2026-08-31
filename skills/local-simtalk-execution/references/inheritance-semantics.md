# Inheritance semantics (Plant Simulation read-only attributes)

From `01-plantsimulation-knowledge/.../common-read-only-attributes.md`:

| Attribute | Meaning |
|---|---|
| `Origin` | The object from which `<Path>` was derived **most recently** (immediate parent) |
| `OriginRoot` | The **root** of the inheritance chain (built-in class library root) |
| `Class` | The class in the Class Library from which `<Path>` was derived, possibly over several levels |
| `InternalClassType` | The unique built-in English object name describing the type of `<Path>` |

If `<Path>.Origin` returns `VOID`, then `<Path>` is a **root class** in the
Plant Simulation Class Library (a built-in). Otherwise it's a **derived
class** (a user-defined subclass).

## `derive` vs `duplicate`

| Operation | Origin after | When to use |
|---|---|---|
| `<parent>.derive(<dest>, <name>)` | Preserved (inherits from `<parent>`) | Want a child that picks up future parent changes |
| `<source>.duplicate(<dest>, <name>)` | Severed — `Origin` becomes the duplicate itself | Want a one-off snapshot |

## Worked example

> `Frame → Frame2 → Frame3` with `Frame1 → Frame2 → Frame3`:
> - `Frame3.Origin` = `.Frame2` (immediate parent)
> - `Frame3.OriginRoot` = `.Frame1` (top of inheritance chain)
> - `Frame3.Class` = `.Frame3` (the Class Library object — interestingly,
>   Plant Simulation walks back up until it finds the Class Library root)