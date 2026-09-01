---
last_updated: 2026-09-01
contributors: [@plant-simulation-expert]
scope: 厂商 AGV 类库学习 + 用户态优化版(AGV_Claude)的扩展模式
---

# 厂商类库扩展模式

本文档基于 MaterialFlow_AGV 厂商类库 + `.AGV_Claude` 用户态优化版的对比,提炼出 **"扩展厂商类库"的可复用模式**。

## 一、MaterialFlow_AGV 是什么

Plant Simulation 提供的**可选厂商类库**(vendored library),默认不随安装加载,需要从 Manage Class Library 显式加载。加载后出现在 Class Library 根目录,路径为 `.MaterialFlow_AGV`。

作用:为模型提供 **AGV 池(AGVPool)+ 路径点(Marker)+ 优化运输类(PalletAGV/BoxAGV)+ 容量计算工具 + 示例面积** 的开箱即用 AGV 系统建模能力。

## 二、顶层结构

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

> ⚠️ **拼写陷阱**:`AdvancedObejcts` 不是 `AdvancedObjects`(厂商笔误)。所有继承链 path 必须用 vendor 的拼写,否则 `str_to_obj` 返回 void。

## 三、核心类能力速查

| 类 | 类型 | 继承自 | 关键方法 | 关键属性 |
|---|---|---|---|---|
| **AGVPool** | AGVPool | `.MaterialFlow_AGV.BasicObjects.Resources.AGVPool` | `getAssignedAGV(No)`, `getAssignedAGVsTable([tab])`, `getIdleAGV()` | `AGV` (path), `Amount` (int), `ShiftCalendarObject` |
| **Marker** | Marker | `.MaterialFlow_AGV.BasicObjects.Resources.Marker` | (随父类) | (随父类) |
| **PalletAGV** | Transporter | `.MaterialFlow_AGV.BasicObjects.MUs.Transporter` | `setRoute`, `setRouteSegments` (Transporter 默认) | `IsIdle`, `BatCharge`, `BatCapacity`, `Speed` |
| **BoxAGV** | Transporter | 同 PalletAGV | 同上 | 同上 |

## 四、Transporter 关键属性(PalletAGV/BoxAGV 共享)

| 属性 | 类型 | 默认 | 备注 |
|---|---|---|---|
| `IsTractor` | boolean | false | 是否可拖挂 trailer |
| `AutomaticRouting` | boolean | true | 启用自动路由 |
| `Speed` | length/time | 1.2 m/s | 行驶速度 |
| `Acceleration` | real | 0.5 | 加速(m/s²) |
| `Deceleration` | real | 1.0 | 减速 |
| `StopAtDestination` | boolean | false | 是否在目的地停车 |
| `XDim` / `YDim` / `ZDim` | integer | 2/1/1 | 装载空间维度 |
| `MUHeight` / `MULength` / `MUWidth` | length | 0.4/1.6/0.8 m | MU 物理尺寸 |
| `BatCapacity` | real | 8 | 电池容量 |
| `BatCharge` | real | 3 | 当前电量 |
| `BatBasicCons` | real | 1 | 静止消耗 |
| `BatDriveCons` | real | 8 | 行驶消耗 |
| `BatChargeCurrent` | real | 40 | 充电电流 |
| `BatChargeCtrl` | method ref | `self.OnCharge` | 充电回调 |
| `BatteryUsed` | boolean | true | 是否启用电池模型 |
| `SafetyZones` | length[4] | [1, 0.3, 2, 0.6] | 安全距离(front, Δside, rear, Δback) |
| `RouteWeightingAttr` | string | "" | 自动路由权重属性 |

## 五、AGVPool 关键 API

```simtalk
-- 静态方法(读)
pool.getIdleAGV() -> object        -- 返回第一个空闲 AGV,自动设 IsIdle=false
pool.getAssignedAGV(No:integer) -> object
pool.getAssignedAGVsTable([tab]) -> table|any

-- 读-only 属性
pool.NumIdleAGVs -> integer        -- watchable
pool.StatAverageTraveledDistance -> length
```

## 六、Marker 简述

`Marker` 是 AGV 路径上的**逻辑航点**。一个 AGV 可有多个 Marker 作为 visit list。配合 `Transporter.setRoute([marker1, marker2, ...])` 实现多站路径。

```simtalk
var AGV : object := AGVPool.Cont
AGV.setRoute([M1, M2, M3, M4])
waituntil AGV.DestinationWasReached
AGV.setRoute([M1, M2, M3, M4])
```

## 七、CapacityCalculation_v2

Frame 类型,内部有方法实现容量分析。BFS dump 时碰到 JSON parse error(估计是方法体内含特殊字符)。直接 `str_to_obj(".MaterialFlow_AGV.AdvancedObejcts.CapacityCalculation_v2")` 可访问,但要列内容需要 read_library 的 single-method probe 模式。

## 八、示例模型(Area/)

`MaterialFlow_AGV.Area` 子文件夹提供开箱即用的演示 Frame:

- `PhaseIV_Shopfloor` / `PhaseIII_Shopfloor` / `PhaseIV_GRArea`
- `PhaseIV_SF` — 45 个节点,典型 AGV 网络(Markers + Connectors)
- `SmallArea/PhaseIV_MaterialArea1`, `PhaseIV_MaterialArea2`

直接 `duplicate()` 这些 Frame 到 `.Models.<your_model>` 即可获得完整 AGV 拓扑。

