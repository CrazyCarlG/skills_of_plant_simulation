---
last_updated: 2026-09-01
audience: plant-simulation-experience-curator（主） + 任何需要补 / 改知识库的人
---

# Contributing to `02-domain-know-how/`

本目录是 Plant Simulation **领域知识库**——按 7 维主题组织的**稳定知识资产**（主体文章可精修，`## 经验 Log` 区 append-only）。

> **与 `03-modeling-experience/` 的区别**：
> - 本目录 = **手工策展的知识主体**（main body 可精修）
> - `03-modeling-experience/` = **curator 新发现入口**（append-via-new-file，main body 不允许改）

---

## 🔴 铁律

1. **主体文章（main body）允许精修**——但保留版本演进痕迹（frontmatter `last_updated` + 必要时 append "修订说明" 段）。
2. **`## 经验 Log` 区 append-only**——新 finding 只 append，不改老 entry；supersede 时老 entry 顶部加 marker，正文保留。
3. **每文件 ≤300 行**——超限拆 `<topic>-part1.md` / `<topic>-part2.md`。
4. **每次改必 bump frontmatter `last_updated`** + 同步更新对应 README 索引行。
5. **不删除任何 .md**——所有文件都是知识资产；想清理走 "supersede + 留档" 路径。

---

## 7 维主题结构

| 子目录 | 主题 |
|---|---|
| `01-factory-know-how/` | 工厂与仓库案例 |
| `02-simtalkclaude-knowhow/` | SimtalkClaude TCP 桥 |
| `03-modeling-know-how/01-objects/` | 对象概念（Class/Instance/Frame/Folder） |
| `03-modeling-know-how/02-simtalk/` | SimTalk 字面契约 + 易踩坑 |
| `03-modeling-know-how/03-software/` | skill 调用决策 + 写操作硬流程 + 贡献协议 |
| `04-modeling-example/` | 建模示例 |
| `05-modeling-experience/` | 经验沉淀（含 `session-summaries/`） |

---

## 文件命名

```
<topic-slug>.md
```

- kebab-case，3-6 词。
- **不带日期前缀**（这是稳定知识，不是 session log）。
- **不带版本号 / `v2/final` 修饰**。

---

## 文件结构（必填）

```markdown
---
last_updated: YYYY-MM-DD
contributors: [@handle1, @handle2]
tags: [tag1, tag2]
---

# <主题一句话>

## <主体内容章节>

...

## 经验 Log（append-only）

<!-- curator 在此处 append 新 entry；不要改上面的主体 -->

### YYYY-MM-DD by @handle

- **症状**：
- **根因**：
- **Workaround / 结论**：
- **tags**：
- **see also**：
```

---

## 与其他目录的边界

| 目录 | 角色 | 流向 |
|---|---|---|
| `02-domain-know-how/`（本目录） | 稳定知识主体 | 归宿（append-only 经验 Log） |
| `03-modeling-experience/` | curator 新发现入口 | 单次发现先落这里 |
| `04-agent-memory/plant-simulation-expert-memory/` | expert session 流水 | 由 curator 评审 → 路由到本目录 or `03-modeling-experience/` |
| `skills/<x>/references/` | skill 内的 Quirk 表 | 互补（不替代本目录） |

---

## 经验 Log entry 模板

```markdown
### YYYY-MM-DD by @handle

- **症状**：（一句话，发生了什么 / 报了什么错）
- **根因**：（一句话；未明写"未知"）
- **Workaround / 结论**：（代码 / 命令 / 决策）
- **tags**：`simtalk, bridge, ...`
- **see also**：`path/to/related.md §X`
```

---

## 不做的事

- ❌ 删 / 改老 entry 正文（append-only 协议）。
- ❌ 跳过 `## 经验 Log` 段（即便无新增也要保留空占位 + 注释说明）。
- ❌ 评估 Quirk 编号准确性（那是 `skills-optimizer` 的活）。
- ❌ 调任何 skill 脚本（这是离线策展）。
- ❌ 把 finding 同时写到本目录 + `03-modeling-experience/`——走 `see also` 交叉引用。
- ❌ 单文件超 300 行硬塞。