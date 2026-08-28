# 02-simulation-file-experience —— Plant Simulation 经验沉淀

> **定位**：本目录是 **Plant Simulation 仿真领域的经验沉淀**，按"知识类型"分层组织。
> agent（特别是 `plant-simulation-expert`）在新任务时按"我要什么"直接定位。
>
> **目录原则**：每层放一类互斥的知识；`01-` `02-` 前缀暗含"读顺序"——先理解概念、再懂桥、再学操作、再看实例。

---

## 阅读顺序（推荐）

```
01-domain-concepts       ← Plant Simulation 领域概念（与模型无关）
02-bridge-tool           ← SimtalkClaude 桥内部（v1/v2 协议 + 模式）
03-workflow-playbook     ← 跨 9 skill 的工作流 + 写操作硬协议
04-model-case-studies    ← 3 个真实模型的踩坑 / 借鉴案例
05-session-archives      ← 一次性 session 报告
```

---

## 各分类索引

### [01-domain-concepts](./01-domain-concepts/) —— Plant Simulation 领域知识

| 文件 | 何时读 |
|---|---|
| [`class-instance-frame-folder.md`](./01-domain-concepts/class-instance-frame-folder.md) | 写 / 读任何 Plant Simulation 对象前必读；解释 Class vs Instance / Frame vs Folder 判定方法（`Origin`/`Class`/`OriginRoot` 三元组） |
| [`derived-methods-quirks.md`](./01-domain-concepts/derived-methods-quirks.md) | 跨文档反复出现的"字面契约 + 易踩小坑"速查（`strLen` vs `s.length`、observer 签名、`writeValue` 不转类型、`infoBox` 模态陷阱等） |

### [02-bridge-tool](./02-bridge-tool/) —— SimtalkClaude TCP 桥

| 文件 | 何时读 |
|---|---|
| [`INDEX.md`](./02-bridge-tool/INDEX.md) | 本分类索引；先按主题选择文件 |
| [`simtalkclaude-v1-and-v2.md`](./02-bridge-tool/simtalkclaude-v1-and-v2.md) | 总入口：版本范围、主题导航、append-only 经验 Log |
| [`simtalkclaude-overview.md`](./02-bridge-tool/simtalkclaude-overview.md) | 定位、支持动作、四层目录与后续方向 |
| [`simtalkclaude-protocol.md`](./02-bridge-tool/simtalkclaude-protocol.md) | TCP 帧、动作路由、鉴权、回复字段、handler 模式 |
| [`simtalkclaude-v2-features.md`](./02-bridge-tool/simtalkclaude-v2-features.md) | v2 相对 v1 的新增功能 |
| [`simtalkclaude-lessons.md`](./02-bridge-tool/simtalkclaude-lessons.md) | 实测教训、推荐实践与反模式 |
| [`simtalkclaude-v1-v2-delta.md`](./02-bridge-tool/simtalkclaude-v1-v2-delta.md) | v1 vs v2 方法清单差异、协议差异与迁移风险 |

### [03-workflow-playbook](./03-workflow-playbook/) —— 跨 skill 工作流

| 文件 | 何时读 |
|---|---|
| [`skill-call-playbook.md`](./03-workflow-playbook/skill-call-playbook.md) | 9 skill 依赖图、决策矩阵（"我要 X 用哪个 skill"）、Top 10 高频坑、写操作 5 步硬流程、退出码语义 |

### [04-model-case-studies](./04-model-case-studies/) —— 3 个真实模型

| 模型 | 何时读 | 子文件 |
|---|---|---|
| **assembly-line** | 想知道"自定义生产线的 Frame-with-UI / 实验管理器 / analyzer 怎么做" | [`README`](./04-model-case-studies/assembly-line/README.md) · [`business-logic`](./04-model-case-studies/assembly-line/assembly-line-business-logic.md) · [`analyzers-pattern`](./04-model-case-studies/assembly-line/analyzers-pattern.md) · [`probe-pipeline-quirks`](./04-model-case-studies/assembly-line/probe-pipeline-quirks.md) |
| **ctu-warehouse** | 想知道"模型即类库包 + 自带 BasicObjects 副本 + AGV/CTU 调度"怎么搭 | [`modeling-experience`](./04-model-case-studies/ctu-warehouse/p4-ctu-modeling-experience.md) · [`class-inheritance`](./04-model-case-studies/ctu-warehouse/p4-ctu-class-inheritance.md) |
| **factory51** | 想知道"Siemens 官方 Class Library / Models 二分法 + 接入 SimtalkClaude v2 后怎么保持隔离" | [`README`](./04-model-case-studies/factory51/README.md) · [`integration-with-simtalkclaude`](./04-model-case-studies/factory51/factory51-simtalkclaude-integration.md) |

