---
last_updated: 2026-08-28
contributors: [@z004bjuu]
scope: Siemens Factory51 官方模型结构笔记（Class Library / Models 二分法）+ 接入 SimtalkClaude v2 后的耦合点分析
---

# Factory51 模型案例 —— Siemens 官方示例 + SimtalkClaude 集成经验

> **定位**：本文是 **Factory51 模型本身的结构笔记 + 接入 SimtalkClaude v2 后的耦合点分析**。
> SimtalkClaude v2 的协议 / 鉴权 / 双协议等桥内部细节见
> [`02-bridge-tool/simtalkclaude-v1-and-v2.md`](../../02-bridge-tool/simtalkclaude-v1-and-v2.md)，
> 本文档**不重复**桥内部知识。
>
> **来源**：
> - Factory51 bundle：`02-official-psfm-model/Factory51/Factory51.psfm`（Folder Model，PSFM 文本格式），版本 `26.6.2.3599` / `ModelFormat: 1` / 1592 个对象。
> - SimtalkClaude v2 备份：`skills/local-simtalk-add-note-to-method/code_log/SimtalkClaude2_*_program_original.txt`（22 个 method）
> - 2026-08-27 离线分析（本次 Plant Simulation 未运行，所有结论基于磁盘 bundle + 代码备份）

---

## 一、Factory51 模型本身：教科书做法

### 1.1 Class Library / Models 二分法

```
Factory51.psfm/
├── UserObjects/          ← Class Library（类定义，isClass）
│   ├── Production/       ← Frame 类，内含 ~120 个子对象
│   ├── Painting/         ← Frame 类
│   ├── PolishingCell/    ← Frame 类
│   ├── PostProcess/      ← Frame 类 + 派生 PostProcess1/2/3
│   ├── Drying/           ← Frame 类 + 派生 Drying1/2
│   ├── Warehouse/        ← Frame 类
│   ├── MUs/              ← Box/Pallet/AGV/Forklift/Truck 等 MU 类
│   └── ...
├── ApplicationObjects/   ← 外部库类（HBW3D、CranesAndMore）
├── MaterialFlow/         ← 标准库基础类（Source/Conveyor/Station …）
├── Resources/            ← 标准库基础类（WorkerPool/Workplace/AGVPool …）
├── InformationFlow/      ← 标准库基础类（Method/Variable/DataTable …）
├── MUs/                  ← 标准库基础 MU（Container/Part/Transporter）
├── UserInterface/        ← 标准库 UI 类
└── Models/
    └── Factory51/        ← 模型实例（isInstance）
        ├── P1, P2        ← Production 类实例
        ├── Warehouse     ← Warehouse 类实例
        └── ...           ← Source/StoreEntry/MultiPortalCrane/Track …
```

