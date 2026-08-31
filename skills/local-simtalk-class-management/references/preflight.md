# Pre-flight rule — build the inheritance map before mutating

Before invoking **any** mutating subcommand in `local-simtalk-class-management`
(`derive` / `duplicate` / `rename` / `delete` / `move` / `add-attr` /
`set-attr` / `del-attr` / `inherit-attr`), first call the sibling skill
`local-simtalk-get-class-inheritance` to understand the inheritance
relationships between the candidate classes. Read-only ops (`list`,
`inspect`) do **not** require this step.

## Why the inheritance map must come first

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

## Recommended workflow

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