### [05-session-archives](./05-session-archives/) —— 一次性 session 报告

| 文件 | 何时读 |
|---|---|
| [`2026-08-27-skill-test-summary.md`](./05-session-archives/2026-08-27-skill-test-summary.md) | 9 skill 全量测试的总结（覆盖矩阵 + 经验教训）。需要历史背景时看 |

---

## 何时不需要读本目录

- **运行时错误**（exit=10/11/12/20）→ 直接看 [`03-workflow-playbook/skill-call-playbook.md` §3.4](./03-workflow-playbook/skill-call-playbook.md)
- **某个 skill 不会用** → 看 `skills/<name>/SKILL.md`
- **写新 SimTalk 的语法问题** → 看 `01-plantsimulation-knowledge/01-plant-simulation-help/simtalk/`

---

## 经验沉淀协议

### 触发点（什么时候必须停下来沉淀）

| 时机 | 为什么要停 |
|---|---|
| **session 末尾**（写完 session summary 之前） | 趁上下文还热，回顾"这次踩了什么坑 / 验证了什么模式" |
| **里程碑达成**（如完成一次 skill 全量测试 / 修复一个 Quirk） | 一次性深度 session 值得立即提炼，否则热度过期 |
| **新坑发现**（撞到 lifelines.md / SKILL.md 没写过的行为） | 临场记忆最准，延迟沉淀会丢失上下文细节 |
| **跨 session 重复出现**（同一坑在两个 session summary 里都提到） | 这是"值得永久沉淀"的强信号 |

> **纪律**：以上任一触发点出现 → **先沉淀、再继续**。不要"先做下一个任务，回头补"——补几乎不会发生。

### 路径分配（沉淀到哪里）

发现新坑 / 新模式 / 新 Quirk 时：

1. **是 skill bug** → 写到 `skills/<name>/log/YYYY-MM-DD_<topic>.md`
2. **是领域知识** → 更新本目录对应分类的现有文件，**别新建**（除非真是一个全新主题）
3. **是 SimtalkClaude 桥内部** → 更新 `02-bridge-tool/` 下对应文件
4. **是跨 skill 的工作流** → 更新 `03-workflow-playbook/skill-call-playbook.md`
5. **是模型特定经验** → 更新对应 `04-model-case-studies/<model>/` 子目录

不要在根目录再放裸 `.md` 文件——一律归类到 `01-` 到 `05-` 的子目录里。

### 自检清单（沉淀前 30 秒）

- [ ] 这条经验能跨 session 复用吗？（一次性 session 流水 → 不沉淀，归 `03-agent-memory/`）
- [ ] 这条经验已经存在于某篇文档的某节吗？→ **更新现有节**，别复制粘贴到新文件
- [ ] 分类对吗？走"路径分配" 5 条规则
- [ ] 写完后 grep 一下关键词，确认未来能搜到

---

## 推荐工作流：用 curator agent 沉淀

本目录的**日常维护**推荐交给 [`plant-simulation-experience-curator`](../agents/plant-simulation-experience-curator.md) agent——它专门负责去重 / 分类 / 索引治理，避免"使用者在主对话里顺手 append 低质量 entry"。

```text
plant-simulation-expert
  └─ 产出：session summary + per-skill log（candidate）
        │
        ▼
plant-simulation-experience-curator
  └─ 产出：agents/curator-reports/INDEX.md + 单次报告 + 候选补丁
        │
        ▼ （用户或 verification 复核后）
02-simulation-file-experience/<file>.md §经验 Log（append 一条新 entry）
```

**硬约束**：curator 本身**不**直接 edit 本目录任何文件——所有 append 走 patch + 用户 / `verification` 复核后再 `Edit` 落地。详细协议见 [`CONTRIBUTING.md`](./CONTRIBUTING.md) 与 curator agent 文件。

