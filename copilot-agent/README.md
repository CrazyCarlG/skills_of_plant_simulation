---
name: plant-simulation-copilot-agents
description: Plant Simulation 自动建模 copilot 的 **agent 全集文档**——13 个 agent 的职责分工、跨 agent 数据流、关键分层纪律、知识库依赖、与 `copilot-agent-mvp/` 子目录的关系。Phase 0 入口 + 总览。
type: agent-spec
owner: Yang Yang
last_updated: 2026-09-15
status: draft
---

# Plant Simulation 自动建模 Copilot — Agent 总览

> **目标**:把"用户提一个仿真需求"到"产出可跑的 `.spp` 模型 + KPI 验证 + 经验沉淀"
> 这条链路,**全流程 agent 化**——13 个 agent 分 7 层编排,每层只做一件事,层间靠
> **结构化 artifact**(JSON / Markdown / SimTalk 源码)交接,不靠自然语言。
>
> **核心承诺**:**架构 / 执行 / 验证三层互相隔离**——架构师不能调桥接,
> 执行者不能改架构,验证者独立——避免"自己测自己"的 silent fail。

---

## 1. 目录

- [1. 目录](#1-目录)
- [2. 与 `copilot-agent-mvp/` 的关系](#2-与-copilot-agent-mvp-的关系)
- [3. Agent 全集(13 个,7 层)](#3-agent-全集13-个7-层)
- [4. 跨 Agent 数据流图](#4-跨-agent-数据流图)
- [5. 关键分层纪律(展开)](#5-关键分层纪律展开)
- [6. 知识库依赖(K / D / E 三区)](#6-知识库依赖k--d--e-三区)
- [7. 桥接与外部系统](#7-桥接与外部系统)
- [8. Quirk 处理纪律](#8-quirk-处理纪律)
- [9. 沉淀路径(Memory Curator)](#9-沉淀路径memory-curator)
- [10. 与"普通代码 copilot"的差异](#10-与普通代码-copilot-的差异)
- [11. 触发与运行模式](#11-触发与运行模式)
- [12. 未完成 agent 与下一阶段](#12-未完成-agent-与下一阶段)
- [13. 一句话总览](#13-一句话总览)

---

## 2. 与 `copilot-agent-mvp/` 的关系

仓库内有两套 agent 文档目录:

| 目录 | 定位 | 状态 | 用途 |
|---|---|---|---|
| **`copilot-agent/`**(本目录) | **完整 13 agent 蓝图**——职责 / 分工 / 边界 / 数据流 | 部分 agent 文档待补齐(`Orchestrator.md` / `Validator.md` / `Debugger.md` / `RequirementAnalyst.md` / `ObjectMethodDesigner.md` / `MemoryCurator.md` / `DocumentationGenerator.md`);**`ModelBuilder.md` 与 `SimTalkCodeGenerator.md` 已落地** | **规划 / 路线图**——回答"应该有谁、做什么、不做什么" |
| **`copilot-agent-mvp/`** | **MVP 已落地的 agent 子集**——文档完整可执行 | 全部完成(`Orchestrator` / `RequirementAnalyst` / `DomainKnowledgeExpert` / `ModelingArchitect` / `SimTalkCodeGenerator`) | **执行 / demo**——直接调 Agent 工具跑 |

**原则**:
- **本目录的 13 agent 是"全集路线图"**——MVP 子目录先实现优先 5 个(Phase 0–4 链路必需),其余 8 个逐步补齐。
- **MVP 子目录的 agent 文档更细**(含 Quirk 引用、KB 路径、KB anchors 等);**本目录的 agent 描述更抽象**(只到职责 + 边界)。
- **不要在本目录"抄一遍" MVP 内容**——本目录只画大图,MVP 目录给细节。

---

## 3. Agent 全集(13 个,7 层)

### A. 编排层 / Orchestration

| # | Agent | 文件 | 职责 | 输出 |
|---|---|---|---|---|
| **0** | **Orchestrator / Pipeline Controller** | [`Orchestrator.md`](./Orchestrator.md) | 串起 1–9,负责**阶段门**(Phase Gate)、失败回退、人工 confirm、session 注册 | `session-log.md` + 每阶段 artifact 路由 |

### B. 需求与领域层 / Requirement & Domain

| # | Agent | 文件 | 职责 | 输出 |
|---|---|---|---|---|
| **1** | **Requirement Analyst** | [`RequirementAnalyst.md`](./RequirementAnalyst.md) | 自然语言 / Excel / 工艺卡 / 图纸 → 结构化 spec(场景 / 实体 / 工序 / 资源 / KPI / 边界) | `requirement-spec.json` |
| **2** | **Domain Knowledge Agent** | [`DomainKnowledgeExpert.md`](./DomainKnowledgeExpert.md) | PS 对象库全集(MaterialFlow / Resources / InformationFlow / MUs / UserInterface 5 大类 + CranesAndMore / HBW3D 等)+ SimTalk 语言规范 + Quirk 行为 + 标准建模范式(Factory51 / Small Parts Production) | `domain-context.md` |

### C. 架构与设计层 / Architecture & Design

| # | Agent | 文件 | 职责 | 输出 |
|---|---|---|---|---|
| **3** | **Modeling Architect** | [`ModelingArchitect.md`](./ModelingArchitect.md) | 选建模范式 / 设计文件夹结构 / 设计类继承树 3 层 / 选标准对象组合 / 定义 Interface 边界 / 选 SimTalk 模式;**只输出架构,不建模型** | `architecture-proposal.json` |
| **4** | **Object & Method Designer** | [`ObjectMethodDesigner.md`](./ObjectMethodDesigner.md) | 把架构方案落地成对象清单(每个 Frame 里放什么 / 类型 / 参数初值)+ 方法清单(Init / Reset / 各 EntranceCtrl / 各 ExitCtrl / 业务方法) | `object-method-table.md`(对象-方法-参数三栏表) |
| **4b** | **Model Builder / Skeleton Builder** ⭐ | [`ModelBuilder.md`](./ModelBuilder.md) | **Phase 3 骨架落地**——消费 `architecture-proposal.json` + `object-method-table.md`,**经桥接在运行中的 PS 进程里建模型骨架**(5 大根 / Class 派生树 / Frame 树 / 对象实例 / 属性初值 / Interface 接线 / **空 Method 占位**);**绝不填方法体源码**(那是 #5 `SimTalkCodeGenerator` 的活);建完必 readback 全量验证 | `04-agent-memory/plant-simulation-model-builder-memory/YYYY-MM-DD_skeleton-report_<topic>.md` |

### D. 代码生成与执行层 / Code Generation & Execution

| # | Agent | 文件 | 职责 | 输出 |
|---|---|---|---|---|
| **5** | **SimTalk Code Generator** | [`SimTalkCodeGenerator.md`](./SimTalkCodeGenerator.md) | 按方法清单生成 SimTalk 源码;**内置 Quirk 处理**(str→num、`<-` 不可作表达式、stopuntil 拉式、Buffer 容量上限、`@.toStr` 链路、Method 引用 vs 直接调用、`$Failures` 分布函数选型);**输出严格符合 SimTalk 2.x 语法,不写伪代码,必须真能编译** | `simtalk-source/<object>.<method>.st` |
| **6** | **Model Builder / Executor** | [`ModelBuilder.md`](./ModelBuilder.md) | 真正写进 Plant Simulation——经 TCP / COM 桥(如 SimtalkClaude socket / OPC)操作 PS 进程;写完必 readback 验证(避免 silent fail);Create Frame / Create Class / Create Object / Set Property / Create Method / Write Method Source / Link Interface;**PS 二进制 `.spp` 不能手工编辑,只能经桥接** | `.spp` 模型 + 写日志 + readback 报告 |

### E. 验证与迭代层 / Verification & Iteration

| # | Agent | 文件 | 职责 | 输出 |
|---|---|---|---|---|
| **7** | **Validator / Verifier** | [`Validator.md`](./Validator.md) | 编译检查(SimTalk 语法)+ Init 烟测(`Source.createMU → Station → Drain.delete`)+ KPI 对照(throughput / WIP / utilization)+ 反模式检查(Station 挂 Method 但未触发 EntranceCtrl / Broker 未绑 / Worker 未注册);**输出 PASS / FAIL + 证据**(运行截图 / 日志 / 统计) | `validation-report.md`(PASS/FAIL + 证据链) |
| **8** | **Debugger / Refiner** | [`Debugger.md`](./Debugger.md) | 读 SimTalk 编译错 / 运行异常 / Quirk 警告;定位根因(对象选错 / 属性配错 / Init 链断 / Quirk 未规避);生成 patch + 回滚预案;回到 6 重写 → 7 复验直到 PASS | `debug-patch.md`(patch + 根因 + 回滚预案) |

### F. 沉淀与文档层 / Documentation & Memory

| # | Agent | 文件 | 职责 | 输出 |
|---|---|---|---|---|
| **9** | **Documentation Generator** | [`DocumentationGenerator.md`](./DocumentationGenerator.md) | 架构图(对象树 / 类继承树 / 数据流)+ user guide(怎么改参数 / 怎么跑实验)+ KPI dashboard 配置;**不写代码,只解释** | `architecture-diagrams/` + `user-guide.md` + `kpi-dashboard.json` |
| **10** | **Memory Curator / Pattern Reuser** | [`MemoryCurator.md`](./MemoryCurator.md) | 把每次自动建模的(需求 → 架构 → SimTalk pattern)沉成模板;未来同类需求(比如又是 "AGV + 立体仓库")直接套模板,跳过 1–4 步;**这是从"工具"到"产品"的关键 agent** | `04-agent-memory/<topic>.md` + 模板索引 |

### G. 横切支撑 / Cross-cutting(可选但强烈推荐)

| # | Agent | 文件 | 职责 | 输出 |
|---|---|---|---|---|
| **11** | **Code Reviewer** | (随 Validator / Code Generator 一起调) | 对生成的 SimTalk 做独立 review,挑 Quirk 风险 / API 误用 / 命名规范 | `code-review-report.md` |
| **12** | **Skill Optimizer** | (随 Model Builder 一起调) | 扫桥接 log,发现 silent fail / timeout / 选错 skill,持续优化执行器 | `skill-optimize-report.md` |
| **13** | **Domain Explainer** | [`DomainKnowledgeExpert.md`](./DomainKnowledgeExpert.md) | user 中途问"为什么用 Station 不用 ParallelStation / Buffer 容量上限是多少"时即时答——**consult 角色,跟执行严格隔离** | 即时答案 + KB 引用 |

---

## 4. 跨 Agent 数据流图

```
            ┌─────────────────────────────────────────────────────────┐
            │                  用户原始需求                            │
            │  (自然语言 / Excel / 工艺卡 / 图纸 / KPI 描述)            │
            └─────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                       ┌────────────────────┐
                       │  0. Orchestrator   │ ← 阶段门 / 失败回退 / 人工 confirm
                       └────────────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              ▼                   ▼                   ▼
       ┌──────────────┐    ┌──────────────┐    (其它入口)
       │ 1. Req Ana.  │    │ 2. Domain KB │ ← 并发读
       │ → require-   │    │ → domain-    │
       │   ment-      │    │   context.md │
       │   spec.json  │    │              │
       └──────────────┘    └──────────────┘
              │                   │
              └─────────┬─────────┘
                        ▼
              ┌──────────────────┐
              │ 3. Model Arch.   │ → architecture-proposal.json
              │  (范式/类继承/    │   (范式 + 文件夹 + 类继承树 + 对象组合 + Interface + SimTalk 模式)
              │   Frame 拓扑/    │
              │   SimTalk 模式)  │
              └──────────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │ 4. Obj&Method    │ → object-method-table.md
              │   Designer       │   (对象-方法-参数三栏表)
              └──────────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │ 4b. Model Builder│ ⭐ Phase 3 落地环节
              │   (Skeleton)     │ → PS 进程里建好的骨架
              │   ★ 已落地       │   (Class / Frame / Object / 属性 / Interface / 空 Method 占位)
              │                  │   + readback 报告
              │                  │   ⚠ 绝不填方法体(留给 #5)
              └──────────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │ 5. SimTalk       │ → simtalk-source/<obj>.<method>.st
              │   Code Generator │   (按方法清单 + Quirk 规避生成源码)
              └──────────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │ 6. Model Builder │ → .spp 模型 + 写日志 + readback 报告
              │   (TCP/COM 桥)   │   (经 SimtalkClaude socket / OPC)
              └──────────────────┘
                        │
                        ▼
              ┌──────────────────┐
              │ 7. Validator     │ → validation-report.md
              │   (编译 + 烟测 + │   (PASS / FAIL + 证据)
              │    KPI 对照)     │
              └──────────────────┘
                │ PASS                │ FAIL
                ▼                     ▼
              ┌──────────┐     ┌──────────────┐
              │ (完成)    │     │ 8. Debugger  │ → debug-patch.md
              └──────────┘     │  (根因 +     │
                               │   patch +    │
                               │   回滚预案)   │
                               └──────────────┘
                                        │ (回到 6 重写)
                                        ▼
                               ┌──────────────────┐
                               │ 6→7 循环 until   │
                               │ PASS             │
                               └──────────────────┘
                                        │
                                        ▼ (PASS)
                              ┌─────────────────┐
                              │ 9. Doc Gen +    │ → 架构图 + user guide + KPI dashboard
                              │ 10. Mem Curator │ → 模板沉淀到 04-agent-memory
                              └─────────────────┘
```

**关键流转节点**(每条线都是"结构化 artifact",不靠自然语言):
- `用户需求` → `requirement-spec.json`(B1)
- `requirement-spec.json + domain-context.md` → `architecture-proposal.json`(C3)
- `architecture-proposal.json` → `object-method-table.md`(C4)
- `architecture-proposal.json + object-method-table.md` → **PS 进程骨架 + skeleton-report**(C4b Model Builder,Phase 3 落地)⭐
- **PS 骨架 + skeleton-report 占位清单** → `simtalk-source/*.st`(D5 填方法体)
- `simtalk-source/*.st` → `.spp` + readback 报告(D6)
- `.spp + 烟测` → `validation-report.md`(E7)
- `validation-report.md` → `debug-patch.md`(E8, FAIL 时)
- `PASS 后` → `architecture-diagrams/ + user-guide.md + kpi-dashboard.json`(F9)
- `PASS 后` → `04-agent-memory/<topic>.md`(F10)

---

## 5. 关键分层纪律(展开)

### 5.1 三层隔离硬纪律

| 纪律 | 为什么 | 违反后果 | 谁负责 |
|---|---|---|---|
| **3(架构) ≠ 6(执行)**:架构师不能直接调桥 | 架构师一旦调桥,会被"已写了一半再改架构"锁死——再改架构就要重写已经写进 PS 的对象,代价指数级增长 | 架构与实现脱钩,后期重构成本暴涨 | Orchestrator 强制门禁 |
| **5(代码生成) ≠ 6(执行)**:代码生成是纯文本,执行是 PS 进程操作 | 写代码不知道 PS 进程反馈、桥接状态;执行不知道代码意图;**中间必须经过"代码静态 lint"(Quirk 检查器)再下发** | 编译错漏到 PS 进程触发 silent fail | Code Generator 负责 Quirk 自检 + 静态 lint 工具 |
| **7(验证)独立**:不能由 6 自己说"我跑了一下没崩就 OK" | PS 的 silent fail / Quirk 经常通过运行时才暴露;写代码的人自己测自己 = 漏一半 | KPI 假阳 / 关键路径 silent fail | Orchestrator 强制独立 session |
| **10(记忆)是 long-term 杠杆**:没有它,每次从零设计,copilot 永远是工具;有了它,copilot 才变成"越用越准"的领域 copilot | 单次模型价值有限,沉淀的模板让同类需求跳过 1–4 步 | 重复造轮子,边际成本不下降 | Memory Curator |

### 5.2 Agent 间"职责不越界"纪律

每个 agent 必须明确回答 3 个边界问题:
1. **我不做的**——下游 / 平行 agent 去做;
2. **我不调的工具**——执行类工具不调(对应 agent 调);
3. **我不写的文件**——其它 agent 的输出 / 知识库 / 配置文件。

**示例**(ModelingArchitect 的边界):
- 不调 `local-simtalk-*` 桥接 skill;
- 不写 `.spp` / `Method.program`;
- 不写 SimTalk 源码(那是 D5 的活)。

详细边界见各 agent 文件的"职责边界"段。

---

## 6. 知识库依赖(K / D / E 三区)

本 copilot 的所有"领域知识"决策都依赖仓库内 3 个**离线只读**目录:

| 区 | 路径 | 内容 | 谁主要读 |
|---|---|---|---|
| **K 区** | `01-plantsimulation-knowledge/` | Siemens 官方 Help(`01-plant-simulation-help/`)+ Factory51 / Small Parts Production 逆向文档(`02-offcial-psfm-model/`)+ PSFM 抽取提示词(`prompts/psfm/`)+ PDF→MD 转换脚本(`scripts/`) | 2 Domain KB / 3 Model Arch / 5 SimTalk Gen |
| **D 区** | `02-domain-know-how/` | 已沉淀主题知识(7 维:factory-know-how / simtalkclaude-knowhow / modeling-know-how / modeling-example / modeling-experience 等) | 2 Domain KB / 3 Model Arch / 5 SimTalk Gen |
| **E 区** | `03-modeling-experience/` | Memory Curator 沉淀的 per-entry 经验(per-topic .md,一个 finding 一文件) | 3 Model Arch 优先引用 |

**纪律**:
- **所有"领域知识"结论必须可追溯到 K/D/E 三区之一**——找不到的,显式说"知识库未覆盖",不编造。
- **D 区由 Knowledge Synthesizer 从 E 区合成**——D 区不是 Memory Curator 直接写。
- **E 区一个 topic 一个 .md 文件,绝不 append**——避免 diff 噪音。

---

## 7. 桥接与外部系统

### 7.1 PS 进程桥接

**两个 agent 允许调桥接**:
- **C4b `Model Builder`**——**只调"骨架构建"写 skill 子集**(`class-management` / `create-method-object` / `modify-object-attribute`)+ 启动 skill + 3 个只读 skill;**禁调** `write-simtalk` / `add-note-to-method`(那是 D5 的活);
- **D6 `Model Builder / Executor`**——端到端执行者,可调**全部写 skill**(`write-simtalk` / `add-note-to-method` / `class-management` / `create-method-object` / `modify-object-attribute`)+ 执行 skill + 启动 skill + 只读 skill。

| 通道 | Skill | 何时用 |
|---|---|---|
| **TCP Socket** | `local-simtalk-execution` / `local-simtalk-write-simtalk` / `local-simtalk-class-management` / `local-simtalk-create-method-object` / `local-simtalk-modify-object-attribute` / `local-simtalk-read-library` / `local-simtalk-get-folder-tree` / `local-simtalk-get-class-inheritance` 等 | 读 / 写 / 跑 SimTalk |
| **COM** | `local-window-com-start-plant-simulation`(只 Windows) | 启动 PS 进程 + 注入 SimtalkClaude.pslib + 配置端口 |
| **OPC**(可选) | (待补) | 实时数据采集 / 与外部系统集成 |

### 7.2 桥接 Quirk 严重度

桥接是高失败率环节——silent fail / timeout / Quirk 漂移频发:

| Quirk 类型 | 示例 | 谁负责 |
|---|---|---|
| **方法写不进去** | `local-simtalk-write-simtalk` 写完没 readback,以为成功 | D6 `Model Builder` 强制 readback |
| **chunked writer 缓冲溢出** | 大方法体一次性写触发 buffer ceiling | D6 拆分 chunk + 流式校验 |
| **BFS leak** | 调 `get-folder-tree(depth=N)` 递归触发 | D6 限制 depth=1 + 单次只读 |
| **encrypted-method** | 加密 Method 无法 read | D6 跳过 + 报警 |

**纪律**:**所有桥接调用必须经由 `local-simtalk-*` skill,绝不允许直接 TCP / COM / GUI 触发**——skill 自带 Quirk 编号、lifeline、buffer ceiling 处理。

### 7.3 外部系统边界

- **Excel / 工艺卡** 输入 → B1 Requirement Analyst(自然语言解析)
- **PLM / ERP** 数据(可选) → 暂未对接,后续可由 B1 增加输入适配
- **3D 场景可视化** → 输出端,user 在 PS GUI 看
- **KPI dashboard** → F9 Documentation Generator 输出配置,部署到 BI 工具

---

## 8. Quirk 处理纪律

**Quirk** = Plant Simulation / SimTalk / 桥接层的非显然行为,失败率高,且不会通过编译错暴露。

### 8.1 Quirk 三大类

| 类 | 描述 | 处理 agent |
|---|---|---|
| **SimTalk Quirk** | `str → num` 转换 / `<-` 不可作表达式 / `stopuntil` 拉式模式 / Buffer 容量上限 / `@.toStr` 链路 / Method 引用 vs 直接调用 | D5 SimTalk Code Generator(生成时规避) |
| **桥接 Quirk** | buffer ceiling / BFS leak / encrypted-method / silent fail | D6 Model Builder + G12 Skill Optimizer |
| **对象选型 Quirk** | Station 挂 Method 但未触发 EntranceCtrl / Broker 未绑 / Worker 未注册 / `WorkerPool.create` 未在 Init | E7 Validator 反模式检查 |

### 8.2 Quirk 沉淀路径

1. **发现 Quirk** → D5/D6/E7 在 artifact 里标 `Quirk #N` 或 `@G11 Code Reviewer 评审 Quirk #N`
2. **评审** → G11 Code Reviewer / G12 Skill Optimizer 评估
3. **入库** → 写入 `02-domain-know-how/03-modeling-know-how/02-simtalk/language-quirks-reference.md`(Quirk 编号协议)
4. **引用** → 后续 D5/D6/E7 遇到同名 Quirk,直接引用编号,不重新解释

---

## 9. 沉淀路径(Memory Curator)

`Memory Curator`(F10)是 copilot 的 long-term 杠杆,**唯一允许**写记忆文件的 agent。

### 9.1 沉淀什么

- **高频需求模板**(AGV + 立体仓库 / 装配线 + 工人协作 / 仓储 + 输送 / ...)
- **已验证 SimTalk pattern**(Factory51 Init 链 / Small Parts Production 子 Frame 自治 / 拉式 + WorkerPool / ...)
- **Quirk 编号**(见 §8)
- **反模式**(Init 链断 / Broker 未绑 / Worker 未注册 / ...)

### 9.2 沉淀到哪里

| 内容类型 | 目标路径 | 文件粒度 |
|---|---|---|
| 模板类 | `04-agent-memory/plant-simulation-expert-memory/<topic>.md` | 每 topic 一文件 |
| 经验类 | `03-modeling-experience/<dim>/<topic>.md` | 每 finding 一文件(不 append) |
| 主题合成长文 | `02-domain-know-how/<dim>/<topic>.md` | 由 Knowledge Synthesizer 从 E 区合成 |

### 9.3 怎么用沉淀

- **同主题新需求** → Orchestrator 命中模板,跳过 B1–C4 直接进 D5
- **Quirk 命中** → D5/D6/E7 引用编号,不重新解释
- **反模式命中** → E7 自动报警

---

## 10. 与"普通代码 copilot"的差异

| 维度 | 普通代码 copilot | Plant Simulation 自动建模 copilot |
|---|---|---|
| **输出形态** | 文本文件(`.py` / `.ts`) | **文本 + 二进制 + 桥接状态**(`.st` 源码 + `.spp` 模型 + PS 进程内存对象) |
| **执行验证** | pytest / npm test | **必须跑 PS 实例 + 收 Stat / TimeSpan 真实数据**(KPI 实测) |
| **架构选型** | 框架选型 / 模块拆分 | **范式选型**(离散 / 连续 / 推 / 拉)+ **类继承树 3 层** |
| **Quirk 处理** | 语言 Quirk(常见) | **桥接 Quirk + SimTalk Quirk + 对象选型 Quirk**(silent fail 频发) |
| **用户交互** | 文件 diff | **3D 场景可视化 + KPI dashboard** + 文件 diff |
| **沉淀价值** | code snippet | **可复用建模模板**(整个 Init 链 + Frame 结构 + KPI 采样策略) |
| **失败模式** | 编译错 / 运行异常 | 编译错 / **silent fail** / KPI 假阳 / Quirk 漂移 |
| **依赖深度** | 语言运行时 | 语言运行时 + **PS 进程状态 + 桥接 socket + K/D/E 三区知识库** |

---

## 11. 触发与运行模式

### 11.1 触发入口

| 入口 | 描述 | 路由 |
|---|---|---|
| **用户自然语言需求** | "我想做一个 AGV 仓储模型" | Orchestrator → B1 |
| **用户给 Excel / 工艺卡** | (待 B1 完善适配) | B1 |
| **用户问领域知识** | "为什么用 Station 不用 ParallelStation" | G13 Domain Explainer(直接答,不进 pipeline) |
| **用户给已存在模型** | "现有模型 Y 重构" | Orchestrator → C3(架构师先看现状) |
| **Memory Curator 命中模板** | "又有 AGV + 立体仓库需求" | Orchestrator 直接进 D5(跳过 B1–C4) |

### 11.2 运行模式

| 模式 | 描述 | 何时用 |
|---|---|---|
| **完整流水线** | B1 → C3 → C4 → D5 → D6 → E7 → (E8 if FAIL) → F9/F10 | 新需求 / 重构 |
| **快速复用** | Memory Curator 命中模板 → D5 → D6 → E7 | 同主题新需求 |
| **单点诊断** | E7 / E8 / G13(独立调用) | "跑不起来"、"为什么慢"、"这个 API 怎么用" |
| **只读探查** | D6 只读 skill + G13 Domain Explainer | "现有模型长什么样" |

### 11.3 阶段门(Phase Gate)

Orchestrator 在每个阶段门强制检查:
- **B → C 门**:`requirement-spec.json` 是否齐全(场景 / 实体 / 工序 / 资源 / KPI / 边界)?不齐 → 回流 B1
- **C → D 门**:`architecture-proposal.json` + `object-method-table.md` 是否齐全(对象路径 / 方法签名 / 触发时机 / 关键参数)?不齐 → 回流 C3/C4
- **D → E 门**:D6 readback 报告是否全 PASS?否则 → 回 D5 重生成
- **E → F 门**:E7 validation-report 是否 PASS?否则 → 进 E8(回到 D6 重写)
- **E → 沉淀 门**:E7 PASS 后才进 F9/F10

---

## 12. 未完成 agent 与下一阶段

### 12.1 当前已落地(MVP 子目录对应)

- ✅ **0 Orchestrator**(`copilot-agent-mvp/Orchestrator.md`)
- ✅ **1 Requirement Analyst**(`copilot-agent-mvp/RequirementAnalyst.md`)
- ✅ **2 Domain Knowledge Expert**(`copilot-agent-mvp/DomainKnowledgeExpert.md`)
- ✅ **3 Modeling Architect**(`copilot-agent-mvp/ModelingArchitect.md` + 本目录 `ModelingArchitect.md`)
- ✅ **4b Model Builder / Skeleton Builder**(`copilot-agent/ModelBuilder.md`)⭐——**新落地**,Phase 3 骨架构建者,介于 C4 与 D5 之间
- ✅ **5 SimTalk Code Generator**(`copilot-agent-mvp/SimTalkCodeGenerator.md`)

### 12.2 当前未完成(本目录 `.md` 为空)

- ⏳ **4 Object & Method Designer**(`ObjectMethodDesigner.md`)——C3 与 D5 中间的"对象-方法-参数三栏表"落地环节(目前由 #3 兼任)
- ⏳ **6 Model Builder / Executor**(`ModelBuilder.md` 文档待拆,详见 §12.4)——端到端执行者(写 `.st` 到 PS + 跑仿真);**注意**:本目录下 `ModelBuilder.md` 已被重新定义为 **#4b Skeleton Builder(Phase 3 骨架构建者)**;Phase 5+ 的 **#6 Model Builder / Executor**(端到端写源码 / 跑仿真)需要另起一份
- ⏳ **7 Validator**(`Validator.md`)——编译 + 烟测 + KPI 对照
- ⏳ **8 Debugger**(`Debugger.md`)——根因诊断 + patch
- ⏳ **9 Documentation Generator**(`DocumentationGenerator.md`)
- ⏳ **10 Memory Curator**(`MemoryCurator.md`)
- ⏳ **G11 Code Reviewer**(作为 D5 / E7 的子环节)
- ⏳ **G12 Skill Optimizer**(作为 D6 的子环节)

### 12.3 下一阶段路线图

| Phase | 目标 | 涉及 agent |
|---|---|---|
| **Phase 0–2(MVP 旧版)** | B1 → C3 → D5(纯文本链路) | ✅ 已完成 |
| **Phase 3(新)** ⭐ | **C4b Skeleton Builder 骨架落地** | ✅ **#4b Model Builder 已落地** |
| **Phase 4(MVP 旧版)** | D5 SimTalk 代码生成 | ✅ 已完成 |
| **Phase 5** | D6 桥接执行(`.st` 写进 PS + 跑仿真) | 6 Model Builder / Executor(待落地) |
| **Phase 6** | E7 验证 + E8 Debugger 闭环 | 7 Validator + 8 Debugger |
| **Phase 7** | F9 文档化 + F10 沉淀 | 9 Doc Gen + 10 Mem Curator |
| **Phase 8** | G11/G12 持续治理 | 11 Code Reviewer + 12 Skill Optimizer |
| **Phase 9** | 跨模型迁移 / 多用户协作 / 版本管理(待定) | 增量 |

### 12.4 关于 `ModelBuilder.md` 的命名与拆分说明

当前 `copilot-agent/ModelBuilder.md` 已被定义为 **#4b Skeleton Builder(Phase 3)**——介于 C4 ObjectMethodDesigner 与 D5 SimTalkCodeGenerator 之间的骨架落地环节。命名沿用 "ModelBuilder" 但**与全集 #6 "Model Builder / Executor"(端到端执行者)是两个不同角色**:

| 维度 | #4b Skeleton Builder(已落地) | #6 Model Builder / Executor(待落地) |
|---|---|---|
| **Phase** | Phase 3 | Phase 5 |
| **职责** | 建模型骨架(类/对象/属性/Interface/空 Method 占位) | 把 `.st` 源码写入 PS 占位 + 跑仿真 + readback |
| **调 `write-simtalk`** | ❌ 禁调(D5 独占) | ✅ 调 |
| **调 `add-note-to-method`** | ❌ 禁调(D5 独占) | ✅ 调 |
| **执行仿真** | ❌ 不跑 | ✅ 跑 |

未来 Phase 5 落地 #6 时,可:
- **方案 A**:把 `ModelBuilder.md` 改名为 `SkeletonBuilder.md`,新建 `Executor.md`;
- **方案 B**:在现有 `ModelBuilder.md` 顶部加 "本 agent = #4b Skeleton;Phase 5+ Executor = #6 见 `Executor.md`"。

---

## 13. 一句话总览

> **Plant Simulation 自动建模 copilot = 13 agent 分 7 层编排**;
> 每层只做一件事,层间靠结构化 artifact(JSON / Markdown / `.st`)交接;
> **架构 / 骨架 / 代码生成 / 执行 / 验证多层互相隔离**——架构师不调桥,骨架构建者不填方法体,代码生成者不落盘,执行者不能改架构,验证者独立;
> 知识库 K/D/E 三区是所有决策的源头,**找不到的不编造**;
> Quirk 三大类(SimTalk / 桥接 / 对象选型)走"发现 → 评审 → 入库 → 引用"四段式;
> Memory Curator 是 long-term 杠杆——沉淀的模板让 copilot "越用越准";
> MVP 子目录(`copilot-agent-mvp/`)已落地 5 个 agent(Phase 0–4 纯文本链路),**Phase 3 骨架构建(#4b Model Builder)** 在 `copilot-agent/` 已独立落地;
> 其余 7 个 agent(D6 / E7 / E8 / F9 / F10 / G11 / G12)按 Phase 5–8 路线图逐步补齐。