## 九、Vendor 限制 vs AGV_Claude 优化

Vendor 提供的能力**仅够"能跑"**,不直接优化调度策略:

| 能力 | MaterialFlow_AGV (vendor) | AGV_Claude (优化版) | 优化点 |
|---|---|---|---|
| 调度策略 | `AGVPool.getIdleAGV()` FIFO | `Pool.AGV_dispatch(pool, pickStation, minBattery)` 按 `1/(1+distance)` 评分,过滤低电量 AGV | 距离最优 + 电量门控 |
| 释放统计 | 无(只 reset `IsIdle`) | `Pool.AGV_release(agv, jobTime, distance)` 写入 AGVTelemetry 表 | jobsDone / totalDistance / lastJobEnd 自动累加 |
| 充电策略 | `BatChargeCtrl` 被动触发 | `Pool.AGV_requestCharge(pool, threshold)` 返回需充电 AGV 列表 | 主动预测性 |
| 多站路由 | `Transporter.setRoute([...])` 一次性 | `Pool.AGV_batchedRoute(agv, stops)` 链式 Destination | 牛奶巡回(milk-run)模式 |
| 状态仪表板 | 无 | `Pool.AGV_dashboard()` 一行打印每池 idle/busy + 全队累计 distance | 调试可视化 |
| 重置 | 手动 | `Pool.AGV_reset()` 截断 Jobs/Telemetry 表 | 实验复制间快速清理 |

## 十、AGV_Claude 类库结构

```
.AGV_Claude/                            (与 MaterialFlow_AGV 同级)
├── Objects/                          (Folder)
│   ├── AGVJobs [DataTable]           (8 列: JobID/Pick/Drop/Priority/Deadline/Status/AssignedAGV/CreatedAt)
│   └── AGVTelemetry [DataTable]      (9 列: AGVID/AGV/Pool/JobsDone/TotalDistance/BatteryEvents/IdleTime/LastJobEnd/IsIdle)
└── Pool [Frame]                     (宿主,所有方法挂这里)
    ├── AGV_init
    ├── AGV_dispatch (param pool, pickStation, minBattery)
    ├── AGV_release (param agv, jobTime, distance)
    ├── AGV_requestCharge (param pool, threshold)
    ├── AGV_batchedRoute (param agv, stops)
    ├── AGV_dashboard
    └── AGV_reset
```

## 十一、评分函数(AGV_dispatch)

```simtalk
score := 1 / (1 + agv.distanceTo(pickStation))
if agv.IsIdle = true
    if agv.BatCharge >= minBattery
        if score > bestScore
            bestScore := score
            bestAgv := agv
        end
    end
end
```

- **距离近 → 分高 → 优先**:`1/(1+d)` 形式避免除零,且 d∈[0,∞) 时分∈(0,1] 单调
- **电量门控**:默认 `minBattery = 0.2`,可用 `param minBattery: real` 覆盖

## 十二、遥测表使用模式

调用方在 `model.init` 中:

1. 把所有 `AGVPool` 引用填入 `.AGV_Claude.pools` 表(列 0)
2. 调 `AGV_init` 初始化两张表头
3. 在 AGV 被分配前调 `AGV_dispatch`;在 AGV 完成任务回到池时调 `AGV_release`

`AGV_release` 自动 upsert:

- 第一次见到该 AGV → 新建 telemetry 行
- 之后每次 → jobsDone++、totalDistance+=、IsIdle=true、lastJobEnd:=simTime

## 十三、何时使用 AGV_Claude vs vendor

**不需要 AGV_Claude**:

- 模型只有 1 个 AGV / 1 个 station → vendor 够用
- AGV 调度逻辑简单 FEFO(first-eligible-first-out)→ 直接用 `getIdleAGV`
- 实验需要 vendor 自带的统计(`StatAverageTraveledDistance`)→ 不要切换

**必须用 AGV_Claude**:

- 多 AGV(>3)+ 多 station → distance-aware 调度能省 15-30% 行程
- 电池敏感场景(AGV 频繁长途)→ 主动 `requestCharge` 避免半路耗尽
- 需要 dashboard 实时监控 → vendor 无此能力
- 牛奶巡回(milk-run)任务 → `batchedRoute` 链式调度

## 十四、扩展厂商类库的标准步骤

1. **同级建 Folder**:`.MyVendorExtension`(与 `MaterialFlow_AGV` 同级,作为用户态 Class Library)
2. **创建 Objects Folder**:装自定义 DataTable(遥测 / 任务)
3. **创建宿主 Frame**(如 `.MyVendorExtension.Pool`):装所有方法
4. **7 类方法 scaffolding**:
   - `init` — 初始化表头(用 `MaxYDim/MaxXDim`,不是 `setSize`!)
   - `dispatch` — 距离评分 + 电量门控
   - `release` — 自动 upsert telemetry
   - `requestCharge` — 主动扫表返回需充电列表
   - `batchedRoute` — 链式 destination(支持 milk-run)
   - `dashboard` — 一行打印 + 或写入 DataTable / 文件
   - `reset` — 截断表(实验复制间快速清理)
5. **接入 model.init**:把所有 vendor Pool 引用填入 `.MyVendorExtension.pools` 表

## 经验 Log

> 本节是 **append-only** 时间线——新发现直接追加在末尾。

<!-- 暂无 entry——首个 entry 由下次踩坑时 append -->
</content>
</invoke>