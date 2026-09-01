---
last_updated: 2026-09-01
contributors: [@plant-simulation-expert]
scope: 工厂与仓库领域核心建模模式(架构 + 调度)
---

# 01-factory-know-how — 工厂与仓库建模知识

本目录整合 **工厂与仓库建模** 的核心模式,基于 Siemens 官方 Factory51 + P4_CTU 两个真实案例提炼。

## 文件索引

| 文件 | 内容主题 |
|---|---|
| [`factory-modeling-architecture.md`](./factory-modeling-architecture.md) | 工厂建模的架构模式:Class Library / Models 二分法 + 模型即类库包 + Hardware/Software 分层 |
| [`warehouse-and-ctu-patterns.md`](./warehouse-and-ctu-patterns.md) | 立体仓库(CTU + AGV)调度的核心模式:RCS 控制中枢 / DataTable 状态机 / 三级执行器 / 触发点防重入 / 生命周期 hook |

## 阅读顺序建议

1. **先读 [`factory-modeling-architecture.md`](./factory-modeling-architecture.md)** —— 理解"类定义 vs 实例"的二分法,以及"模型即类库包"的可移植性设计
2. **再读 [`warehouse-and-ctu-patterns.md`](./warehouse-and-ctu-patterns.md)** —— 理解 RCS 控制中枢 + DataTable 状态机 + 触发点防重入的工程模式

## 核心可借鉴模式速查

| 模式 | 出处 | 价值 |
|---|---|---|
| Class Library / Models 二分法 | Factory51 | 业务类定义与运行时实例分目录存放 |
| "一条线定义、两条线实例化" | Factory51 P1/P2 | Origin 指向 Production,改参数一次循环搞定 |
| 模型即类库包(Folder-as-Package) | P4_CTU | 整套 Hardware/Software 打包成可重用 class library |
| BasicObjects 携带类库副本 | P4_CTU | 自包含、跨机可移植,不依赖全局库版本 |
| SimtalkClaude 作为顶层 Folder 隔离 | Factory51 | 不污染业务命名空间 |
| Hardware/Software 分层 | P4_CTU AdvancedObject | 物理设备 vs 控制中枢分离 |
| DataTable 即状态机 | P4_CTU RCS | 一切状态在表里,清空即冷启动 |
| 三级执行器(Task → Device → Execute) | P4_CTU | 任务/设备/执行清晰分层 |
| 触发点防重入(`_Running` + `executeNewCallchain`) | P4_CTU | 任何"长跑 worker"的标准三件套 |
| 生命周期 hook(OnCreate/OnDelete/OnMove)自动注册 | P4_CTU | 动态对象自动加入控制中枢 |

## 重构元数据

- 重构日期:2026-09-01
- 重构来源:`02-simulation-file-experience/04-model-case-studies/{factory51,ctu-warehouse}/` 4 篇
- 重构策略:从 4 篇源文档提炼模式,重新撰写为 2 篇主题导向文档(架构 + 调度模式)
</content>
</invoke>