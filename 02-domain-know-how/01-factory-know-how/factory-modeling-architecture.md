---
last_updated: 2026-09-01
contributors: [@plant-simulation-expert]
scope: Plant Simulation 工厂建模的架构模式(Class Library / Models 二分法 + 模型即类库包 + Hardware/Software 分层)
---

# 工厂建模架构模式

本文档基于两个真实案例(Siemens Factory51 + P4_CTU)提炼出 **Plant Simulation 工厂建模的可复用架构模式**。

## 一、Class Library / Models 二分法(Factory51 教科书做法)

### 1.1 标准目录结构

```
Factory51.psfm/
├── UserObjects/              ← Class Library(类定义)
│   ├── Production/           ← Frame 类,内含 ~ 120 子对象
│   ├── Painting/
│   ├── PolishingCell/
│   ├── PostProcess/
│   ├── Drying/
│   ├── Warehouse/
│   └── MUs/                  ← Box/Pallet/AGV/Forklift/Truck
├── ApplicationObjects/       ← 第三方库类(HBW3D、CranesAndMore)
├── MaterialFlow/             ← 标准库基础类
├── Resources/                ← WorkerPool/Workplace/AGVPool
├── InformationFlow/          ← Method/Variable/DataTable
├── MUs/                      ← Container/Part/Transporter
├── UserInterface/            ← Button/Chart/Display/Dialog
└── Models/
    └── Factory51/            ← 模型实例
        ├── P1, P2            ← Production 类实例
        ├── Warehouse
        └── Source/StoreEntry/MultiPortalCrane/Track
```

### 1.2 职责分层

| 层 | 职责 | 复用方式 |
|---|---|---|
| `UserObjects/` | 业务类定义 | 跨模型/跨实例复用 |
| `ApplicationObjects/` | 第三方库类 | 跨模型复用 |
| 标准库基础类 | MaterialFlow/Resources/InformationFlow/MUs/UserInterface | 跨模型复用 |
| `Models/` | 当前模型的具体实例 | 当前模型独占 |

### 1.3 "一条线定义、两条线实例化"

```
Production(UserObjects/Production,自定义 Frame 类)
  ├── P1(Models/Factory51/P1,isInstance)
  └── P2(Models/Factory51/P2,isInstance,结构与 P1 完全一致)
```

- Production 类内含全部 11 个工序子 Frame + ~ 90 个对象(Line/Converter/Station/Workplace/WorkerPool 等)
- P1/P2 通过 `Origin` 指向 Production 的 UUID,继承全部结构
- P2 与 P1 同构,没有任何 override——完全相同的副本

**对 agent 的杠杆**:外部指令"把 P2 的所有 Workplace 都加上 pause=true"时,可以直接 `for p in [P1, P2] { ... }` 用同一段逻辑遍历,而不必针对 P1/P2 各写一份代码。

## 二、模型即类库包(P4_CTU 模式)

### 2.1 反直觉的核心

`.P4_CTU` 这个节点:
- `InternalClassType = "Folder"`
- `Origin = VOID`,`Class = VOID`

它**不是 Frame 实例**,而是 **Class Library 里的一个 Folder(用户自定义类库)**。

里面所有东西都是**类定义**,用户实际跑仿真时,要 `duplicate(.P4_CTU.ctux1_agvx1, .Models.Model)` 把模板拖进运行视图,才能产生实例。

### 2.2 完整结构

```
.P4_CTU                                  ← 用户自定义类库文件夹
├── ctux1_agvx1, ctux1_agvx2             ← 模板 Frame 类(变体)
├── BasicObjects/                        ← 类库副本
│   └── PartA, PartB, Box, MyFrame       ← 用户自定义 MU 类
├── AdvancedObject/
│   ├── Hardware/                        ← 硬件类
│   │   ├── AGV        (Transporter)
│   │   ├── AGVPool    (AGVPool)
│   │   ├── Rack       (Frame 类,含 v_x/v_y/bin_l/bin_w/...)
│   │   ├── CTU        (Folder)
│   │   │   ├── CTU        (Transporter)
│   │   │   ├── Lifttable  (Container)
│   │   │   └── Carrier, Carrier_Box
│   │   └── Store
│   └── Software/                        ← 软件/控制类
│       ├── RCS                       (Frame 类 — Rack Control System)
│       ├── MapGenerator              (Frame 类)
│       └── ...
```

### 2.3 BasicObjects 自包含副本

