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

## 文件正文模板（≤300 行，过程流水账）

**定位**:expert session summary 是**操作流水账**——记「做了什么 / 怎么做 / 返回了什么 / 卡在哪」。**不做维度分类,不做经验抽象**(抽象是 curator / synthesizer 的活)。

```markdown
# <主题一句话>
**Date:** YYYY-MM-DD  **Agent:** plant-simulation-expert
**Duration:** <粗估，含卡死/迭代/批量写入分钟数>
**Skills called:** <skill1>(<子命令>), <skill2>, ...
**Target:** <Frame / 对象路径，如 .Models.Factory51.Station_1>
**Result:** success / partial / fail

## 任务与背景
- <用户原始请求一句话 + 本 session 的目标边界（做什么 / 不做什么）>

## 操作步骤（时序）
1. <skill 名(子命令)> → 目标 `<对象路径>` → 结果 ✅/⚠️/❌ 一句话
2. ...

## 操作日志（关键 I/O）
- <关键调用的实际参数 + 返回的 `result` 与 `log` 字段原文（截断到关键行）>

## 遇到的问题与处置
- <现象 → 判断 → 处置 → 是否解决>；涉及已知 Quirk 标 `Quirk #N`

## Cross-references
- per-skill logs: `skills/<x>/log/YYYY-MM-DD_*.md`
- 已沉淀 entry: `03-modeling-experience/<子目录>/<file>.md`
- 团队记忆: `memory/team/<file>.md`
- KB 文档: `02-domain-know-how/<dim>/<file>.md` 或 `01-plantsimulation-knowledge/<path>.md`

## Open questions / next steps
- <未解 / 待 curator 沉淀 / 待 verification / @skills-optimizer 评审项>
```

**段位纪律**:
- **`## 操作步骤`**:按时序编号,一步一行——每行必须含 **skill + 目标路径 + 结果**。curator 复盘的主输入,**不合并步骤**。
- **`## 操作日志`**:摘录关键调用的 `result` / `log` 字段原文(`log` 是真信号源);不粘贴完整 stdout,长输出引用 `data/<query>.json`。
- **`## 遇到的问题与处置`**:含选错 skill / silent fail / 桥卡死 / Quirk 漂移;**无问题**则写"本 session 无异常"。
- 段未触发 → 写"本 session 无"+ 一句话原因(**不省略小标题**)。

---

## README 第 4 列取值（表头历史遗留为 `Dimensions touched`）

**维度分类已废弃**——expert 不再给 session 打 `01-domain-concepts` / `02-bridge-tool` 之类的维度标签（那套 taxonomy 源自已删除的 `02-simulation-file-experience/` 目录树，commit `e9affee`）。

- 第 4 列**填本次涉及的对象 / Frame 路径**,逗号分隔,例:`.Models.Factory51.Station_1, .AGV_Claude.AGV_dispatch`
- 路径过多 → 填最能定位的 2–3 个 + `等 N 个`。
- ❌ **不**为了迁就旧表头去编维度值。
- ❌ **不**引用 `02-simulation-file-experience/` / `05-session-archives`——目录已删除,仅历史 session summary 里残留。
- 表头重命名需 user 批准,本目录 README 仍保留 `Dimensions touched` 字样（historical column header）。

---

## Cross-references 协议

expert 在 `## Cross-references` 段必须给两类链接：

1. **per-skill logs**：本次 session 涉及的 `skills/<x>/log/*.md`。
2. **已沉淀到 `03-modeling-experience/` 的 entry**：curator 已经处理过的 finding 引用其目标文件路径。
3. **团队记忆**（如有）：`memory/team/<file>.md`。
4. **KB 文档**（若有）：`02-domain-know-how/<dim>/<file>.md`（合成主题文档）或 `01-plantsimulation-knowledge/<path>.md`（官方 API）。

> **未沉淀的 finding 写在 `## 遇到的问题与处置` 正文段**，不在 cross-references 里"画饼"——只在 `## Open questions` 标 "建议下次 curator 沉淀到 `03-modeling-experience/<子目录>/<slug>.md`"。

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