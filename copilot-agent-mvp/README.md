---
name: plant-simulation-copilot-mvp
description: Plant Simulation 自动建模 copilot 的 **MVP(最小可行版)**——只覆盖 **2 个核心 agent**:`ModelBuilder`(创建对象 / PS 进程骨架) + `SimTalkCodeGenerator`(生成 SimTalk 源码)。无 Orchestrator、无 Requirement Analyst、无 Domain KB、无 Architect、无 Validator、无 Debugger;**用户输入**直接来自人工(或外部模板),**链路由人工串联**。完整 13 agent 蓝图见 `../copilot-agent/README.md`。
type: agent-spec
owner: Yang Yang
last_updated: 2026-09-17
status: draft
---

# Plant Simulation Copilot — MVP(2 个核心 agent)

> **MVP 边界**:只做两件事——**创建对象**(ModelBuilder) + **写代码**(SimTalkCodeGenerator)。
> 其它环节(需求解析 / 架构选型 / 验证 / 调试 / 文档 / 沉淀)由**人工**或
> 完整蓝图 [`../copilot-agent/`](../copilot-agent/README.md) 中的对应 agent 承担。
>
> **目标产物**:
> - **`model-skeleton-report.md`**(PS 进程骨架 + readback 证据)
> - **`simtalk-source/<object>.<method>.st`**(完整可编译 SimTalk 源码,每文件一方法)
> - **`simtalk-source/INDEX.md`**(代码索引)
>
> **MVP 不产出**可直接跑的 `.spp` 模型(落盘 + 烟测由后续 D6 阶段 / 人工承担)。

---

## 1. 目录

