# Quirks — gotchas discovered while modifying Plant Simulation attributes

> This file collects the real-world gotchas encountered when running the
> `local-simtalk-modify-object-atrribute` skill against a live server. Each
> entry includes a brief explanation and a workaround. The hard rules from
> `local-simtalk-execution/references/lifelines.md` still apply; this file
> is the **layered, attribute-specific** overlay.

## Q1. `readlog` is unreliable in v15+ — but still works for marker-grep

Per `local-simtalk-execution/references/lifelines.md` §5, the v15+ server
build (2606.0002) regressed `readlog` to v12 behavior:

- buffer-explosion feedback loops in tight reads
- may not capture `print` output at all
- may show stale entries from prior requests

**In practice (2026-08-26 verification session):** the marker-grep pattern
(`###MARKER### ... ###END###`) worked on every `simtalk_run` followed by a
single `readlog`. The pattern succeeded 4/4 times against this server.
However, do not put `readlog` in a tight loop — only call it once per
`simtalk_run` and only after a real write.

**Workaround if `readlog` returns empty:** retry once. If still empty, the
write may have failed (Quirk #7 — `result:"success"` with
`log:"code execute failed..."`), or the print output never made it to the
log. Fall back to manual GUI console inspection (Window ribbon → Console).

## Q2. `data` field is always empty (Quirk #6)

The `simtalk_run` envelope's `data` field never carries a value, even when
the SimTalk ends in `return X` with a `-> T` declaration. Don't waste a
round-trip checking it.

**Workaround:** use `print(X)` + `readlog` to recover values.

## Q3. Runtime errors are reported as `result:"success"` (Quirk #7)

A SimTalk runtime exception (unknown identifier, division by zero,
dereferencing `void`, etc.) does **not** set `result:"failed"`. Instead:

- `result` = `"success"`
- `log` = `"code execute failed. error msg:<details>"`

This is by design — see the persistent team memory at
`/root/.openclaude/projects/-root-skills-of-plant-simulation/memory/team/simtalk-run-soft-failure-design.md`.
**Always** check both fields:

```text
result == "success"  AND  not log.startswith("code execute failed")
```

`scripts/attr_modify.py` implements this check and exits with code 11 if it
fails.

## Q4. Undeclared-attribute writes hang the socket (modal trap)

If `<ATTR>` doesn't exist on the object, Plant Simulation pops a modal
dialog: "Create this attribute?". Until the operator clicks Yes/No, the
server thread is blocked and `simtalk_send.py` will time out.

**Workaround:** always confirm the attribute exists in the Plant Simulation
knowledge base first:

```
01-plantsimulation-knowledge/01-plant-simulation-help/objects/<type>/attributes/attributes.md
```

The `<type>` is the object's `InternalClassType` — e.g. `EventController`,
`Buffer`, `Source`.

## Q5. `str_to_obj` returns `void` for unloaded paths

If the path isn't loaded (e.g., a class library node that hasn't been
instantiated, or a typo), `str_to_obj` returns `void`. Dereferencing
`void.<attr>` triggers Quirk #7 with `error msg:Unknown identifier` or
similar.

**Workaround:** the helper script checks for `void` and prints an `ERR:`
line via the marker, exiting with code 11. If you write SimTalk by hand,
always include the `if obj = void` guard (see `code-templates.md`).

## Q6. `.SimtalkClaude.*` is off-limits by user convention

The user has explicitly excluded the `.SimtalkClaude` folder from any
skill-driven modification. `scripts/attr_modify.py` enforces this by
refusing any path containing `.SimtalkClaude` (case-insensitive) and
exiting with code 2.

**Workaround:** if you need to modify something inside `.SimtalkClaude`,
do it manually in the Plant Simulation GUI or via direct file editing.

## Q7. Boolean literals are case-insensitive in SimTalk

`obj.<ATTR> := true` and `obj.<ATTR> := TRUE` are both accepted. The
helper script lowercases the input and also accepts `1` / `yes` for
`true`, and `0` / `no` for `false`.

## Q8. `to_str()` on `dateTime` / `time` produces human-readable form

After a `dateTime` or `time` write, `to_str()` returns a formatted string
(not the raw internal representation). This means the `before` and
`after` values printed via markers may differ slightly in formatting even
when they represent the same time — compare **semantically**, not byte-for-byte.

## Q9. `length` type coerces from integer literals

The `length` type accepts integer literals without complaint
(`obj.lengthAttr := 5` is fine even if the underlying unit expects meters).
The helper script accepts both `integer` and `real` literals for `length`
attributes — it just emits the raw value into the SimTalk literal slot.

## Q10. Path strings must use Plant Simulation syntax

- `.` — basis root (anonymous, can't be passed to `str_to_obj`)
- `.Models.Model` — Frame at `<basis>/Models/Model`
- `.Models.Model.EventController` — child node by name

Leading dot required. **No backslash paths, no slashes, no bracket indexing.**
`node(i)` works for index-based access inside SimTalk but can't be passed
through `str_to_obj`.

## Q11. `--batch` is not transactional

If attribute 2 of 3 in a `--batch` run fails after attribute 1 already
succeeded, attribute 1 will be modified and `--restore` will only restore
based on what it captured (the modified value, not the original).

**Workaround:** for atomic modifications, write a single `simtalk_run`
that does all writes in one SimTalk transaction (see
`code-templates.md` §"Multiple attributes on the same object"). Use the
helper for single attributes or for cases where partial-failure rollback
is acceptable.

## Q12. The helper exits 11 on Quirk #7, 10 on compile errors

`simtalk_send.py` exit codes:
- `0` — semantic success
- `10` — `result != "success"` (compile error or result="timeout")
- `11` — Quirk #7 (runtime exception with soft-failure semantics)

`scripts/attr_modify.py` propagates these directly. If you wrap the helper
in CI, gate on `exit_code == 0` and treat 10/11 as failures.