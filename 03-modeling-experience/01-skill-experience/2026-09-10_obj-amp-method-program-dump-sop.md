---
last_updated: 2026-09-10
dimension: 01-skill-experience
source_sessions:
  - 04-agent-memory/student-memory/2026-09-02-AllModels-station-onpull-meta-analysis.md
  - 04-agent-memory/student-memory/2026-09-02-MarkerCrossing-crossing-semaphore-deepdive.md
  - 04-agent-memory/student-memory/2026-09-02-SevenAxisRobot-onpull-dump-part1.md
skills_touched: [local-simtalk-execution]
models_touched: [.Models.RobotComau, .Models.XZYStacker, .Models.PortalCrane, .Models.LinearPortal, .Models.SevenAxisRobot, .Models.MarkerCrossing, .Models.AGVWithRobot]
---

# `obj.&Method.Program` 完全可移植 SOP — 跨 8+ 个 Method dump 验证

## 症状
- simtalk_run 反射层 dump Method 源码的标准 SOP 验证。
- 跨 5 个 Frame 模型 + 8+ 个不同 Station/Init/DestCtrl/EntranceCtrl/ExitCtrl/RecalcLayout/Reset Method 全部成功。
- 是 student / expert 在 PS 2.0 反射层最稳定的 dump 路径。

## 根因
- SimTalk 中 `&Method.Program` 是 method ref + 源码属性的标准访问语法。
- simtalk_run 在 v2606 实测对该语法完整支持,跨 Method 类型(Frame-level + 嵌套 Frame-level)、跨带参(`param newValue:real`)与无参 Method 都可用。

## Workaround / 结论
- **完整 SOP**:
  ```simtalk
  var m: object
  m := str_to_obj(".<path>.<MethodName>")
  print m.~  -- 确认 to_str 返回正确路径
  print obj.&MethodName.Program  -- dump 源码
  ```
- **批量 OnPull 扫描模式**:先 `s.PullCtrl` 检测 callback 存在,再 `s.&OnPull.Program` dump — 适合 meta-analysis。
- **限制**(已知):
  - Method 是 `Method` ICN(无 Nw 前缀)— 与 Frame/Source/Station/NwArc 等 Nw 系列类不同
  - 嵌套 Frame 内部 Method 也可直接用相同 SOP,无需特殊路径
  - 不适用 encrypted Method(返回 VOID 或 error)
- **SOP 适用场景**:
  - 学习他人模型(读 7-Frame 集全部 Station callback)
  - meta-analysis(5 个 OnPull 横向对比)
  - Reverse-engineer(从源码推 Pattern / boilerplate)

## see also
- `04-agent-memory/student-memory/2026-09-02-AllModels-station-onpull-meta-analysis.md §02-simtalkclaude-knowhow`
- `04-agent-memory/student-memory/2026-09-02-MarkerCrossing-crossing-semaphore-deepdive.md §02-simtalkclaude-knowhow`
- `@skills-optimizer 评审`:`local-simtalk-read-library/SKILL.md` Limitations 修订 + `language-quirks-reference.md` 新增 dump SOP

## 反思
`obj.&Method.Program` 是 PS 反射层最稳定的 SOP,但 SKILL.md 目前未明示;optimizer 应把它正式写进 read-library SKILL.md 的 "When to use" 表。
