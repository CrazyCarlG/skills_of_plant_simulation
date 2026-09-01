# MaterialFlow_AGV — AGV_Claude 优化点对照

> `AGV_Claude` 是与 `MaterialFlow_AGV` **同级的用户态 Class Library Folder**(路径 `.AGV_Claude`),
> 用 SimTalk 在用户域内实现 vendor 没提供的优化算法。

## API 对照表

| 能力 | MaterialFlow_AGV (vendor) | AGV_Claude (优化版) | 优化点 |
|---|---|---|---|
| 调度策略 | `AGVPool.getIdleAGV()` FIFO | `Pool.AGV_dispatch(pool, pickStation, minBattery)` 按 `1/(1+distance)` 评分,过滤低电量 AGV | 距离最优 + 电量门控 |
| 释放统计 | 无(只 reset `IsIdle`) | `Pool.AGV_release(agv, jobTime, distance)` 写入 AGVTelemetry 表 | jobsDone / totalDistance / lastJobEnd 自动累加 |
| 充电策略 | `BatChargeCtrl` 被动触发 | `Pool.AGV_requestCharge(pool, threshold)` 返回需充电 AGV 列表 | 主动预测性 |
| 多站路由 | `Transporter.setRoute([...])` 一次性 | `Pool.AGV_batchedRoute(agv, stops)` 链式 Destination | 牛奶巡回 (milk-run) 模式 |
| 状态仪表板 | 无 | `Pool.AGV_dashboard()` 一行打印每池 idle/busy + 全队累计 distance | 调试可视化 |
| 重置 | 手动 | `Pool.AGV_reset()` 截断 Jobs/Telemetry 表 | 实验复制间快速清理 |

## 类库结构

```
.AGV_Claude/
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

## 评分函数 (AGV_dispatch)

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

- **距离近 → 分高 → 优先**:1/(1+d) 形式避免除零,且 d∈[0,∞) 时分∈(0,1] 单调。
- **电量门控**:默认 `minBattery = 0.2`,可用 `param minBattery: real` 覆盖。

## 遥测表使用模式

调用方在 model.init 中:
1. 把所有 `AGVPool` 引用填入 `.AGV_Claude.pools` 表(列 0)。
2. 调 `AGV_init` 初始化两张表头。
3. 在 AGV 被分配前调 `AGV_dispatch`;在 AGV 完成任务回到池时调 `AGV_release`。

`AGV_release` 自动 upsert:
- 第一次见到该 AGV → 新建 telemetry 行。
- 之后每次 → jobsDone++、totalDistance+=、IsIdle=true、lastJobEnd:=simTime。

## 何时不需要 AGV_Claude

- 模型只有 1 个 AGV / 1 个 station → vendor 够用。
- AGV 调度逻辑简单 FEFO (first-eligible-first-out) → 直接用 `getIdleAGV`。
- 实验需要 vendor 自带的统计(StatAverageTraveledDistance) → 不要切换。

## 何时必须用 AGV_Claude

- 多 AGV (>3) + 多 station → distance-aware 调度能省 15-30% 行程。
- 电池敏感场景(AGV 频繁长途) → 主动 requestCharge 避免半路耗尽。
- 需要 dashboard 实时监控 → vendor 无此能力。
- 牛奶巡回 (milk-run) 任务 → batchedRoute 链式调度。