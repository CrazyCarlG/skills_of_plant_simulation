---
last_updated: 2026-09-01
contributors: [@plant-simulation-expert]
scope: 9 skill 全量测试总结 + 跨 session 提炼的洞察（session 报告统一归 `04-agent-memory/plant-simulation-expert-memory/`，本目录不再保留镜像）
---

# 05-modeling-experience — 建模经验沉淀

本目录整合 **一次性 session 报告 + 跨 session 提炼的洞察**。

## 文件索引

| 文件 | 内容主题 |
|---|---|
| [`skill-test-coverage-matrix.md`](./skill-test-coverage-matrix.md) | **9 skill 全量测试覆盖矩阵**:从 2026-08-27 的 9 个 `local-simtalk-*` skill 回归测试中提炼 |
| [`consolidated-insights.md`](./consolidated-insights.md) | **跨 session 洞察**:从 14 篇 session summary 中提炼的高频主题与核心教训 |
| [`curator-workflow-conventions.md`](./curator-workflow-conventions.md) | **curator workflow 元知识**:3 大用户约定 + P0/P1/P2/P3 分类 + D1-D7 评估 rubric + quarantine 机制(从 `agents/curator-reports/` 提炼) |
| — | **Session 报告**:统一归 [`04-agent-memory/plant-simulation-expert-memory/`](../../04-agent-memory/plant-simulation-expert-memory/)(2026-09-01 起不在本目录保留镜像) |

## 何时读本目录

- **新 agent 冷启动时**:先读 [`consolidated-insights.md`](./consolidated-insights.md) 掌握高频教训,然后查索引按需读具体 session
- **找"踩坑时间线"**:`04-agent-memory/plant-simulation-expert-memory/` 提供了完整的历史决策链
- **复盘特定 Quirk**:跨 session 的同一坑 → 找 consolidated-insights.md 的相关章节

## 何时不需要读本目录

- **找 Plant Simulation 概念** → [`../03-modeling-know-how/01-objects/`](../03-modeling-know-how/01-objects/)
- **找 SimTalk 字面契约** → [`../03-modeling-know-how/02-simtalk/`](../03-modeling-know-how/02-simtalk/)
- **找 skill 调用 workflow** → [`../03-modeling-know-how/03-software/`](../03-modeling-know-how/03-software/)
- **找 SimtalkClaude 桥内部** → [`../02-simtalkclaude-knowhow/`](../02-simtalkclaude-knowhow/)
- **找工厂/仓库案例** → [`../01-factory-know-how/`](../01-factory-know-how/)
- **找通用建模示例** → [`../04-modeling-example/`](../04-modeling-example/)

## Session Summaries

session 报告**统一归** [`04-agent-memory/plant-simulation-expert-memory/`](../../04-agent-memory/plant-simulation-expert-memory/)——cold-start 第一动作 = Read 该目录的 README 索引，不要批量 Read 同目录下 14 篇 session summary。

**索引示例**(去 `04-agent-memory/.../README.md` 查完整版 + cold-start 协议):

- 2026-09-01 — AGV_Claude v2 收尾 / 恢复 / recovery prep
- 2026-08-31 — `.AGV_Claude` library 创建 + replicate source → target
- 2026-08-28 — SyncToolkit foundation + P4_CTU 模型实现解读
- 2026-08-27 — A* / 9 skill 回归 / 多模型学习（teaching / new assembly / Factory51 / ModelAssistants）

## 重构元数据

- 重构日期:2026-09-01
- 重构来源:
  - `03-agent-memory/plant-simulation-expert-memory/` 14 篇 session summary
  - `02-simulation-file-experience/05-session-archives/2026-08-27-skill-test-summary.md`
- 重构策略:
  - **Skill test summary** 重写为清晰的覆盖矩阵(原文档较长)
  - **跨 session 洞察** 新撰写 consolidated-insights.md(从 14 篇提炼)
  - **Session summaries** 已迁移到 `04-agent-memory/plant-simulation-expert-memory/`(2026-09-01 重组)，不在本目录保留镜像
</content>
</invoke>