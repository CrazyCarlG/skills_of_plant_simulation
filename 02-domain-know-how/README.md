---
last_updated: 2026-09-01
contributors: [@plant-simulation-expert]
scope: Plant Simulation 领域知识库总入口(按 7 维主题组织:工厂/桥/对象/语言/工作流/示例/经验)
---

# 02-domain-know-how — Plant Simulation 领域知识库

> **定位**:本目录是 **Plant Simulation 仿真领域的"知识 + 经验"沉淀**,按"领域类型"分层组织。
>
> **与源目录关系**:
> - **来源**:从 `02-simulation-file-experience/`(48 篇) + `03-agent-memory/`(14 篇) **理解内容后重新撰写**
> - **重组策略**:不是简单复制,而是**按主题归位** + **去重 + 提炼** → 形成 7 维知识体系
> - **保留原始文件**:源目录(02-simulation-file-experience/ 与 03-agent-memory/)未删除,作为 fallback 与历史时间线

## 目录结构

```
02-domain-know-how/
├── 01-factory-know-how/                    ← 工厂与仓库案例
│   ├── README.md
│   ├── factory-modeling-architecture.md
│   └── warehouse-and-ctu-patterns.md
├── 02-simtalkclaude-knowhow/               ← SimtalkClaude TCP 桥
│   ├── README.md
│   ├── bridge-architecture.md
│   ├── v1-vs-v2-comparison.md
│   └── operational-patterns.md
├── 03-modeling-know-how/                   ← 通用建模知识
│   ├── 01-objects/
│   │   ├── README.md
│   │   └── object-classification.md
│   ├── 02-simtalk/
│   │   ├── README.md
│   │   └── language-quirks-reference.md
│   └── 03-software/
│       ├── README.md
│       ├── skill-orchestration-guide.md
│       └── contribution-protocol.md
├── 04-modeling-example/                    ← 建模示例
│   ├── README.md
│   ├── assembly-line-patterns.md
│   ├── vendor-library-extension.md
│   ├── probe-pipeline-quirks.md
│   └── simtalk-implementation-quirks.md
└── 05-modeling-experience/                 ← 经验沉淀
    ├── README.md
    ├── skill-test-coverage-matrix.md
    ├── consolidated-insights.md
    └── session-summaries/                  ← 14 篇 session summary
```

## 各分类索引

### [01-factory-know-how](./01-factory-know-how/) — 工厂与仓库案例

| 文件 | 内容主题 |
|---|---|
| [`README.md`](./01-factory-know-how/README.md) | 工厂案例阅读顺序 + 核心可借鉴模式 |
| [`factory-modeling-architecture.md`](./01-factory-know-how/factory-modeling-architecture.md) | Class Library / Models 二分法 + 模型即类库包 + Hardware/Software 分层 |
| [`warehouse-and-ctu-patterns.md`](./01-factory-know-how/warehouse-and-ctu-patterns.md) | RCS 控制中枢 / DataTable 状态机 / 三级执行器 / 触发点防重入 |

### [02-simtalkclaude-knowhow](./02-simtalkclaude-knowhow/) — SimtalkClaude TCP 桥

| 文件 | 内容主题 |
|---|---|
| [`README.md`](./02-simtalkclaude-knowhow/README.md) | 总入口 + 阅读顺序 |
| [`bridge-architecture.md`](./02-simtalkclaude-knowhow/bridge-architecture.md) | 桥架构 + 四层目录 + TCP 帧协议 + scratch buffer 模式 |
| [`v1-vs-v2-comparison.md`](./02-simtalkclaude-knowhow/v1-vs-v2-comparison.md) | v1 vs v2 方法清单 + 协议差异 + 迁移风险 |
| [`operational-patterns.md`](./02-simtalkclaude-knowhow/operational-patterns.md) | 11 类 Quirk 实测 + 12 项推荐 + 8 个反模式 |

### [03-modeling-know-how](./03-modeling-know-how/) — 通用建模知识

