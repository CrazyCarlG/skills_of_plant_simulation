# Session Summary — learn teaching model(3rd model swap of the day)
**Date:** 2026-08-27  **Agent:** plant-simulation-expert
**Duration:** ~5 min(single-turn orientation)
**Skills called:** local-simtalk-execution, local-simtalk-get-folder-tree, local-simtalk-read-library, local-simtalk-get-class-inheritance

## 04-model-case-studies
- **当日第 3 次换模型**:09:37 warehouse(Factory51)→ 10:20 assembly line(Assembly1/2)→ 12:16 **teaching model**
- 模型分 3 层:
  - **Layer A — TCP server runtime** (`.SimtalkClaude.*`) — agent 自己的桥;real code 在 `.SimtalkClaude.src.SimtalkAction.*`(6 non-empty methods);`main.*` + `connection.*` 是 visual shell templates
  - **Layer B — Demo / teaching domain** (`.Models.internal.*`) — `Admin` Frame (17 methods,学生-打分/考试-No analyzer) + `autoexec`(3072B,模型最大方法) + `Localization`
  - **Layer C — Material-flow templates** (`.Models.SourceTrigger.*`) — 5 Source variants + 3 sample Parts
- **0 user-derived classes** — 每个 Frame/Dialog/HtmlReport/Comment 直接继承 Plant Simulation built-ins。**后续若 user 问"本模型定义了什么类",答:"none derived"**

## 01-domain-concepts
- 35 个空 Methods 多是 template placeholders(`.SimtalkClaude.connection.*`、`.SimtalkClaude.main.SimtalkAction.*`、`.Models.internal.Admin.*`、`.Models.SourceTrigger.*` 等的 lifecycle shells)
- Real code 集中在 28 个方法:`.Models.internal.Admin.*`(~10KB)+ `.Models.internal.autoexec` + `.Models.internal.Localization.*` + `.SimtalkClaude.src.SimtalkAction.*`

## 02-bridge-tool
- **疑似 bug(out of scope)**:`.SimtalkClaude.src.SimtalkAction.simtalkcode` body 22B,内容是 `var obj:=.createfodler` — `createfodler` 不是 PS function(应是 `createFolder`)。标记待用户确认是否修

## 03-workflow-playbook
- Model 每 1-2 小时就 swap,新 session **必须**先 `bfs_full.py` depth=1 of `.` 确认加载的是哪个模型(廉价且权威)

## Cross-references
- per-skill logs: `skills/local-simtalk-get-folder-tree/log/2026-08-27_orientation-summary-from-fresh-data-2.md`(prior `-1` variant preserved)
- 02-simulation-file-experience entries: 无新增(本次只 orientation,未触发新 domain 沉淀)

## Open questions / next steps
- 若 user 想 drill teaching model:`.Models.internal.autoexec`(3072B, entry point)→ `.Models.internal.Admin.dispatcher`(1323B,主 flow controller)
- 若想扩展 agent runtime:从 `.SimtalkClaude.src.SimtalkAction.simtalk_execute`(281B,TCP 桥 → PS 代码执行 handler)入手
- `simtalkcode` body `createfodler` typo — 等 user 确认
