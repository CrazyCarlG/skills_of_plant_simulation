---
last_updated: 2026-09-10
dimension: 01-skill-experience
source_sessions:
  - 04-agent-memory/plant-simulation-expert-memory/2026-09-02_session-summary_write-model-structure-comments.md
  - 04-agent-memory/plant-simulation-expert-memory/2026-09-02_session-summary_write-astar-graph-method.md
  - 04-agent-memory/student-memory/2026-09-07-Python_GA_Demo-jobsshop-ga-integration.md
skills_touched: [local-simtalk-execution]
models_touched: [AGV_Claude, Python_GA_Demo, Factory51]
---

# `length()` 不是 SimTalk 函数 — 必须用 `strLen(s)` / `x.dim`

## 症状
- SimTalk 源码里写 `length("abc")` 或 `print length(str)` → 编译报 `Syntax error near line N at 'length'` 或 `Unknown identifier`。
- 同样地 `s.length` / `x.length()` 在部分上下文被拒绝(`A 'string' cannot accept the method 'Length'`)。
- 跨 session 复现 ≥3 次,跨 3 个不同模型(.AGV_Claude / .Python_GA_Demo / .Models.Model)。

## 根因
- SimTalk 没有 Python/Java 风格 `len()` / `length()` 函数。
- 合法替代:
  - **string**:`strLen(s: string) → integer`(在 `string-functions` predefined functions)
  - **list / DataList / DataTable**:`x.dim` 属性(list 长度)
  - **string 部分访问**:`s.length` 是 false friend name,在本 v2606 实测报"cannot accept the method 'Length'"

## Workaround / 结论
- 代码中:用 `strLen(myStr)` 拿 string 长度,`x.dim` 拿 list/dict 长度。
- 不要写 `length(...)` 或 `len(...)`。
- simtalk_run probe 时遇到 `Syntax error near 'length'` → 立刻知道是踩这条 Quirk。

## see also
- KB 文档:`01-plantsimulation-knowledge/01-plant-simulation-help/simtalk/predefined-functions-i-os-math-string-datetime/string-functions/string-functions.md`
- 关联 Quirk 候选(student 提):`#31 length() is not a SimTalk function`(应进 canonical)
- `04-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-recovery.md Key findings`(实测 `length()` 不工作)

## 反思
Python 习惯写 `length(x)` 进 SimTalk 是高频踩坑,SKILL.md / `language-quirks-reference.md` 应该把 `length()` 显式列为反例 + 给 `strLen/x.dim` 替代。
