# MaterialFlow_AGV — 类层级与继承链

> 基于 2026-08-31 probe_inheritance.py 输出 + BFS tree dump 整理。
> Source model port: 50007. Path root: `.MaterialFlow_AGV`。

## 继承总览

```
.MUs.Transporter  ←  PalletAGV, BoxAGV        (Transporter 衍生)
.Resources.AGVPool ←  .Resources.AGVPool       (AGVPool 复用)
.Resources.Marker  ←  .Resources.Marker        (Marker 复用)
.MaterialFlow.Source ←  OrderCreater            (Source 衍生)
.Frame ← CapacityCalculation_v2                  (自定义 Frame)
```

| Class path | Type | Origin (parent class) |
|---|---|---|
| `.MaterialFlow_AGV.AdvancedObejcts.PalletAGV` | Transporter | `.MaterialFlow_AGV.BasicObjects.MUs.Transporter` |
| `.MaterialFlow_AGV.AdvancedObejcts.BoxAGV` | Transporter | `.MaterialFlow_AGV.BasicObjects.MUs.Transporter` |
| `.MaterialFlow_AGV.AdvancedObejcts.AGVPool` | AGVPool | `.MaterialFlow_AGV.BasicObjects.Resources.AGVPool` |
| `.MaterialFlow_AGV.AdvancedObejcts.Marker` | Marker | `.MaterialFlow_AGV.BasicObjects.Resources.Marker` |
| `.MaterialFlow_AGV.AdvancedObejcts.CapacityCalculation_v2` | Frame | (root class — standalone) |
| `.MaterialFlow_AGV.AdvancedObejcts.OrderCreater` | Source | `.MaterialFlow_AGV.BasicObjects.MaterialFlow.Source` |

> ⚠️ **拼写陷阱**:`AdvancedObejcts` 不是 `AdvancedObjects`(厂商笔误)。所有继承链 path 必须用 vendor 的拼写,否则 str_to_obj 返回 void。

## Transporter 关键属性 (PalletAGV/BoxAGV 共享)

来自 Factory51/Factory51.psfm/UserObjects/MUs/AGV.yaml 节选:

| 属性 | 类型 | 默认 | 备注 |
|---|---|---|---|
| `IsTractor` | boolean | false | 是否可拖挂 trailer |
| `AutomaticRouting` | boolean | true | 启用自动路由 |
| `Speed` | length/time | 1.2 m/s | 行驶速度 |
| `Acceleration` | real | 0.5 | 加速 (m/s²) |
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
| `SafetyZones` | length[4] | [1, 0.3, 2, 0.6] | 安全距离 (front, Δside, rear, Δback) |
| `RouteWeightingAttr` | string | "" | 自动路由权重属性 |

## AGVPool 关键 API

```simtalk
-- 静态方法(读)
pool.getIdleAGV() -> object        -- 返回第一个空闲 AGV,自动设 IsIdle=false
pool.getAssignedAGV(No:integer) -> object
pool.getAssignedAGVsTable([tab]) -> table|any

-- 读-only 属性
pool.NumIdleAGVs -> integer        -- watchable
pool.StatAverageTraveledDistance -> length
```

## Marker 简述

`Marker` 是 AGV 路径上的**逻辑航点**。一个 AGV 可有多个 Marker 作为 visit list。配合 `Transporter.setRoute([marker1, marker2, ...])` 实现多站路径。

参考用法(来自 help `conveyor-track-agv-battery.md`):
```simtalk
var AGV : object := AGVPool.Cont
AGV.setRoute([M1, M2, M3, M4])
waituntil AGV.DestinationWasReached
AGV.setRoute([M1, M2, M3, M4])
```

## CapacityCalculation_v2

Frame 类型,内部有方法实现容量分析。BFS dump 时碰到 JSON parse error(估计是方法体内含特殊字符)。直接 `str_to_obj(".MaterialFlow_AGV.AdvancedObejcts.CapacityCalculation_v2")` 可访问,但要列内容需要 read_library 的 single-method probe 模式。

## 示例模型 (Area/)

`MaterialFlow_AGV.Area` 子文件夹提供开箱即用的演示 Frame:
- `PhaseIV_Shopfloor` / `PhaseIII_Shopfloor` / `PhaseIV_GRArea`
- `PhaseIV_SF` — 45 个节点,典型 AGV 网络 (Markers + Connectors)
- `SmallArea/PhaseIV_MaterialArea1`, `PhaseIV_MaterialArea2`

直接 `duplicate()` 这些 Frame 到 `.Models.<your_model>` 即可获得完整 AGV 拓扑。