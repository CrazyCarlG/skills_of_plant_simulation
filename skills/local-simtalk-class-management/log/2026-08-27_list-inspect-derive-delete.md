# Usage log — local-simtalk-class-management: list + inspect + derive + delete

**Date:** 2026-08-27
**Skill:** `local-simtalk-class-management`
**Target:** `.UserObjects` folder (read + write) and `.MaterialFlow.Station` (parent for derive)
**Mode / Action:** `class_ops.py list / inspect / derive / delete` (all `--no-infobox`)
**Operator:** plant-simulation-expert (OpenClaude subagent)

## Goal

Verify the dispatcher's read paths (`list`, `inspect`) and the full
derive→verify→delete lifecycle for a brand-new subclass. Confirm the
JSON envelope shape, the inheritance metadata accuracy (Origin /
OriginRoot / Class), and clean teardown so the model returns to its
baseline.

## Steps

### Test 1a — `list .UserObjects` (read-only)

```bash
python3 skills/local-simtalk-class-management/scripts/class_ops.py --no-infobox list .UserObjects
```

Returned (envelope → children):
```json
{
  "ok": true,
  "subcommand": "list",
  "folder": ".UserObjects",
  "count": 4,
  "children": [
    {"i":1,"name":"PartA","type":"Part","path":".UserObjects.PartA"},
    {"i":2,"name":"PartB","type":"Part","path":".UserObjects.PartB"},
    {"i":3,"name":"Box","type":"Container","path":".UserObjects.Box"},
    {"i":4,"name":"MyFrame","type":"Frame","path":".UserObjects.MyFrame"}
  ]
}
```

Verdict: PASS — 4 user-defined classes enumerated; the script's `###CLASS_OP###`
/ `###CLASS_OP_END###` markers visible in `log_tail` confirm the readlogic
works. Note: `--no-infobox` MUST be **before** the subcommand
(`--no-infobox list ...`), not after — placing it after the subcommand
errors with `unrecognized arguments: --no-infobox` because argparse uses
subparsers.

### Test 1b — `inspect` on a user-derived class + a built-in

```bash
class_ops.py --no-infobox inspect .UserObjects.MyFrame
class_ops.py --no-infobox inspect .MaterialFlow.Station
```

Returned:

| Path | NAME | TYPE | ORIGIN | ORIGINROOT | CLASS | NUMATTRIBUTES | NUMCHILDREN |
|---|---|---|---|---|---|---|---|
| `.UserObjects.MyFrame` | MyFrame | Frame | VOID | `.UserObjects.MyFrame` | VOID | 1 | 0 |
| `.MaterialFlow.Station` | Station | Station | VOID | `.MaterialFlow.Station` | VOID | 0 | 2 |

