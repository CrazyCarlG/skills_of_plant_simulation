# MaterialFlow_AGV — Library Overview

> Plant Simulation 厂商类库 `MaterialFlow_AGV` 的学习与扩展笔记。
> 由 2026-08-31 plant-simulation-expert session 沉淀。

## 是什么

`MaterialFlow_AGV` 是 Plant Simulation 提供的**可选厂商类库**(vendored library),默认不随安装加载,需要从 Manage Class Library 显式加载。加载后会出现在 Class Library 根目录下,路径为 `.MaterialFlow_AGV`。

它的作用:为模型提供 **AGV 池 (AGVPool) + 路径点 (Marker) + 优化运输类 (PalletAGV/BoxAGV) + 容量计算工具 + 示例面积** 的开箱即用 AGV 系统建模能力。

## 顶层结构

```
.MaterialFlow_AGV/
├── BasicObjects/         (标准 MaterialFlow/InformationFlow/UserInterface/MUs 子集)
│   ├── Resources/        (Workplace, WorkerPool, Worker, Broker, Marker, ShiftCalendar, AGVPool, ...)
│   ├── MUs/              (Part, Container, Transporter)
│   ├── MaterialFlow/     (Connector, EventController, Source, Drain, ...)
│   ├── InformationFlow/  (Method, Variable, DataTable, Generator, SankeyDiagram, ...)
│   └── UserInterface/    (Button, Chart, Display, Dialog, ...)
├── AdvancedObejcts/      ⚠️ 厂商拼写错误,注意是 "Obejcts" 不是 "Objects"
│   ├── AGVPool           (Transporter-of-AGVPool)
│   ├── CapacityCalculation_v2  (Frame - 容量计算工具)
│   ├── Marker            (waypoint for AGV routes)
│   ├── OrderCreater      (Source 子类)
│   ├── PalletAGV         (Transporter 子类 - 托盘式 AGV)
│   └── BoxAGV            (Transporter 子类 - 箱式 AGV)
└── Area/                 (示例模型 - PhaseIV_Shopfloor, SmallArea, PhaseIV_SF, ...)
```

## 核心类能力速查

| 类 | 类型 | 继承自 | 关键方法 | 关键属性 |
|---|---|---|---|---|
| **AGVPool** | AGVPool | `.MaterialFlow_AGV.BasicObjects.Resources.AGVPool` | `getAssignedAGV(No)`, `getAssignedAGVsTable([tab])`, `getIdleAGV()` | `AGV` (path), `Amount` (int), `ShiftCalendarObject` |
| **Marker** | Marker | `.MaterialFlow_AGV.BasicObjects.Resources.Marker` | (随父类) | (随父类) |
| **PalletAGV** | Transporter | `.MaterialFlow_AGV.BasicObjects.MUs.Transporter` | `setRoute`, `setRouteSegments` (Transporter 默认) | `IsIdle`, `BatCharge`, `BatCapacity`, `Speed` |
| **BoxAGV** | Transporter | 同 PalletAGV | 同上 | 同上 |

## 已知限制 / 优化空间

vendor 提供的能力**仅够"能跑"**,不直接优化调度策略:

1. **`getIdleAGV()` 是 FIFO**:无距离、电量、负载、优先级考量,直接返回第一个 IsIdle=true 的 AGV。
2. **无 per-AGV 遥测**:vendor 只暴露 `StatAverageTraveledDistance`(全池均值),没有 jobsDone / 等待时间 / 电量事件。
3. **无充电策略**:vendor 只被动触发 `BatChargeCtrl` (e.g. `self.OnCharge`);无主动 `requestChargeIfLow` API。
4. **无批处理路由**:每次只能 `setRoute([...])` 一段路径;无 multi-stop tour 优化。
5. **无状态仪表板**:vendor 没有 `dashboard()` 一键查看所有池的实时状态。

→ 这些就是我们 `AGV_Claude` (同级 Class Library Folder,路径 `.AGV_Claude`) 要补齐的能力。

## 子文档

| 主题 | 文件 |
|---|---|
| 类层级与继承链详解 | [`class-structure.md`](./class-structure.md) |
| AGV_Claude 优化点对照表 | [`optimization-patterns.md`](./optimization-patterns.md) |
| 实现期踩到的 SimTalk 坑 | [`simulation-quirks.md`](./simulation-quirks.md) |

## 引用

- Plant Simulation Help: `AGVPool` (attributes / methods / read-only)
- 官方示例模型: `Factory51/Factory51.psfm` (P1/P2 各有完整 AGV+Track 网络)
- Plant Simulation 2606 step-by-step: `Modeling Transport Systems, AGVs, and Battery-powered Transporters`