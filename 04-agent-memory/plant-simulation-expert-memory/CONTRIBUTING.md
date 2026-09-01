---
last_updated: 2026-09-01
audience: plant-simulation-expert
---

# Contributing to `plant-simulation-expert-memory/`

本目录是 `plant-simulation-expert` 自己的 **session log 仓库**——每次 expert session 落一份新文件，**不 append** 到已有 session summary 正文（末尾 `Operator self-review` 段除外）。

> 索引与 cold-start 协议见 [README](./README.md)。
> 跨 agent 公共纪律见 [`../CONTRIBUTING.md`](../CONTRIBUTING.md)。

---

## 🔴 铁律

1. **每个 expert session = 一份新文件**——文件名 `YYYY-MM-DD_session-summary_<topic>.md`。
2. **每文件 ≤300 行**——超限立即拆 `<topic>-part1.md` / `<topic>-part2.md`。
3. **session 结束必填 README 索引行**（newest at top）+ bump frontmatter `last_updated`。
4. **不调 curator 的写文件流程**——那是 curator 的活；expert 只**产出** session summary。
5. **不 Edit 其他 agent 的 memory**（包括 `curator-memory/` / `student-memory/`）。

---

## 文件命名

```
YYYY-MM-DD_session-summary_<topic>.md
```

### 已存在的例外（保留原名，不强制改名）

- `2026-08-27_modelassistants-study.md`（缺中缀）
- `2026-08-27_session-summary.md`（缺 topic）

> 历史命名例外不破坏 cross-ref；**新文件必须遵循标准格式**。

---

## 文件正文模板（≤300 行）

```markdown
# <主题一句话>
**Date:** YYYY-MM-DD  **Agent:** plant-simulation-expert
**Duration:** <粗估，含卡死/迭代/批量写入分钟数>
**Skills called:** <skill1>(<子命令>), <skill2>, ...

## 01-domain-concepts
- <一句话 finding + 证据（路径 / Quirk #N / error 文本）>

## 02-bridge-tool
- ...

## 03-workflow-playbook
- ...

## 04-model-case-studies
- ...

## Cross-references
- per-skill logs: `skills/<x>/log/YYYY-MM-DD_*.md`
- 03-modeling-experience entries: `03-modeling-experience/<子目录>/<file>.md`
- 团队记忆: `memory/team/<file>.md`

## Open questions / next steps
- <未解 / 待 curator 沉淀 / 待 verification>
```

---

## `Dimensions touched` 字段（README 索引列取值）

README 索引表里 `Dimensions touched` 列允许以下值（逗号分隔、按出现顺序）：

- `01-domain-concepts` — 领域概念（SimTalk / 模型对象 / 类继承）
- `02-bridge-tool` — SimTalkClaude 桥接 / TCP 协议 / 命令行工具
- `03-workflow-playbook` — 工作流套路 / 调试方法 / verification 设计
- `04-model-case-studies` — 具体模型（Factory51 / P4_CTU / AGV_Claude / SyncToolkit 等）

> **历史值** `02-simulation-file-experience/` 已被 `03-modeling-experience/` 取代；旧 session summary 里仍可能引用老路径，**新文件不要复用**。

---

## Cross-references 协议

expert 在 `## Cross-references` 段必须给两类链接：

1. **per-skill logs**：本次 session 涉及的 `skills/<x>/log/*.md`。
2. **已沉淀到 `03-modeling-experience/` 的 entry**：curator 已经处理过的 finding 引用其目标文件路径。
3. **团队记忆**（如有）：`memory/team/<file>.md`。

> **未沉淀的 finding 写在 `## 0X-<dim>` 正文段**，不在 cross-references 里"画饼"——只在 `## Open questions` 标 "建议下次 curator 沉淀到 `03-modeling-experience/<子目录>/<slug>.md`"。

---

## 与 curator 的协作边界

| 边界 | expert 责任 | curator 责任 |
|---|---|---|
| 谁读谁 | 写 `plant-simulation-expert-memory/` | 读 + 沉淀到 `03-modeling-experience/` |
| 谁改谁 | 改 expert 自己的 session summary + README | 改 curator 自己的 session log + `03-modeling-experience/` 新文件 |
| Quirk 编号漂移 | 在 session summary 里 cite Quirk #N | quarantine → 转 `skills-optimizer` |

**expert 不做的事**：
- ❌ 直接 `Edit skills/<x>/references/quirks.md`（那是 optimizer 的活）
- ❌ 直接 `Edit 03-modeling-experience/`（那是 curator 的活）
- ❌ 替 curator 写沉淀文件

---

## 不做的事

- ❌ append 到已有 session summary 正文（除末尾 `Operator self-review`）。
- ❌ Edit README 索引表以外的列 / 不 bump `last_updated`。
- ❌ 写 `usage_log/` 以外的 log（per-skill log 写 `skills/<x>/log/`）。
- ❌ 在 session summary 里"假装已沉淀"——只写**已通过 curator 沉淀**的引用。
- ❌ 单文件超 300 行硬塞。