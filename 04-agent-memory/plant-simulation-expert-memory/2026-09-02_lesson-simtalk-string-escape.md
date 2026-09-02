---
type: lesson-learned
date: 2026-09-02
session: 2026-09-02_session-summary_write-astar-graph-method.md
quorum: private
---

# Lesson: SimTalk string literal 内 `"` 必须 `\"` 转义,**不**是 `""` doubling

## 唯一正确路径 / 反例表
| 写法 | 错误信息 / 后果 |
|---|---|
| ✅ Python encode: `replace('"', '\\"')` | 生成的 SimTalk literal `print "\""` 编译通过 |
| ❌ Python encode: `replace('"', '""')` (VB / SQL 习惯) | chunk-3 fail:`Syntax error near line 3 at '"'` — SimTalk 编译器把 `""` 看作**两个相邻字符串字面量**而非转义 |
| ❌ 源里直接含 `"` 不处理 | 服务端拿到 `"` 时直接关闭字符串字面量,后面字符变成裸 token |

## 官方依据 (引用 01-plantsimulation-knowledge/<path>.md 路径 + 段标题)
- `01-plantsimulation-knowledge/01-plant-simulation-help/simtalk/data-types-expressions/primitive-structured/primitive-structured.md` line 844:`var value1 := j.parse("{ \"count\": 123 }")` — SimTalk 字面量内用 `\"` 反斜杠 escape

## 配套纪律
- chunked-write protocol 的 `encode_chunk` 必须先 `replace('\\', '\\\\')` 再 `replace('"', '\\"')`(顺序不能反,否则反斜杠转义反复套娃)
- 任何含 `"` 的 source 行(注释或字面量)都是 trap — 写前 grep `'"'`,encode 后 grep `'\\\\"'` 验证 escape 存在
- 与 lesson `2026-09-02_lesson-method-program-text.md` 互补:method program 写入协议 + 本 lesson 的 escape 细节 = chunked writer 完整闭环

## 反例触发场景(本 session)
- `/tmp/_write_astar_method.py` 第 1 次执行,chunk 3 fail — chunk 3 含 `// 注意: 不能在 if 块里直接 next 跳出外层 for, 用 "if not cond ... end" 反向包裹.`(注释里有嵌入 `"`)
- 错误信息:`Syntax error near line 3 at '"'. (in row :3)`
- 修复:encode_chunk escape 改 `\"`,`m.Program := ""` reset,然后重跑 23/23 全 OK