---
last_updated: 2026-09-01
contributors: [@plant-simulation-student]
scope: `plant-simulation-student` agent 产出的"模型学习 session 笔记"索引,按 Date + Model + Scenario 维度
---

# 04-agent-memory/student-memory — 模型学习 session 笔记索引

> **定位**:本目录是 `plant-simulation-student` agent 的**只写**记忆区。每个 session 笔记 = 一份按 `02-domain-know-how/` 5 维结构镜像分析某个用户仿真模型的观察报告。
>
> **与 `plant-simulation-expert-memory/` 的区别**:
> - expert = 跑 SimTalk / 写方法 / 改模型 / 执行任务 → session summary 记录"做了什么"
> - student = 只读扫描 / 提炼模式 / 5 维分析 → session note 记录"学到了什么"
>
> **何时不需要读本目录**:
> - 想看专家的执行流水 → `../plant-simulation-expert-memory/`
> - 想看已沉淀到知识库的 finding → `../../02-domain-know-how/`

## 命名与路径

- **路径**:``04-agent-memory/student-memory/<date>-<model>-<scenario>.md``
  - `<date>` = `YYYY-MM-DD`
  - `<model>` = 模型根 Frame 路径末段(`.UserObjects.Warehouse` → `Warehouse`),多个 root 用逗号
  - `<scenario>` = 用户场景简述,kebab-case,不超过 5 个英文词
- **示例**:`2026-09-01-Factory51-warehouse-orientation.md`

## 索引表(newest at top)

| Date | Model | Scenario | Top finding | Path |
|---|---|---|---|---|

## 5 维结构

每篇 session 笔记固定包含以下章节(未触发的维度写"本 session 无新增"):

1. `## 01-factory-know-how` — 工厂/仓库建模模式
2. `## 02-simtalkclaude-knowhow` — 桥协议相关观察
3. `## 03-modeling-know-how` — 通用建模(`01-objects` / `02-simtalk` / `03-software` 子节按需)
4. `## 04-modeling-example` — 可借鉴示例
5. `## 05-modeling-experience` — 经验沉淀(Quirk / 模式 / 反模式)
6. `## Cross-references` — 引用过的知识库条目 + 同模型 prior session
7. `## Open questions / cross-pollination` — 未关闭问题 + 建议由 curator 评审的 finding

## 何时需要读本目录

- **新 student session 开始前**:命中某 Model + Scenario 组合的 prior session,先读避免重复扫描
- **curator 评估沉淀候选**:扫 `## Open questions / cross-pollination` 段,看是否有值得 append 到 `02-domain-know-how/` 的 finding
- **用户问"我们之前学过 X 模型吗"**:查索引表定位

## 与其他目录的关系

| 目录 | 内容性质 | 关系 |
|---|---|---|
| `04-agent-memory/student-memory/`(本目录) | student 产出的模型学习笔记 | **候选 finding 池**,供 curator 评估 |
| `04-agent-memory/plant-simulation-expert-memory/` | expert 的执行 session summary | **并行记忆**,与 student 同侧但维度不同(执行 vs 学习) |
| `02-domain-know-how/` | 已沉淀的领域知识(append-only) | **本目录的目标归宿**——由 curator 评审后沉淀 |
| `agents/curator-reports/` | curator 的评审报告 | **本目录的治理输出**——读 curator 报告可追溯哪些 finding 被采纳/拒绝 |

## 重构元数据

- 创建日期:2026-09-01
- 创建执行者:plant-simulation-student(由用户指示新增)
- 创建原因:用户希望把"读模型"与"写模型"两条 agent 路径拆开,student 走只读扫描 + 5 维镜像分析,不污染 expert 的执行日志