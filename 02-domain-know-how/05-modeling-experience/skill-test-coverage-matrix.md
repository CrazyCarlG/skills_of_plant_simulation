---
last_updated: 2026-09-01
contributors: [@plant-simulation-expert]
scope: 9 个 `local-simtalk-*` skill 的全量测试覆盖矩阵(2026-08-27)+ 经验教训与推荐后续行动
---

# 9 Skill 全量测试总结(2026-08-27)

## 一、目标与范围

**目标**:Exercise every skill in `skills/local-simtalk-*` at least twice with full usage logs。

**操作者**:plant-simulation-expert(OpenClaude subagent)+ user-driven session。

## 二、9 个 skill 覆盖矩阵

| # | Skill | Sub-areas touched | Verdict |
|---|---|---|---|
| 1 | `local-simtalk-execution` | ping, syntax, run, readlog, infoBox lifecycle | ✅ PASS |
| 2 | `local-simtalk-get-folder-tree` | `.Basis` tree + `.Models.Model` tree(BFS) | ✅ PASS |
| 3 | `local-simtalk-get-class-inheritance` | `obj.Class`, `obj.Origin`, `obj.OriginRoot`, `rootClasses` | ✅ PASS |
| 4 | `local-simtalk-read-library` | `probe_methods.py` single + multi-path | ✅ PASS |
| 5 | `local-simtalk-write-simtalk` | Flow A replace, Flow B `.&Method.duplicate()` | ✅ PASS |
| 6 | `local-simtalk-add-note-to-method` | `add_note.py` bug exposure + raw-socket workaround | ⚠️ FAIL(script)/ PASS(workaround) |
| 7 | `local-simtalk-modify-object-attribute` | read-only, boolean + restore, batch real+integer + restore | ✅ PASS |
| 8 | `local-simtalk-class-management` | list, inspect(user + built-in), derive, delete | ✅ PASS |
| 9 | `local-simtalk-os-functions` | `getApplicationProcessID`, `availableMemory`, `getEnv`, `getCurrentDirectory`, `strLen`, `strCopy` | ✅ PASS |

**9 / 9 skills exercised**。1 个 FAIL(script)有 workaround,其它 8 个 PASS。

## 三、核心经验教训

### 3.1 Quirk #7 软失败契约已验证

Every `simtalk_run` reply with `result:"success"` + `log:"code execute failed..."` is a runtime exception, not a server bug. Per the team memory note `simtalk-run-soft-failure-design.md`, this is by design — the result field is "did the code compile + enter execution", the log field carries the error.

### 3.2 Quirk #15(`.&Method.duplicate()` required for new Methods)已验证

Three `create()` variants all fail; `.&Method.duplicate(<frame>, <name>)` with `&` on the class name + object-ref frame(NOT string)is the only reliable Method-creation path。

### 3.3 `add_note.py` has a real, exploitable bug

The `readlogic` reads the polluted server Console log buffer instead of trusting the `simtalk_run` reply directly. The on-disk backup is corrupted as a consequence; `--restore` is useless。

**Workaround**:raw `socket_client.py` with `chr(10)`-joined SimTalk string literals and the existing `o.program := src;` write pattern. The skill's SKILL.md is honest about the risk but the implementation chose the degraded read path anyway — flagged for refactor。

### 3.4 SimTalk 2.0 strings: `strLen(s)`, NOT `s.length` / `s.numCharacters`

Caught in `local-simtalk-os-functions` Test 2; correct path is the top-level `strLen(s)` function(per `predefined-functions-i-os-math-string-datetime/string-functions/string-functions.md`)。

String slicing uses `strCopy(s, pos, n)`, not `s.copy(...)`。

### 3.5 `argparse subparsers` and `--no-infobox` position

For `class_ops.py`, `--no-infobox` MUST come **before** the subcommand(`class_ops.py --no-infobox list .UserObjects`). Placing it after the subcommand errors with `unrecognized arguments: --no-infobox`. This is the opposite of folder-tree / read-library / add-note scripts。

### 3.6 `Origin` / `OriginRoot` / `Class` triple semantics verified

For a user class derived directly from a built-in(`MyStation ← MaterialFlow.Station`), `Origin` = immediate parent(`.MaterialFlow.Station`), `OriginRoot` = topmost(`.MaterialFlow.Station`), `Class` = first user-space class in chain → `VOID` when no user-class intermediate exists. Built-in roots themselves have `Origin=VOID`, `OriginRoot=self`。

### 3.7 Non-modal `infoBox(text, false)` is the safe task-boundary pattern

Modal forms(`infoBox("msg")` / `infoBox("msg", true)`)block the GUI and `simtalk_run` — see lifelines §4. The non-modal form returns `result:"success"` immediately and is safe to use at task start / end。

### 3.8 The `local-simtalk-read-library` `probe_methods.py` is the safe pre-image capture path

It uses `&o.Program` direct attribute access(LF-decoded concatenation into the reply),never goes through `readlog`. Recommended refactor target for `add_note.py`。

### 3.9 Cleanup confirmed across all skills

The model returned to its baseline after every test(e.g. `.UserObjects` back to 4 entries, `.Models.Model.Method` back to 70 bytes, EventController attributes restored). Subsequent skill tests start from a clean model。

## 四、推荐后续行动

1. **Refactor `add_note.py` to use `probe_methods.py` for the read step**(or mimic its attribute-access pattern). Until then, do not use `add_note.py` for real work — use raw `socket_client.py` with the `chr(10)` literal pattern。
2. **Add `--no-infobox` position note to `class_ops.py` SKILL.md** — this burned ~1 minute of round-trip in this session。
3. **Update `SKILL.md` index in the README to point at the 9 fresh 2026-08-27 logs**, so future operators can pick up the latest patterns without grepping for `2026-08-27_*`。
4. **Keep the team memory note `simtalk-run-soft-failure-design.md`** in sync with any new `simtalk_run` failure modes discovered in future sessions。

## 五、文件 touched by this session

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
```

## 经验 Log

> 本节是 **append-only** 时间线——新发现直接追加在末尾。

<!-- 暂无 entry——首个 entry 由下次踩坑时 append -->
</content>
</invoke>