| 子目录 | 内容主题 |
|---|---|
| [`01-objects/`](./03-modeling-know-how/01-objects/) | 对象概念(Class/Instance/Frame/Folder)+ 判定方法 |
| [`02-simtalk/`](./03-modeling-know-how/02-simtalk/) | SimTalk 字面契约 + 10 大类易踩坑 |
| [`03-software/`](./03-modeling-know-how/03-software/) | skill 调用决策 + 写操作硬流程 + 贡献协议 |

### [04-modeling-example](./04-modeling-example/) — 建模示例

| 文件 | 内容主题 |
|---|---|
| [`assembly-line-patterns.md`](./04-modeling-example/assembly-line-patterns.md) | 装配生产线 + WorkerChart + PalletOptimization + 2 个 Analyzer |
| [`vendor-library-extension.md`](./04-modeling-example/vendor-library-extension.md) | MaterialFlow_AGV 库 + AGV_Claude 7 方法 |
| [`probe-pipeline-quirks.md`](./04-modeling-example/probe-pipeline-quirks.md) | 探针工具 4 个隐性 quirk |
| [`simtalk-implementation-quirks.md`](./04-modeling-example/simtalk-implementation-quirks.md) | SimTalk 实现期 12 个坑(Quirk #1-#12) |

### [05-modeling-experience](./05-modeling-experience/) — 经验沉淀

| 文件 | 内容主题 |
|---|---|
| [`README.md`](./05-modeling-experience/README.md) | 总入口 + 14 篇 session 索引 |
| [`skill-test-coverage-matrix.md`](./05-modeling-experience/skill-test-coverage-matrix.md) | 9 skill 全量测试覆盖矩阵 |
| [`consolidated-insights.md`](./05-modeling-experience/consolidated-insights.md) | 跨 session 洞察(5 大主题 + 8 个硬规则) |
| [`session-summaries/`](./05-modeling-experience/session-summaries/) | 14 篇历史 session 报告 |

## 何时不需要读本目录

- **运行时错误**(exit=10/11/12/20)→ 直接看 [`03-modeling-know-how/03-software/skill-orchestration-guide.md §3.4`](./03-modeling-know-how/03-software/skill-orchestration-guide.md)
- **某个 skill 不会用** → 看 `skills/<name>/SKILL.md`
- **写新 SimTalk 的语法问题** → 看 [`03-modeling-know-how/02-simtalk/language-quirks-reference.md`](./03-modeling-know-how/02-simtalk/language-quirks-reference.md)
- **Plant Simulation 官方文档查属性/方法签名** → 看 `01-plantsimulation-knowledge/01-plant-simulation-help/`

## 推荐 agent 冷启动流程

```
1. Read 02-domain-know-how/README.md (本文件)
2. Read 各主题目录的 README.md (7 篇,~50 行/篇,~400 行)
3. Read 05-modeling-experience/consolidated-insights.md (跨 session 洞察)
4. Read 05-modeling-experience/skill-test-coverage-matrix.md (skill 验证基线)
5. 按当前任务匹配的主题目录,深读对应文件
6. 仅当需要"决策上下文"时才打开 session-summaries/ 具体某篇

# 14 篇 session + 48 个源文件 → 7 篇 README + 14 篇主体文档 (本目录最终结构)
```

## 重构元数据

- **重构日期**:2026-09-01
- **重构执行者**:plant-simulation-expert
- **重构方式**:**理解文件内容后重新创建**,而非简单复制
- **重构来源**:
  - `02-simulation-file-experience/` 全部内容(48 个 .md)
  - `03-agent-memory/plant-simulation-expert-memory/` 14 篇 session summary
- **重构策略**:
  - **内容主体重新撰写** —— 按 7 维主题归位、去重、提炼
  - **顶层 README + 各子目录 README 新撰写** —— 作为新结构的入口索引
  - **保留 append-only 时间线** —— 每个文件的 `## 经验 Log` 区保留为空占位
  - **保留历史 session 摘要** —— 14 篇 session summary 重写为统一模板(Goals / What was done / Key findings / Cross-references / Open questions)
  - **未删除任何源文件** —— 源目录仍保留作为 fallback,后续 curator 评估后可选择性清理
</content>
</invoke>