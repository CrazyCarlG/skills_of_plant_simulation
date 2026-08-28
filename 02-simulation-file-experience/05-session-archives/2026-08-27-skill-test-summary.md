---
last_updated: 2026-08-27
contributors: [@z004bjuu, @plant-simulation-expert]
scope: 9 个 `local-simtalk-*` 技能全量测试的覆盖矩阵 + 经验教训（一次性 session 报告，不再追加）
---

# Skill test summary — 2026-08-27

**Date:** 2026-08-27
**Scope:** Exercise every skill in `skills/local-simtalk-*` at least twice
with full usage logs.
**Operator:** plant-simulation-expert (OpenClaude subagent) + user-driven
session.

## Coverage matrix

| # | Skill | Fresh logs (this session) | Sub-areas touched | Verdict |
|---|---|---|---|---|
| 1 | `local-simtalk-execution` | `2026-08-27_ping-syntax-run-readlog.md`, `2026-08-27_ping-syntax-run-readlog-2.md` | ping, syntax, run, readlog, infoBox lifecycle | PASS |
| 2 | `local-simtalk-get-folder-tree` | `2026-08-27_basis-and-models-model-tree.md` | `.Basis` tree + `.Models.Model` tree (BFS) | PASS |
| 3 | `local-simtalk-get-class-inheritance` | `2026-08-27_instances-and-root-classes.md` | `obj.Class`, `obj.Origin`, `obj.OriginRoot`, `rootClasses` | PASS |
| 4 | `local-simtalk-read-library` | `2026-08-27_probe-methods-1path-and-3path.md` | `probe_methods.py` single + multi-path | PASS |
| 5 | `local-simtalk-write-simtalk` | `2026-08-27_flow-a-replace-and-flow-b-duplicate.md` | Flow A replace, Flow B `.&Method.duplicate()` | PASS |
| 6 | `local-simtalk-add-note-to-method` | `2026-08-27_readlogic-readlog-pollutes-backup.md` | `add_note.py` bug exposure + raw-socket workaround | FAIL (script) / PASS (workaround) |
| 7 | `local-simtalk-modify-object-attribute` | `2026-08-27_eventcontroller-batch-and-boolean.md` | read-only, boolean + restore, batch real+integer + restore | PASS |
| 8 | `local-simtalk-class-management` | `2026-08-27_list-inspect-derive-delete.md` | list, inspect (user + built-in), derive, delete | PASS |
| 9 | `local-simtalk-os-functions` | `2026-08-27_misc-pid-env-path-cwd.md` | `getApplicationProcessID`, `availableMemory`, `getEnv`, `getCurrentDirectory`, `strLen`, `strCopy` | PASS |

**9 / 9 skills exercised, 9 fresh usage logs written.**

## Highlights / lessons learned this session

- **Quirk #7 soft failure contract verified across 9 skills.** Every
  `simtalk_run` reply with `result:"success"` + `log:"code execute
  failed..."` is a runtime exception, not a server bug. Per the team
  memory note `simtalk-run-soft-failure-design.md`, this is by design —
  the result field is "did the code compile + enter execution", the log
  field carries the error.

- **Quirk #15 (`.&Method.duplicate()` required for new Methods) verified.**
  Three `create()` variants all fail; `.&Method.duplicate(<frame>, <name>)`
  with `&` on the class name + object-ref frame (NOT string) is the only
  reliable Method-creation path. Documented in
  `local-simtalk-write-simtalk/log/2026-08-27_flow-a-replace-and-flow-b-duplicate.md`.

- **`add_note.py` has a real, exploitable bug.** The `readlogic` reads
  the polluted server Console log buffer instead of trusting the
  `simtalk_run` reply directly. The on-disk backup is corrupted as a
  consequence; `--restore` is useless. Workaround: raw `socket_client.py`
  with `chr(10)`-joined SimTalk string literals and the existing
  `o.program := src;` write pattern. The skill's SKILL.md is honest
  about the risk but the implementation chose the degraded read path
  anyway — flagged for refactor (see
  `local-simtalk-add-note-to-method/log/2026-08-27_readlogic-readlog-pollutes-backup.md`).

