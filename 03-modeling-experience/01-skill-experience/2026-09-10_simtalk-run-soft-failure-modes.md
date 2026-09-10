---
last_updated: 2026-09-10
dimension: 01-skill-experience
source_sessions:
  - 04-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-wrap.md
  - 04-agent-memory/plant-simulation-expert-memory/2026-09-02_session-summary_port-50008-model-structure.md
skills_touched: [local-simtalk-execution]
models_touched: [AGV_Claude, Factory51, .Models]
---

# `simtalk_run` 静默失败的 4 种模式 — 全部 result:success 也要 double-check

## 症状
- `simtalk_run` 返回值与 inner 实际行为不一致,常见 4 种:
  1. **`result: "failed"` + `log: " hasError: ..."`**(返回极快,<1s)— 真正编译错
  2. **`result: "success"` + `log: "execute success"`** — 但 inner print 不在 immediate response,需 `readlog` 单独拉
  3. **`readlog` 累积日志停在 `execute sim-code: '...'` 头就截断** — print buffer 没 flush 或被更晚的 simtalk_run 覆盖
  4. **inner `executeSilent(<expr>)` 内的 print 不直接转发** — 必须用 `getExecuteSilentError` 捕获 error,print 看不到

## 根因
- v15+ readlog 退化(参见 `2026-09-10_v15-readlog-regression-workarounds.md`)。
- `result: success` 只表示 TCP envelope 收到回应,不代表 inner SimTalk 逻辑正确。
- `executeSilent` 是嵌套 execute 路径,有自己的 error channel。

## Workaround / 结论
- **永远 double-check log 字段**,不只看 result。
- 4 种模式处置:
  1. failed → 读 `log` 里的 `hasError`,定位 syntax error
  2. success + readlog 缺 → 主动 `readlog` + 解析 print marker
  3. readlog 截断 → 用 `system("echo")` shell-out 写文件,绕过 print 通道
  4. executeSilent → `var err := getExecuteSilentError; print err`
- 团队记忆:`memory/team/simtalk-run-soft-failure-design.md`(双重判据: result + log)

## see also
- `04-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-wrap.md §02-bridge-tool`
- 团队记忆:`memory/team/simtalk-run-soft-failure-design.md`

## 反思
"result: success" 是 TCP 协议层面的成功,不等于 SimTalk 语义层面的成功;expert 每次写 readback 都必须按这 4 种模式交叉验证。
