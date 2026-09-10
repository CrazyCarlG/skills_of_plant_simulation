---
last_updated: 2026-09-10
dimension: 01-skill-experience
source_sessions:
  - 04-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-wrap.md
  - 04-agent-memory/plant-simulation-expert-memory/2026-09-02_session-summary_port-50008-model-structure.md
  - 04-agent-memory/plant-simulation-expert-memory/2026-09-02_session-summary_write-astar-graph-method.md
  - 04-agent-memory/plant-simulation-expert-memory/2026-08-31_session-summary_create-agv-claude-library.md
  - 04-agent-memory/student-memory/2026-09-07-Python_GA_Demo-jobsshop-ga-integration.md
skills_touched: [local-simtalk-execution, local-simtalk-write-simtalk]
models_touched: [AGV_Claude, Factory51, Python_GA_Demo]
---

# v15+ readlog 退化 — print / readlog 多处不传播,需三重 readback proxy

## 症状
- `simtalk_run` 内部 `print "X"` → 返回 `result: "success"` + `log: "execute success"`,但 readlog 不显示该 print。
- `readlog` 累积日志可能停在 `execute sim-code: '...'` 头就截断,print buffer 不 flush。
- `OpenConsoleLogFile` 日志**只捕获引擎事件**(`execute sim-code: ...`) + 自定义 `system("echo")` 标记,**不**捕获 `print()` 输出。
- 多个 `system()` 调用在同一 `simtalk_run` 内静默失败(部分写文件、部分丢失,单独都"exit 0")。
- 跨 ≥5 个 session 复现,跨 ≥3 个 skill(涵盖 write / execution / get-folder-tree)。

## 根因
- Plant Simulation v15+ 重新设计了 readlog buffer,print 输出不再直接转发到 TCP readlog envelope。
- `OpenConsoleLogFile` 是引擎级事件流,与 print() 通道分离。
- `system()` 在 PS 2606 sandbox 里有并发限制,多次调用部分丢失。

## Workaround / 结论
- **三重 readback proxy**(推荐):
  1. `simtalk_syntax --target-path m` → `has no Error` = 程序可解析
  2. `m.execute()` 无参 → soft-fail log 显示 `"0 passed, 7 expected"` = param count 识别
  3. functional test `m.execute(args)` → `execute success` = method 真的被加载
- **print 不可见时**:`system("cmd.exe /C echo " + line + " > file.txt")` 拼成单次调用(单次 OK,多次 fail — Quirk #32)
- **`getExecuteSilentError`** 是 executeSilent 的唯一 fresh-compile error 通路(配合 executeSilent)
- **OpenConsoleLogFile 不替代 readlog**:用前者收集 engine 事件,后者(若可用)做 print 输出,实测两个都退化
- **写 dashboard / report**:走 `writeToFile` 写到 `/tmp/dashboard_<timestamp>.csv`,不依赖 print

## see also
- `04-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-wrap.md §02-bridge-tool`(silent failure 4 种模式)
- `04-agent-memory/plant-simulation-expert-memory/2026-09-02_session-summary_write-astar-graph-method.md §Lessons extracted Lesson 3`
- `04-agent-memory/student-memory/2026-09-07-Python_GA_Demo-jobsshop-ga-integration.md §03-software`(Quirk #32/#33 候选)
- 团队记忆:`memory/team/simtalk-run-soft-failure-design.md`(双重判据)

## 反思
v15+ 的 readlog 退化是 plant-simulation-expert / student 都高频踩的隐性问题,任何"想用 print 看结果"的工作流都会断;专家 / 工具链必须把 readback 全部切到 syntax / executeSilent / system() shell-out 三条替代路径。