- **SimTalk 2.0 strings: `strLen(s)`, not `s.length` / `s.numCharacters`.**
  Caught in `local-simtalk-os-functions` Test 2; correct path is the
  top-level `strLen(s)` function (per
  `predefined-functions-i-os-math-string-datetime/string-functions/string-functions.md`).
  String slicing uses `strCopy(s, pos, n)`, not `s.copy(...)`.

- **`argparse subparsers` and `--no-infobox` position.** For
  `class_ops.py`, `--no-infobox` MUST come **before** the subcommand
  (`class_ops.py --no-infobox list .UserObjects`). Placing it after the
  subcommand errors with `unrecognized arguments: --no-infobox`. This is
  the opposite of folder-tree / read-library / add-note scripts.
  Documented in
  `local-simtalk-class-management/log/2026-08-27_list-inspect-derive-delete.md`.

- **`Origin` / `OriginRoot` / `Class` triple semantics verified.** For a
  user class derived directly from a built-in
  (`MyStation ← MaterialFlow.Station`), `Origin` = immediate parent
  (`.MaterialFlow.Station`), `OriginRoot` = topmost
  (`.MaterialFlow.Station`), `Class` = first user-space class in chain
  → `VOID` when no user-class intermediate exists. Built-in roots
  themselves have `Origin=VOID`, `OriginRoot=self`.

- **Non-modal `infoBox(text, false)` is the safe task-boundary pattern.**
  Modal forms (`infoBox("msg")` / `infoBox("msg", true)`) block the GUI
  and `simtalk_run` — see lifelines §4. The non-modal form returns
  `result:"success"` immediately and is safe to use at task start / end.
  Encoded in `agents/plant-simulation-expert.md` §"任务边界".

- **The `local-simtalk-read-library` `probe_methods.py` is the safe
  pre-image capture path.** It uses `&o.Program` direct attribute
  access (LF-decoded concatenation into the reply), never goes through
  `readlog`. Recommended refactor target for `add_note.py`.

- **Cleanup confirmed across all skills.** The model returned to its
  baseline after every test (e.g. `.UserObjects` back to 4 entries,
  `.Models.Model.Method` back to 70 bytes, EventController attributes
  restored). Subsequent skill tests start from a clean model.

## Recommended follow-ups

1. **Refactor `add_note.py` to use `probe_methods.py` for the read step**
   (or mimic its attribute-access pattern). Until then, do not use
   `add_note.py` for real work — use raw `socket_client.py` with the
   `chr(10)` literal pattern from
   `local-simtalk-write-simtalk/log/2026-08-27_flow-a-replace-and-flow-b-duplicate.md`.
2. **Add `--no-infobox` position note to `class_ops.py` SKILL.md** — this
   burned ~1 minute of round-trip in this session.
3. **Update `SKILL.md` index in the README to point at the 9 fresh
   2026-08-27 logs**, so future operators can pick up the latest patterns
   without grepping for `2026-08-27_*`.
4. **Keep the team memory note
   `simtalk-run-soft-failure-design.md`** in sync with any new
   `simtalk_run` failure modes discovered in future sessions.

## Files added this session

```
skills/local-simtalk-execution/log/2026-08-27_ping-syntax-run-readlog.md
skills/local-simtalk-execution/log/2026-08-27_ping-syntax-run-readlog-2.md
skills/local-simtalk-get-folder-tree/log/2026-08-27_basis-and-models-model-tree.md
skills/local-simtalk-get-class-inheritance/log/2026-08-27_instances-and-root-classes.md
skills/local-simtalk-read-library/log/2026-08-27_probe-methods-1path-and-3path.md
skills/local-simtalk-write-simtalk/log/2026-08-27_flow-a-replace-and-flow-b-duplicate.md
skills/local-simtalk-add-note-to-method/log/2026-08-27_readlogic-readlog-pollutes-backup.md
skills/local-simtalk-modify-object-attribute/log/2026-08-27_eventcontroller-batch-and-boolean.md
skills/local-simtalk-class-management/log/2026-08-27_list-inspect-derive-delete.md
skills/local-simtalk-os-functions/log/2026-08-27_misc-pid-env-path-cwd.md
05-session-archives/2026-08-27-skill-test-summary.md         (this file, renamed)
agents/plant-simulation-expert.md                         (modified — infoBox lifecycle rule)
```

11 file touches, all reversible except the agent modification (which is a
deliberate workflow refinement per the user's mid-session request).