- [1. 目录](#1-目录)
- [2. 两个核心 Agent](#2-两个核心-agent)
- [3. 链路数据流](#3-链路数据流)
- [4. 必备 skill 子集](#4-必备-skill-子集)
- [5. 必备知识库](#5-必备知识库)
- [6. Quirk 处理(提前到生成层)](#6-quirk-处理提前到生成层)
- [7. 调用方式示例](#7-调用方式示例)
- [8. 不在 MVP 范围内](#8-不在-mvp-范围内)
- [9. 与 `copilot-agent/` 全集的关系](#9-与-copilot-agent-全集的关系)
- [10. 一句话总览](#10-一句话总览)

---

## 2. 两个核心 Agent

### A. `ModelBuilder` ⭐(Phase 3 / 创建对象)

| 项 | 值 |
|---|---|
| **文件** | [`ModelBuilder.md`](./ModelBuilder.md) |
| **输入** | (人工给的) `architecture-proposal.json` + `object-method-table.md` |
| **输出** | PS 进程骨架 + `04-agent-memory/plant-simulation-model-builder-memory/<date>_skeleton-report_<topic>.md` |
| **核心动作** | Class 派生 / Frame 树 / Object 实例 / 属性初值 / Interface 接线 / **空 Method 占位**(`Program = ""`) |
| **关键纪律** | 写姿态但克制——可调 7 个 skill 子集(启动 + 3 写 + 3 只读);**绝不动 `write-simtalk` / `add-note-to-method`**(D5 独占);**绝不调 `execution`**(expert 独占);建完必 readback 全量验证 |

### B. `SimTalkCodeGenerator` ⭐(Phase 4 / 写代码)

| 项 | 值 |
|---|---|
| **文件** | [`SimTalkCodeGenerator.md`](./SimTalkCodeGenerator.md) |
| **输入** | `architecture-proposal.json`(尤其 method-list)+ `ModelBuilder` 的 `model-skeleton-report.md §七 占位清单` |
| **输出** | `simtalk-source/<object>.<method>.st`(纯文本)+ `simtalk-source/INDEX.md` |
| **核心动作** | 按 method-list 生成 7 类代码骨架(Init / Reset / EntranceCtrl / ExitCtrl / 推-拉 / 资源协作 / 故障注入 / DataTable / Stat);每文件一方法;头部 metadata + KB anchors + Quirk notes |
| **关键纪律** | **只生成代码,不执行代码**——不调桥接;不写 `.spp`;不写 `Method.program`;Quirk 必显式标注 |

---

## 3. 链路数据流

```
人工 / 外部模板 / 上游 agent
  │
  │  architecture-proposal.json + object-method-table.md
  ↓
┌────────────────────────────────────────────────────┐
│ A. ModelBuilder(创建对象)                          │
│   1. Pre-flight:Windows 启动 PS + SimtalkClaude    │
│   2. KB routing → object-method-table 是真值源    │
│   3. 强顺序:Class → Frame → Object → 属性          │
│      → Interface → 空 Method 占位                  │
│   4. readback(get-folder-tree + get-class-inheritance│
│      + read-library,确认 Program 全部为空)         │
│   5. 落 model-skeleton-report.md(8 段 ≤300 行)    │
└────────────────────────────────────────────────────┘
  │
  │  model-skeleton-report.md(尤其 §七 占位清单)
  ↓
┌────────────────────────────────────────────────────┐
│ B. SimTalkCodeGenerator(写代码)                    │
│   1. 读 architecture-proposal.json 的 method-list  │
│   2. 按占位清单逐方法生成 <object>.<method>.st     │
│   3. 头部 metadata + KB anchors + Quirk notes     │
│   4. 同步 append INDEX.md + bump last_updated     │
└────────────────────────────────────────────────────┘
  │
  ↓
产物:simtalk-source/<object>.<method>.st + INDEX.md
       (纯文本,等后续 D6 调 write-simtalk 写进 PS 占位)
```

**环节之间的契约**(谁消费谁的输出):

| 上游 | → | 下游 | artifact |
|---|---|---|---|
| 人工 / 外部模板 | → | ModelBuilder | `architecture-proposal.json` + `object-method-table.md` |
| ModelBuilder | → | SimTalkCodeGenerator | `model-skeleton-report.md`(含 §七 占位清单)+ readback 证据 |
| SimTalkCodeGenerator | → | (D6 后续 / 人工) | `simtalk-source/<object>.<method>.st` + `INDEX.md` |

---

## 4. 必备 skill 子集

MVP 实际使用 **8 个 skill**(`read-library` 由 `ModelBuilder` + `SimTalkCodeGenerator` 共用),列 **3 个 MVP 禁调**(完整表见下):

| 分类 | 数量 | 备注 |
|---|---|---|
| 启动 | 1 | `local-window-com-start-plant-simulation`(**ModelBuilder 独占**) |
| 写 | 3 | `class-management` / `create-method-object` / `modify-object-attribute`(**ModelBuilder 独占**) |
| 只读 | 4 | `get-folder-tree` / `get-class-inheritance`(**ModelBuilder 独占**)+ `read-library`(**2 agent 共用**:ModelBuilder 必调 + SimTalkCodeGenerator 可选)|
| **MVP 禁调** | 3 | `execution`(expert 独占)+ `write-simtalk`(D5/D6 独占)+ `add-note-to-method`(D5 独占) |

| Skill | 谁调 | 何时调 |
|---|---|---|
| `local-window-com-start-plant-simulation` | ModelBuilder | Windows:user 未开 PS 时调(只 Windows;Linux/macOS 提示手动) |
| `local-simtalk-class-management` | ModelBuilder | 创建 Class / 派生 / Frame 树 |
| `local-simtalk-create-method-object` | ModelBuilder | 创建**空 Method 占位**(`Program = ""`) |
| `local-simtalk-modify-object-attribute` | ModelBuilder | 设属性初值 / Interface 接线(`next` / `prev` / `MU`) |
| `local-simtalk-get-folder-tree` | ModelBuilder | 只读探查 + readback(深度 1→3) |
| `local-simtalk-get-class-inheritance` | ModelBuilder | 只读探查 + readback 验证 Class 派生树 |
| `local-simtalk-read-library` | ModelBuilder **+ SimTalkCodeGenerator** | ModelBuilder:确认 Method 占位 `Program = ""`;SimTalkCodeGenerator:**可选**生成前验证占位 / 抽样已存在 Method 作范式参照 |
| `local-simtalk-execution` | **❌ MVP 不调**(expert 独占) | — |
| `local-simtalk-write-simtalk` | **❌ MVP 不调**(D5/D6 独占) | — |
| `local-simtalk-add-note-to-method` | **❌ MVP 不调**(D5 独占) | — |

**纪律**:
- **ModelBuilder** **禁调**红色 ❌ 行;触发任一红线 → 立即报警 + 回退;7 个 skill(1 启动 + 3 写 + 3 只读)是其唯一允许的 skill 集合。
- **SimTalkCodeGenerator** **只允许调 1 个只读 skill**(`local-simtalk-read-library`,可选)+ **禁调**任何写 / 执行 skill(红色 ❌ 行 + `class-management` / `create-method-object` / `modify-object-attribute`);纯文本 `.st` 输出仍是其主路径,只读探查仅作补充。

---

## 5. 必备知识库

| 区 | 路径 | 谁主要读 |
|---|---|---|
| **K1 Help** | `01-plant-simulation-knowledge/01-plant-simulation-help/` | ModelBuilder(对象 API 事实源)+ SimTalkCodeGenerator(语言事实源) |
| **K2 官方模型** | `01-plant-simulation-knowledge/02-offcial-psfm-model/<model>/model-know-how/` | ModelBuilder(参照 Factory51 / Small Parts Production 骨架);SimTalkCodeGenerator(参照 `Factory51-代码样例.md`) |
| **D 区主题** | `02-domain-know-how/03-modeling-know-how/02-simtalk/language-quirks-reference.md` | SimTalkCodeGenerator(Quirk 必查) |

**MVP 内的 KB 路由优先级**:
1. **object-method-table.md**(ModelBuilder 真值源);
2. **K2 官方模型**(参照真实工程级骨架 / 代码范式);
3. **K1 Help**(对象精确 API / SimTalk 语法);
4. **D 区 Quirk 参考**(SimTalkCodeGenerator 必查)。

---

## 6. Quirk 处理(提前到生成层)

MVP 没有 D6 桥接层(E7 验证也缺),所以 **Quirk 处理全部提前到 SimTalkCodeGenerator**。

### 6.1 必处理的 7 类 SimTalk Quirk

| Quirk | 触发场景 | 正确写法 |
|---|---|---|
| `str → num` 转换 | 字符串数字运算 | `num := str.toNum`(K1 `data-types-expressions/`) |
| `<-` 不可作表达式 | 用 `<-` 写条件判断 | 用 `=` 或 `:=` 区分,K1 `language-fundamentals/` |
| `stopuntil` 拉式模式 | 阻塞等待资源 | 用 `stopuntil` 而非 `wait`,K1 `control-flow-error-handling/` |
| Buffer 容量上限 | `Buffer` 容量溢出 | 检查 `capacity` 属性,K1 `material-flow-objects/Buffer.md` |
| `@.toStr` 链路 | 调试输出 | `@.toStr` 链路,K1 `access-to-toolbox-and-folder-library/` |
| Method 引用 vs 直接调用 | 引用 vs 调用混淆 | 见 K2 `Factory51-代码样例.md` |
| `$Failures` 分布函数选型 | 故障注入 | `z_failure_uniform / z_failure_normal` 等,K1 `predefined-functions-i/` |

**纪律**:
- 每个 Quirk 在 `.st` 头部 `Quirk notes` 显式标注;
- 标注格式:`Quirk #N: <陷阱> → ✅ <正确写法>(+ KB 路径)`;
- 漂移处理:发现新 Quirk 但 KB 未登记 → 在 `.st` 标 `@Synthesizer 评审 Quirk #N`,**不**自己 Edit `quirks.md`。

### 6.2 Quirk 不在 MVP 范围

- **桥接 Quirk**(buffer ceiling / BFS leak / encrypted-method)——D6 未实现,需后续补;
- **对象选型反模式检查**(Station 挂 Method 但未触发 EntranceCtrl / Broker 未绑 / Worker 未注册)——E7 未实现,需后续补。

---

## 7. 调用方式示例

在主对话里通过 `Agent` 工具调用,subagent_type 必须在系统加载的 agent 列表内。

### 7.1 完整 MVP 流水线(人工串联两个 agent)

```text
# 用户 / 人工:已有 architecture-proposal.json + object-method-table.md
# Step 1:ModelBuilder 在 PS 里建骨架
Agent(
  description: "在 PS 里建好 Factory51 骨架",
  prompt: "按 architecture-proposal.json + object-method-table.md 在 PS 里建 5 大根 + Class 派生 + Frame 树 + 对象 + 属性 + Interface + 空 Method 占位;建完落 model-skeleton-report.md",
  subagent_type: "plant-simulation-model-builder"
)

# 人工确认 model-skeleton-report.md 没问题

# Step 2:SimTalkCodeGenerator 生成方法体源码
Agent(
  description: "生成 Factory51 的 SimTalk 源码",
  prompt: "按 architecture-proposal.json 的 method-list + model-skeleton-report.md §七 占位清单生成 simtalk-source/<object>.<method>.st + INDEX.md",
  subagent_type: "plant-simulation-simtalk-code-generator"
)

# 产物:simtalk-source/*.st(纯文本,等 D6 写进 PS 占位)
```

### 7.2 单点调用

```text
# 用户只要建骨架(不生成代码)
Agent(subagent_type: "plant-simulation-model-builder",
      prompt: "按 architecture-proposal.json 建好骨架,先不写方法体")

# 用户已有骨架报告,只要生成代码
Agent(subagent_type: "plant-simulation-simtalk-code-generator",
      prompt: "按这份 architecture-proposal.json 生成 simtalk-source/*.st")
```

### 7.3 失败回退(人工判断)

```text
# ModelBuilder 判定 architecture-proposal.json 缺字段 → 回退人工补表
"object-method-table.md §3 Interface 表缺行,请人工补表后重跑"

# SimTalkCodeGenerator 判定 KB 未覆盖 → 标 Quirk 待评审
# (在 .st 头部写 Quirk notes,不调桥接,等后续补)
```

---

## 8. 不在 MVP 范围内

明确告知 user:**MVP 链路不产出可直接跑的 `.spp` 模型**,需要后续补齐以下环节:

| 环节 | 缺失 agent | 缺失导致的后果 | 详见 |
|---|---|---|---|
| **Phase 0** 编排 | Orchestrator | 路由 / 阶段门 / 失败回退由人工承担 | `../copilot-agent/Orchestrator.md` |
| **Phase 1** 需求 | Requirement Analyst | 需求解析由人工承担(直接给 architecture-proposal.json) | `../copilot-agent/RequirementAnalyst.md` |
| **Phase 1** 领域 | Domain Knowledge Expert | 概念答疑由人工承担 | `../copilot-agent/DomainKnowledgeExpert.md` |
| **Phase 2** 架构 | Modeling Architect | 范式 / 类继承 / Frame 拓扑由人工承担 | `../copilot-agent/ModelingArchitect.md` |
| **C4** 对象清单 | Object & Method Designer | object-method-table 由人工承担(Modeling Architect 兼任) | `../copilot-agent/ObjectMethodDesigner.md` |
| **D6** 落盘 | Model Builder / Executor | **生成的 `.st` 不能自动写进 PS**——需 user 手动复制粘贴或后续 D6 阶段补 | `../copilot-agent/Executor.md` |
| **E7** 验证 | Validator | **生成的代码无法自动跑编译检查 / Init 烟测 / KPI 对照**——需人工目检 | `../copilot-agent/Validator.md` |
| **E8** 调试 | Debugger | 编译错 / silent fail 需 user 人工诊断 | `../copilot-agent/Debugger.md` |
| **F9** 文档 | Documentation Generator | 无架构图 / user guide / KPI dashboard | `../copilot-agent/DocumentationGenerator.md` |
| **F10** 沉淀 | Memory Curator | 无模板沉淀,同主题需求每次从零设计 | `../copilot-agent/MemoryCurator.md` |

**注意区分两个 "ModelBuilder"**:
- **`MVP ModelBuilder`(Phase 3,本目录,`./ModelBuilder.md`)**——骨架构建者,只建类/对象/属性/Interface/空 Method 占位,**绝不填方法体**;
- **`D6 Model Builder / Executor`(Phase 5+,`../copilot-agent/Executor.md`)**——端到端执行者,把 `.st` 写进 PS 占位 + 跑仿真 + readback。这是 MVP **未覆盖**的最后一步。

---

## 9. 与 `copilot-agent/` 全集的关系

| 目录 | 定位 | 范围 | 状态 |
|---|---|---|---|
| [`../copilot-agent/`](../copilot-agent/README.md) | **13 agent 全集蓝图**——职责 / 分工 / 边界 / 数据流 / 路线图 | 7 层 / 13 agent | 全部完成 |
| **`copilot-agent-mvp/`**(本目录) | **2 agent MVP 最小切片**——只覆盖"创建对象 + 写代码" | 1 层 / 2 agent | **全部完成** |

**MVP 与全集的取舍**:
- **删**:Orchestrator / RequirementAnalyst / DomainExpert / ModelingArchitect / ObjectMethodDesigner / Validator / Debugger / DocGen / Curator / Executor(后 5 个不全集内已有,但 MVP 不引用);
- **保留 + 强化**:ModelBuilder + SimTalkCodeGenerator——这是 MVP 的两个核心。

---

## 10. 一句话总览

> **Plant Simulation 自动建模 copilot MVP = 2 个核心 agent**:
> **`ModelBuilder`(在 PS 里建骨架)** + **`SimTalkCodeGenerator`(生成 SimTalk 源码)**。
> 输入:`architecture-proposal.json` + `object-method-table.md`(人工 / 外部提供)。
> 输出:`model-skeleton-report.md` + `simtalk-source/<object>.<method>.st` + `INDEX.md`。
> 7 个 skill 子集(启动 + 3 写 + 3 只读),3 区 KB(K1 / K2 / D 区 Quirk)。
> **架构 / 骨架 / 代码生成严格分层**——骨架构建者不填方法体,代码生成者只产纯文本,绝不调桥接。
> Quirk 处理提前到生成层(7 类 SimTalk Quirk 必在 `.st` 头部标注)。
> **MVP 不含端到端 `.st` 写进 PS / 不含 KPI 验证 / 不含经验沉淀**——后续 Phase 5+ 补 Executor/Validator/Curator 等。