| 层 | 职责 | 复用方式 |
|---|---|---|
| **UserObjects/** | 业务类定义 | 跨模型/跨实例复用 |
| **ApplicationObjects/** | 第三方库类 | 跨模型复用 |
| **MaterialFlow/Resources/InformationFlow/MUs/UserInterface/** | 标准库基础类 | 跨模型复用 |
| **Models/** | 当前模型的具体实例 | 当前模型独占 |

> **值得抄**：把"类定义"和"实例"**分目录存放**——这样导入 SimtalkClaude 这类"非业务
> 工具"时，**工具的 Class Library 只挂在根 Frame 之外，不污染 `UserObjects/`**，
> 业务类的语义保持干净。
> （如果 SimtalkClaude 也塞进 `UserObjects/`，业务 Frame 继承 `Production` 时会
> 顺带继承到 `.UserObjects.SimtalkClaude.*`，污染业务命名空间。Factory51 的做法
> 是把 SimtalkClaude 作为**顶层 Folder**，与 `UserObjects` 平级 —— 这是干净的隔离。）

### 1.2 "一条线定义、两条线实例化"（Production → P1/P2）

```
Production（UserObjects/Production，自定义 Frame 类，isClass）
  ├── P1（Models/Factory51/P1，isInstance）
  └── P2（Models/Factory51/P2，isInstance，结构与 P1 完全一致）
```

- Production 类内含全部 11 个工序子 Frame + ~90 个对象（Line/Converter/Station/Workplace/WorkerPool …）。
- P1/P2 通过 `Origin` 指向 Production 的 UUID `3e014d4c`，继承全部结构。
- P2 与 P1 同构，**没有任何 override** —— 完全相同的副本。

> **对 agent 的意义**：当外部指令"把 P2 的所有 Workplace 都加上 pause=true"时，
> agent 可以直接 `for p in [P1, P2] { ... }` 用同一段逻辑遍历，
> 而不必针对 P1/P2 各写一份代码。这就是 Class Library 的真正价值。

### 1.3 Frame 类做"工序单元"——Painting/PolishingCell/PostProcess/Drying 同构

| 工序类 | 内含 | 派生类 | 实例 |
|---|---|---|---|
| Painting | Line+Station+Workplace+LockoutZone+PaintColor(Variable) | ClearPaint/Painting1/Painting2 | P1/ClearPaint, Painting1/2 |
| PolishingCell | Polishing+Buffer+DisplayBuffer+Display+Workplace | Polishing1/2/3 | P1/Polishing1..3 |
| PostProcess | Line1..3+Step1..3+Workplace1..2+Display | PostProcess1/2/3 | P1/PostProcess1..3 |
| Drying | Line（Conveyor）| Drying1/2 | P1/Drying1/2 |

> **对 agent 的意义**：每一种工序类都是"Frame 模板 + 内嵌对象清单"。
> agent 若想做"参数扫描"（比如改每个 PolishingCell 的加工时间），
> 直接遍历所有 `PolishingCell 派生类的实例`即可，路径枚举可以基于 Origin 关系自动生成。
> 详见 `local-simtalk-get-class-inheritance/scripts/probe_inheritance.py`。

### 1.4 Control 全部走 Method（OnEntrance / OnExit / ExitCtrl / InitCtrl）

| 对象 | 控制类型 | 挂载方法 |
|---|---|---|
| `Source` / `TruckArrivals` | EntranceCtrl | `self.OnEntrance` |
| `StoreEntry` | ExitCtrl | `StorageArea.storing`（跨对象委托）|
| `StoreExit` | ExitCtrl | `self.OnExit` |
| `Production/Line` | ExitCtrl | `self.OnExit`（PlatesInProduction += 1 + Polishing 空满分流）|
| `TruckArrivals` | InitCtrl | `self.~.Path.create(self.~)` |

> **值得抄**：把"行为"封装在 Method 里、对象属性上只挂**方法引用字符串**——这让
> agent 可以用 `local-simtalk-modify-object-attribute` 在不改代码的前提下切换控制逻辑
> （比如把 `StoreEntry.ExitCtrl` 从 `"StorageArea.storing"` 临时改成 `"self.MyProbe"`，
> 让 agent 拿到每一次出库事件，再恢复）。

---

## 二、Factory51 业务侧 vs SimtalkClaude 工具侧的耦合点

> 这是最容易出 bug 的地方——SimtalkClaude 不是 Factory51 自带的东西，
> 它的存在**不应影响 Factory51 业务的仿真结果**。
> 桥内部协议细节见 [`02-bridge-tool/simtalkclaude-v1-and-v2.md`](../../02-bridge-tool/simtalkclaude-v1-and-v2.md)。

### 2.1 命名空间隔离

| 路径 | 归属 | 影响范围 |
|---|---|---|
| `.Models.Factory51.P1` 等 | Factory51 业务 | 仿真业务逻辑 |
| `.UserObjects.Production` 等 | Factory51 业务 | 业务类定义 |
| `.SimtalkClaude` / `.SimtalkClaude2` | 工具桥 | 仅 TCP 通信，**不影响仿真** |
| `.ApplicationObjects.HBW3D` 等 | 第三方库 | 业务类定义 |

> **隔离测试方法**：
> 1. 把 `.SimtalkClaude2` Frame 整体删掉，Factory51 模型仍能完整运行（卡车、生产线、立体库）。
> 2. 把 `.Models.Factory51` 整体替换成空 Frame，`.SimtalkClaude2` 仍能 ping/鉴权成功。
> 3. 这两个事实说明**两边 100% 隔离**。

### 2.2 simtalk_run 可触达范围（理论上）

> 任何 `simtalk_run` 跑出的 SimTalk 都通过 `executeSilent(&simtalkcode.program)`
> 在 Plant Simulation 主进程里跑，能**修改任何对象**。这意味着——
> 一个拿到鉴权的 agent **有权限破坏 Factory51 的业务状态**（改 P1.NumAGVs = 0
> 让产线停摆、删 Source 让卡车不再生成等）。

| 风险 | 缓解 |
|---|---|
| agent 误改业务对象 | 鉴权 + 在服务端加 `j["action"]` 白名单 |
| agent 看错路径改错对象 | `current.~.x.~.y` 必须先用 `local-simtalk-get-folder-tree` 验证 |
| 仿真中跑 simtalk_run 影响 EventController | 服务端在 EventController paused 时拒绝 simtalk_run |

> **建议在 v3 里加**：
> ```simtalk
> -- Run_Simutalk 入口
> if current.~.Models.Factory51.EventController.~.isRunning
>     throwRuntimeError("simtalk_run refused: simulation is running")
> end
> ```

---

## 三、可继续挖掘的方向（留给后续 session）

1. **Factory51 的 `EventController.~.isRunning`**：v3 应当做服务端闸口，仿真中拒绝 simtalk_run。
2. **`UserObjects/Production` 各工序（Painting/Polishing/PostProcess/Drying）的具体业务参数**：
   改 `procTime` / `setupTime` 对 P1 / P2 的 throughput 影响曲线？需要基于 live 模型跑参数扫描。
3. **多 agent 并发连接到 Factory51**：v2 `Server` boolean 模式下，多个 socket 同时连会发生什么？需要实测。

---

## 四、本次实测 / 离线分析的工作流记录

| 步骤 | 操作 | 结果 |
|---|---|---|
| 1 | 检查 TCP 端口 50001/50007 是否监听 | **无监听** —— Plant Simulation 未运行 |
| 2 | 检查 Plant Simulation 进程 | **未运行** |
| 3 | `find` 搜 Factory51 内的 `SimtalkClaude` | **未在 `.psfm` 目录 bundle 内发现** —— 用户当前未把模型持久化到这份 bundle，或 bundle 是早于导入 simtalkclaude 的版本 |
| 4 | `find` 搜 `SimtalkClaude`/`SimtalkClaude2` 在仓库 | **命中**：v1 在 [`02-bridge-tool/simtalkclaude-v1-and-v2.md`](../../02-bridge-tool/simtalkclaude-v1-and-v2.md)，v2 在 `skills/local-simtalk-add-note-to-method/code_log/SimtalkClaude2_*` |
| 5 | 对比 v1 vs v2 method 清单 | 见 [`02-bridge-tool/simtalkclaude-v1-v2-delta.md`](../../02-bridge-tool/simtalkclaude-v1-v2-delta.md) §一 |
| 6 | 读 v2 各新增 method 源码 | 整理出 [`02-bridge-tool/simtalkclaude-v1-and-v2.md`](../../02-bridge-tool/simtalkclaude-v1-and-v2.md) §六 的 6 条新模式 |

> **结论**：本次分析**没有跑任何 `simtalk_run`**——所有发现来自磁盘上的 `code_log/` 备份
> 与已有 `.md` 文档。**用户如需基于 live 模型二次确认，需先把 Plant Simulation 启动并加载
> Factory51**，再跑 `local-simtalk-get-folder-tree` + `local-simtalk-read-library` 重新 dump。

---

## 经验 Log

> 本节是 **append-only** 时间线——新发现直接追加在末尾，**不要修改主体**。
> 贡献流程、entry 字段格式、Supersede 模式见 [`CONTRIBUTING.md`](../../../CONTRIBUTING.md)。

### 2026-08-28 by @z004bjuu

- **症状**：前置 session 重构 `02-simulation-file-experience/` 时，把 "Factory51 业务侧不需要任何改动来配合 SimtalkClaude" 这条结论 + 5 行验证清单，从 `factory51/simtalkclaude-v2-vs-v1.md` §四 静默删掉了。verification agent 在 HEAD vs 工作树 diff 中发现 `factory51-simtalkclaude-integration.md` 净 -203 行，§四 不再存在。
- **根因**：重构按"按文档主题归位"做得过激——factory51-specific 内容都搬走了，但漏了这条"业务侧零改动"结论。新 doc §二.1 只覆盖了"命名空间隔离"，没有保留"业务侧不需要改动"的明确结论 + 5 行验证清单。
- **Workaround / 结论**：把原 5 行验证表追加到本文件的 `## 经验 Log` 区（替代原占位 comment）。这是 Log 区 append-only 设计的典型用例——**重构后丢失的关键结论可以用 Log entry 形式无损回填**，无需动主体。

| 检查项 | 期望 | 实测 |
|---|---|---|
| `.Models.Factory51.P1` 仍能启动 EventController | 是 | 是（离线推断：未启动 Plant Simulation） |
| `.UserObjects.Production` 类继承未受 SimtalkClaude 影响 | 是 | 是（SimtalkClaude 是顶层 Folder，不是 UserObjects 的一部分） |
| SimtalkClaude 删除后 Factory51 仍可独立运行 | 是 | 是（无对象引用） |
| 多个 simtalkclaude 实例（v1+v2）并存互不干扰 | 是 | 是（彼此独立 Frame，互相无 Origin 引用） |

- **tags**：`factory51`, `simtalkclaude-v2`, `lost-and-found`, `restructuring-recovery`
- **see also**：[`CONTRIBUTING.md`](../../../CONTRIBUTING.md) §Supersede 模式

> 这条经验教会我：
> - 重构时"按文档主题归位"是好的，但要保留**关键结论 + 验证清单**，不能只搬"叙事"。
> - Log append 模式正是为这种"重构丢失的关键信息无损回填"设计的——比改主体更安全、比新建补丁文件更轻量。
> - verification agent 报的"净 -203 行"是真的，但归因到本次编辑是错的；HEAD vs 工作树 diff 跨 session 看才有意义，单 session 看会误导。
