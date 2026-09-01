---
last_updated: 2026-09-01
audience: plant-simulation-student（未来 agent）
---

# Contributing to `student-memory/`

本目录是 `plant-simulation-student` 的 **session log 仓库**——student 负责"只读扫描 + 5 维镜像分析"用户仿真模型，每个 session 一份新文件。

> 索引与定位见 [README](./README.md)。
> 跨 agent 公共纪律见 [`../CONTRIBUTING.md`](../CONTRIBUTING.md)。

---

## 🔴 铁律

1. **每个 student session = 一份新文件**——文件名 `<date>-<model>-<scenario>.md`（区别于 expert 的 `YYYY-MM-DD_session-summary_<topic>.md`）。
2. **每文件 ≤300 行**——超限拆 part1/part2。
3. **session 结束必填 README 索引行**（newest at top）+ bump `last_updated`。
4. **不写 SimTalk / 不改模型**——student 只读扫描；写模型是 `plant-simulation-expert` 的活。
5. **不 Edit 其他 agent 的 memory**。
6. **5 维结构必填**——未触发的维度写"本 session 无新增"。

---

## 文件命名

```
<date>-<model>-<scenario>.md
```

- `<date>` = `YYYY-MM-DD`
- `<model>` = 模型根 Frame 路径末段（`.UserObjects.Warehouse` → `Warehouse`），多个 root 用逗号
- `<scenario>` = kebab-case,≤5 个英文词

**示例**：`2026-09-01-Factory51-warehouse-orientation.md`

> student 文件名**不带** `_session-summary_` 中缀——这是 student agent 的命名例外。跨 agent 公共 CONTRIBUTING 允许此例外。

---

## 5 维结构（每篇必填）

```markdown
# <主题一句话>
**Date:** YYYY-MM-DD  **Agent:** plant-simulation-student
**Model:** <model>
**Scenario:** <scenario>

## 01-factory-know-how
<工厂/仓库建模模式观察>

## 02-simtalkclaude-knowhow
<桥协议相关观察>

## 03-modeling-know-how
<通用建模，含 01-objects / 02-simtalk / 03-software 子节按需>

## 04-modeling-example
<可借鉴示例>

## 05-modeling-experience
<经验沉淀：Quirk / 模式 / 反模式>

## Cross-references
- `02-domain-know-how/<子目录>/<file>.md`
- 同 model prior session: `<prior-file>.md`

## Open questions / cross-pollination
- <未关闭问题 + 建议 curator 评审的 finding>
```

---

## 与 curator 的协作边界

| 边界 | student 责任 | curator 责任 |
|---|---|---|
| 谁读谁 | 写 `student-memory/` | 读 + 评审 + 沉淀到 `03-modeling-experience/` |
| Open questions 段 | 标记 "建议 curator 沉淀" 候选 | 评审 + 沉淀或 quarantine |
| Quirk 漂移 | 在 5 维结构里 cite Quirk #N | quarantine → 转 `skills-optimizer` |

---

## 不做的事

- ❌ append 到已有 session note 正文（除末尾 `Operator self-review` 段）。
- ❌ 写 SimTalk / 改模型 / 调 skill 脚本。
- ❌ 直接 Edit `02-domain-know-how/`（那是 curator 的活）。
- ❌ 用 expert 的 `_session-summary_` 命名（student 例外）。
- ❌ 单文件超 300 行硬塞。
- ❌ 跳过 5 维结构（即便"本 session 无新增"也要占位）。