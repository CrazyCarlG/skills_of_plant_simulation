---
last_updated: 2026-09-01
audience: 跨 session 经验沉淀的写作者 + reader
---

# Contributing to `05-modeling-experience/`

跨 session 经验沉淀——skill 覆盖矩阵、合并洞察、session 归档。**本目录是知识库最末梢**——任何到这里的内容都已经过 curator 评审。

> 跨主题公共纪律见 [`../CONTRIBUTING.md`](../CONTRIBUTING.md)

## 当前内容

| 文件 | 主题 |
|---|---|
| `skill-test-coverage-matrix.md` | 9 skill 全量测试覆盖矩阵 |
| `consolidated-insights.md` | 跨 session 洞察（5 大主题 + 8 个硬规则） |
| — | session 报告统一归 `04-agent-memory/plant-simulation-expert-memory/`（本目录不放） |

## 何时写到哪个文件

| finding 类型 | 落点 |
|---|---|
| skill 验证用例新增 / 通过 / 失败 | 更新 `skill-test-coverage-matrix.md` 主体 + bump `last_updated` |
| 跨多个 session 的合并洞察 / 硬规则 | append 到 `consolidated-insights.md ## 经验 Log` |
| 单 session 的可复用结论 | 落到 `04-agent-memory/plant-simulation-expert-memory/<session-slug>.md`（expert 端） |

## 不做的事

- ❌ 单 session 单次发现进 `consolidated-insights.md`（应去 `03-modeling-experience/01-skill-experience/`）。
- ❌ 把 session 报告放到本目录（应去 `04-agent-memory/plant-simulation-expert-memory/`）。
- ❌ 评估 skill 描述准确性（那是 `skills-optimizer` 的活）。
- ❌ 调任何 skill 脚本（离线策展）。