Observations:
- Both root classes report `Origin = VOID` and `OriginRoot = self` (because
  neither has a parent in user space — they're both terminal roots).
- `.UserObjects.MyFrame` has 1 user-defined attribute (NUMATTRIBUTES=1)
  but 0 children objects under it.
- `.MaterialFlow.Station` has 2 children (likely the `MUs` / `ProcTime`
  etc. sub-objects built into the Station class definition).

Verdict: PASS — both inspect calls return clean JSON with the documented
fields, both correctly identify themselves as root classes.

### Test 2a — `derive .MaterialFlow.Station .UserObjects MyStation` (mutating)

```bash
class_ops.py --no-infobox derive .MaterialFlow.Station .UserObjects MyStation
```

Returned envelope:
```json
{
  "ok": true,
  "subcommand": "derive",
  "data": {
    "BEFORE_PATH": ".MaterialFlow.Station",
    "BEFORE_NAME": "Station",
    "BEFORE_TYPE": "Station",
    "AFTER_PATH": ".UserObjects.MyStation",
    "AFTER_NAME": "MyStation",
    "AFTER_TYPE": "Station",
    "AFTER_ORIGIN": ".MaterialFlow.Station",
    "AFTER_ORIGINROOT": ".MaterialFlow.Station",
    "AFTER_CLASS": "VOID"
  }
}
```

Observations:
- **Inheritance chain is correct.** New `MyStation` has `Origin = .MaterialFlow.Station`
  (immediate parent) and `OriginRoot = .MaterialFlow.Station` (root of chain — same as
  parent, since parent is a built-in).
- **Class=VOID** because there is no user-derived class between MyStation and the
  root; this is consistent with the Plant Simulation help (§common-read-only-attributes.md):
  `Class` is the user-space class in the chain, which doesn't exist when the chain is
  directly `<user-derived> → <built-in>`.

Verdict: PASS — derive operation succeeded; the new class is in `.UserObjects`
and inherits from the named built-in parent.

### Test 2b — `list .UserObjects` (verify derive stuck)

```bash
class_ops.py --no-infobox list .UserObjects
```

Returned: 5 entries (the new MyStation appended at i=5).

Verdict: PASS — MyStation is now a real child of `.UserObjects`.

### Test 2c — `delete .UserObjects.MyStation` (cleanup)

```bash
class_ops.py --no-infobox delete .UserObjects.MyStation
```

Returned:
```json
{
  "ok": true,
  "subcommand": "delete",
  "data": {
    "BEFORE_PATH": ".UserObjects.MyStation",
    "RESULT": "deleted"
  }
}
```

`RESULT: deleted` means the underlying `obj.deleteObject` returned `true`
(no live instances blocking — expected for a freshly-derived class with
no instances yet). The script surfaces the boolean correctly per the
Quirk CM-4 contract.

Verdict: PASS — cleanup succeeded.

### Test 2d — `list .UserObjects` (re-verify)

```bash
class_ops.py --no-infobox list .UserObjects
```

Returned `count: 4` (back to baseline PartA / PartB / Box / MyFrame).

Verdict: PASS — model state restored.

## Result

| # | Subcommand | Path | Outcome | Verdict |
|---|---|---|---|---|
| 1a | `list` | `.UserObjects` | 4 children enumerated | ✅ |
| 1b | `inspect` | `.UserObjects.MyFrame` | user-derived root, 1 UDA, 0 children | ✅ |
| 1b | `inspect` | `.MaterialFlow.Station` | built-in root, 0 UDAs, 2 children | ✅ |
| 2a | `derive` | `.MaterialFlow.Station` → `.UserObjects.MyStation` | new class with Origin=.MaterialFlow.Station | ✅ |
| 2b | `list` (re-verify) | `.UserObjects` | 5 entries (MyStation appended) | ✅ |
| 2c | `delete` | `.UserObjects.MyStation` | `RESULT:deleted` | ✅ |
| 2d | `list` (cleanup verify) | `.UserObjects` | back to 4 entries | ✅ |

## Verdict

PASS — 7/7 subcommands clean. The dispatcher correctly composes SimTalk
snippets, sends them via `simtalk_send.py`, and surfaces the JSON envelope
with `before`/`after`/`data`/`log_tail` fields. Derive semantics match
Plant Simulation's documented Origin / OriginRoot / Class triple.
Cleanup leaves the model in its baseline state.

## What this run validated / learned

- **`--no-infobox` MUST come BEFORE the subcommand.** argparse uses
  subparsers, so `class_ops.py list .UserObjects --no-infobox` errors
  with `unrecognized arguments: --no-infobox`. Correct form:
  `class_ops.py --no-infobox list .UserObjects`. This is the **opposite**
  position convention from the folder-tree / read-library / add-note
  scripts where `--no-infobox` was a trailing positional arg. **Document
  this in the SKILL.md usage example to save future operators a wasted
  round-trip.**
- **The JSON envelope shape is stable.** All subcommands return
  `ok` (bool), `subcommand` (str), `exit_code` (int), `data` (dict),
  and `log_tail` (last ~200 chars of server log). Mutating ops add
  `before`/`after` fields. Read-only ops add the relevant payload field
  (`children` for `list`, `data` for `inspect`).
- **`Origin` vs `OriginRoot` vs `Class` semantics verified.**
  - `Origin` = immediate parent (what was derived from most recently).
  - `OriginRoot` = topmost class in the inheritance chain.
  - `Class` = first user-space class in the chain (skips built-ins).
  - For a user class derived directly from a built-in
    (`MyStation ← MaterialFlow.Station`), all three converge on
    `.MaterialFlow.Station` IF we ignore the built-in root semantics,
    but `Class=VOID` because `Class` only points to user-space classes.
    Built-in roots themselves have `Origin=VOID`, `OriginRoot=self`.
- **Delete on a freshly-derived class with no instances returns
  `true` immediately.** Quirk CM-4 (`deleteObject` returns `false` if
  the class has live instances) didn't trigger here because MyStation
  had no instances. The script surfaces the boolean correctly via
  `RESULT:deleted`. To exhaustively test Quirk CM-4, would need to
  first `duplicate()` the class into a Frame (which creates an
  instance), then attempt `delete` — out of scope for this run but
  noted for future testing.
- **The `derive` subcommand is safe with explicit name.** Quirk CM-1
  warns about silent name suffixing when `name` is omitted; this run
  always passed an explicit name (`MyStation`) and got exactly that
  name back — no `_2` suffix. Confirmed: always pass `name`.
- **`class_ops.py` reads via `print` + readlog extraction** (the
  `###CLASS_OP###` / `###CLASS_OP_END###` markers visible in `log_tail`),
  same approach as `add_note.py` but using **markers the script itself
  emits** to bracket each operation. This means: as long as the script's
  emit-order matches the read-extract-order, the readback is reliable.
  The v15+ readlog regression (per `local-simtalk-execution` §5) might
  still bite on long log buffers, but for the small sub-second operations
  in this skill it's not a problem.
- **The skill's `infoBox` convention (`infoBox(text, false)` on entry,
  close twice on exit) was bypassed via `--no-infobox` for these
  headless test runs.** A future run with the GUI visible should
  confirm the infoBox lifecycle visually — but the open/close path is
  verified by the smoke test in the modify-object-attribute log
  (`infoBox("msg", false)` returns `result:"success"` without blocking).
- **All cleanup confirmed** — `.UserObjects` is back to its baseline
  4 classes (PartA / PartB / Box / MyFrame). Subsequent skill tests
  have an untouched Class Library to work with.