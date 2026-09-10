---
last_updated: 2026-09-10
dimension: 01-skill-experience
source_sessions:
  - 04-agent-memory/plant-simulation-expert-memory/2026-09-02_session-summary_write-astar-graph-method.md
skills_touched: [local-simtalk-execution]
models_touched: [.Models.Model]
---

# multi-line `simtalk_run` — Python 字面必须真换行,不是 `\n` 两字符

## 症状
- Python f-string 里写 `"var x: object\nx := str_to_obj(...)"`,期望传过去是真 newline。
- SimTalk 服务端报 `Syntax error near line 1 at 'root'`(单行多个 `var ...` 用 `;` 串),或 `Syntax error near line 3 at 'length'`(单行多语句)。
- 实测 `"\n"` 是两字符(`\` + `n`),不是换行符。

## 根因
- `simtalk_run` 接收的 `simtalk_code` 字段是 raw text,服务端按字面 parse。
- Python 里 `"...\n..."` 经 JSON 序列化后服务端拿到的是真换行字符;但若用 r-string 或误写 `\\n`,服务端拿到的是字面 `\n` 两字符。
- SimTalk 不接受 `;` 多语句单行(`var a; a := ...`),必须真 newline 分隔。

## Workaround / 结论
- 写多语句 SimTalk 必须用真换行字符 `"\n"`(不是字面 `\\n`)。
- probe 时报错 `Syntax error near 'X' at line 1`(X 是第二个 var 名)→ 检查是否单行多语句。
- multi-line probe SOP:用 Python list `"\n".join([line1, line2, line3])` 拼好再 send。

## see also
- `04-agent-memory/plant-simulation-expert-memory/2026-09-02_session-summary_write-astar-graph-method.md §Lessons extracted Lesson 2`
- `04-agent-memory/plant-simulation-expert-memory/2026-09-02_session-summary_write-model-structure-comments.md §遇到的问题 1`(同类陷阱)

## 反思
"newline vs literal backslash-n" 是 JSON wire protocol 层的隐性陷阱,SKILL.md 应明示 `simtalk_code` 字段是 raw text + 必须真换行。
