---
last_updated: 2026-09-01
audience: plant-simulation-experience-curator（以及任何需要往 03-modeling-experience 写新 finding 的人）
---

# Contributing to `03-modeling-experience/`

本目录是 `plant-simulation-experience-curator` 沉淀的**长期经验资产**。**Append-via-new-file only**——严禁 append 到已有非 README 文件正文。

---

## 🔴 铁律（必读）

1. **每文件硬上限 ≤300 行**——超限立即拆 `<topic>-part1.md` / `<topic>-part2.md`，并在 README 各索引一行。
2. **每个 finding/topic = 一个新文件**——严禁修改已有文件正文、严禁合并旧 entry。
3. **README 是该目录唯一索引**——顶层 + 子目录 README 每次写入必须 append 一行 + bump `last_updated`。
4. **新文件 `YYYY-MM-DD` ≥ source session 日期**——避免时间倒置。

---

## 子目录路由 / Subdir Routing

| Finding 类型 | 落到 |
|---|---|
| skill CLI / API / Quirk / 最佳实践 / `simtalk_*` 行为 | `01-skill-experience/` |
| 用户预期 / 偏好 / 沟通模式 / 教学节奏 / 提问习惯 | `02-user-expectation-experience/` |
| 具体模型建模 pattern / 架构 / 坑 | `03-modeling-experience/` |

---

## 文件命名 / File Naming

```
<YYYY-MM-DD>_<topic-slug>.md
```

- `YYYY-MM-DD` ≥ source session 日期。
- `<topic-slug>` 用 kebab-case，3-5 词。
- 不带版本号、不带 `v2/final` 等修饰。

---

## 文件 frontmatter（必填）

```markdown
---
last_updated: YYYY-MM-DD
dimension: 01-skill-experience | 02-user-expectation-experience | 03-modeling-experience
source_sessions:
  - 04-agent-memory/plant-simulation-expert-memory/YYYY-MM-DD_session-summary_<topic>.md
skills_touched: [<skill1>, <skill2>]
models_touched: [<model1>, <model2>]
---
```

---

## 文件正文模板（≤300 行）

```markdown
# <主题一句话>

## 症状
- <一句话>

## 根因
- <一句话>

## Workaround / 结论
- <代码 / 命令 / 决策>

## see also
- `path/to/related.md §X`
- `skills/<x>/SKILL.md §Y`

## 反思（可选，≤3 行）
- <1-2 句心智模型沉淀>
```

---

## README bump 协议（写入后**立即**执行）

1. 顶层 [`README.md`](./README.md) —— 在 `## Files` 表 append 一行 + bump frontmatter `last_updated`。
2. 受影响子目录 README —— 同样 append + bump。
3. Newest at top。

---

## 绝对不做的事

- ❌ append 到已有非 README `.md` 正文。
- ❌ 删 / 改老 entry。
- ❌ 调任何 skill 脚本（这是离线资产策展）。
- ❌ 评估 `SKILL.md` 准确性（那是 `skills-optimizer` 的活）。
- ❌ 跨多个子目录重复落同一 finding（用 `see also` 交叉引用）。