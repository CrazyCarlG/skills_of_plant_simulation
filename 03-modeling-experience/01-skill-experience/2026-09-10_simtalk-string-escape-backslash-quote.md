---
last_updated: 2026-09-10
dimension: 01-skill-experience
source_sessions:
  - 04-agent-memory/plant-simulation-expert-memory/2026-09-02_session-summary_write-astar-graph-method.md
skills_touched: [local-simtalk-execution, local-simtalk-write-simtalk]
models_touched: [.Models.Model]
---

# SimTalk string literal escape 必须是 `\"`,不是 `""` doubling

## 症状
- Python 写 chunked writer,用 `replace('"', '""')`(Visual Basic / Pascal 风格 escape)对 chunk 内 `"` 转义。
- 写到第 3 chunk 时 `simtalk_run` 报 `Syntax error near line 3 at '"'. (in row :3)`。
- 全 chunk 全坏,因为前面 1-2 chunk 已用错 escape 写入。

## 根因
- SimTalk string literal escape 是 `\"`(反斜杠 + 双引号),**不是** Visual Basic / Pascal 的 `""` doubling。
- Python f-string / JSON 序列化里 `"` 默认不会自动 escape;需要手动 `replace('"', '\\"')`。

## Workaround / 结论
- encode_chunk 必须用:`replace('\\', '\\\\').replace('"', '\\"')`(先 escape 反斜杠,再 escape 双引号)。
- 多 chunk writer 失败后**必须 reset method program**:`var m; m := str_to_obj(path); m.Program := ""` 清空已写错 chunk,再从头重跑。
- 不要假设 SimTalk 兼容任何已知的 string escape 约定;查 `primitive-structured.md` line 844 实测。

## see also
- KB 文档:`01-plantsimulation-knowledge/01-plant-simulation-help/simtalk/data-types-expressions/primitive-structured/primitive-structured.md` line 844
- `04-agent-memory/plant-simulation-expert-memory/2026-09-02_session-summary_write-astar-graph-method.md §Lessons extracted Lesson 1`
- `@skills-optimizer 评审`:`local-simtalk-write-simtalk/references/quirks.md` 加 1 条 `simtalk-string-escape` per-skill Quirk

## 反思
跨语言 string escape 规则差异是隐性陷阱,SKILL.md 的 "When to use" 表应明确 SimTalk 用 `\"`,避免 expert 把 Python/VB 习惯带入。