```
.P4_CTU.BasicObjects.MaterialFlow.Station   ← duplicate 自 .MaterialFlow.Station
.P4_CTU.BasicObjects.MUs.Transporter        ← duplicate 自 .MUs.Transporter
.P4_CTU.BasicObjects.Resources.AGVPool      ← duplicate 自 .Resources.AGVPool
```

模型自己带了一份 Plant Simulation 内置类库的副本,**不依赖用户机器上的内置库版本/补丁**。

实测确认:`.P4_CTU.AdvancedObject.Hardware.AGV` 的 `Origin` 是 `.P4_CTU.BasicObjects.MUs.Transporter` 而不是 `.MUs.Transporter`——**继承链指向本地副本而非全局类库**。这就是"模型可移植"的精髓。

### 2.4 命名空间隔离

| 路径 | 归属 | 影响范围 |
|---|---|---|
| `.Models.Factory51.P1` 等 | Factory51 业务 | 仿真业务逻辑 |
| `.UserObjects.Production` 等 | Factory51 业务 | 业务类定义 |
| `.SimtalkClaude` / `.SimtalkClaude2` | 工具桥 | 仅 TCP 通信,**不影响仿真** |
| `.ApplicationObjects.HBW3D` 等 | 第三方库 | 业务类定义 |

把 SimtalkClaude 作为顶层 Folder 隔离,与 `UserObjects` 平级——这是干净的隔离姿势。如果塞进 `UserObjects/`,业务 Frame 继承 `Production` 时会顺带继承到 `.UserObjects.SimtalkClaude.*`,污染业务命名空间。

## 三、Hardware/Software 分层(P4_CTU AdvancedObject 模式)

```
AdvancedObject/
├── Hardware/        ← 硬件类(物理设备)
│   ├── AGV         (Transporter)
│   ├── AGVPool     (AGVPool)
│   ├── Rack        (Frame 类)
│   ├── CTU/        (Folder,承装 CTU 设备的多种类)
│   └── Store       (Store)
└── Software/       ← 软件/控制类(调度逻辑)
    ├── RCS                  (Frame 类 — 控制中枢)
    ├── MapGenerator         (Frame 类)
    └── MapGenerator.*      (变体: Home / ChargingPlace / StockInLoader)
```

**核心原则**:物理设备(AGV/CTU/Rack)与控制中枢(RCS/MapGenerator)在物理路径上分离,但语义上耦合——通过 `m_Oncreate` / `m_OnMove` / `m_OnDelete` 生命周期 hook 自动注册到控制中枢。

## 四、可直接复用的架构步骤

要在新模型里"抄作业":

1. **建类库文件夹**:`.MyModel`(Folder,挂在 class library 根)
2. **BasicObjects 副本**:把需要的 .MaterialFlow.* / .Resources.* / .InformationFlow.* 拖进来
3. **Hardware 类**:在 `.MyModel.Hardware.*` 定义物理设备类(含 `_3d.dimensions` 等几何参数)
4. **Software 类**:在 `.MyModel.Software.*` 定义控制中枢(RCS 风格的 DataTable + executer)
5. **Hook 方法**:每个 Hardware 类挂 `m_Oncreate/m_OnMove/m_OnDelete` 自动注册
6. **模板 Frame**:`.MyModel.template_v1`(Frame 类)把 Hardware + Software + BasicObjects 包起来
7. **用户使用**:新模型只要 `duplicate(.MyModel.template_v1, .Models.Model)` 就有完整功能

## 五、不建议照搬的反模式

| 反模式 | 后果 | 改进建议 |
|---|---|---|
| 把 SimtalkClaude 塞进 `UserObjects/` | 业务 Frame 继承时污染命名空间 | SimtalkClaude 作为顶层 Folder,与 `UserObjects/` 平级 |
| Class Library 与 Models 混放 | 复用时无法分离定义与实例 | 严格按"类在 Class Library,实例在 Models"分离 |
| BasicObjects 不带 | 跨机部署时依赖全局库版本 | duplicate 内置类到 `.MyModel.BasicObjects.*` |
| Hardware 与 Software 混放在同一文件夹 | 物理与控制语义不清 | 按 `AdvancedObject.Hardware/Software` 分层 |
| 不挂 `m_Oncreate/OnDelete` hook | 用户得手动在 init 里 `for child in frame: rcs.add(child)` | 每个动态对象都挂自动注册 hook |

## 经验 Log

> 本节是 **append-only** 时间线——新发现直接追加在末尾。

<!-- 暂无 entry——首个 entry 由下次踩坑时 append -->