---
type: lesson-learned
date: 2026-09-02
session: 2026-09-02_session-summary_write-astar-graph-method.md
quorum: private
---

# Lesson: multi-line simtalk_run 代码必须在源字符串中放真 `\n` 换行字符,**不**是字面 `\n` 两字符

## 唯一正确路径 / 反例表
| 写法 | 错误信息 / 后果 |
|---|---|
| ✅ Python f-string:`f'var m: object := str_to_obj(...)\nm.Program := ...\nprint "OK"'` | Python 解析为真换行字符 `0x0A`,经 `json.dumps` 序列化为 JSON 转义 `\n`,服务端 `json.loads` 反序列化为真 newline,SimTalk 编译器按 multi-line 解析 ✅ |
| ❌ 字面 `\n`(两字符 `\` + `n`):`'var m;\nvar x'` | SimTalk 编译器看到字符串里出现 `\` 字符,报 `Syntax error near 'root'`(line 1 — 因为所有内容被吃成 1 行) |
| ❌ `;` 多语句单行:`'var m: object; m := ...; print ...'` | SimTalk 不支持 `;` 多语句,报错 `near '<first var>'` |

## 官方依据 (引用 01-plantsimulation-knowledge/<path>.md 路径 + 段标题)
- 无官方文档(协议由 `skills/local-simtalk-execution/scripts/simtalk_send.py` line 145-149 / 182-186 的 `"simtalk_code": args.code` JSON 序列化路径隐式确定):JSON 序列化会把真 newline 编码为 `\n` 两字符,但服务端反序列化还原为真 newline。**这不是 SimTalk 规则,而是 JSON-over-TCP 协议约束**。

## 配套纪律
- **任何** simtalk_run multi-statement 调用必须用 `subprocess.run(...)` 经 Python 直接传字符串(保留 `\n` 真字符),**不要**用 shell `$(cat file)`(bash 处理换行可能 strip)
- chunked-write 协议(`/tmp/_write_astar_method.py` 的 `simtalk = f'... \n ...'`)正是依赖这一行 — 每 chunk 内部 multi-line `var m; var cur; m.Program := ...; print ...` 必须真换行才能被 SimTalk 编译器逐行解析
- 与 lesson `2026-09-02_lesson-method-program-text.md` 配套:chr(10) 是 source 内部的 newline,本 lesson 是**承载 source 的 simtalk_run 代码本身的 newline**

## 反例触发场景(本 session)
- Step 2:`simtalk_send.py run --code "..."` 单行 probe(`;` 串多语句)→ `Syntax error near 'root'`
- Step 3:`simtalk_send.py run` multi-line 字面 `\n` → `Syntax error near 'length'`
- Step 4:切到 Python `subprocess.run` + 真 newline → RC=0 success