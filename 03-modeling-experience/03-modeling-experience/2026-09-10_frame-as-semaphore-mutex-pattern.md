---
last_updated: 2026-09-10
dimension: 03-modeling-experience
source_sessions:
  - 04-agent-memory/student-memory/2026-09-02-MarkerCrossing-crossing-semaphore-deepdive.md
models_touched: [Models.MarkerCrossing]
---

# Frame-as-Semaphore — Frame 内部 Variable + EntranceCtrl/ExitCtrl 实现 AGV 互斥锁

## 症状
- 4 个 AGV 路径交叉点(2×2 grid + 对角交叉)需要互斥资源管理。
- 教学集用 Frame 内部 Variable(`Owner` + `StoppingCounter`)做互斥锁,**不**用 RCS 集中 DataTable 状态机。
- 嵌套 4 Frame 各占 1 个角,内部含 26 子节点(4 corner + 5 entry/exit Markers + 4 Variables + 4 Methods + 9 Connector)。

## 根因 / 完整机制
**嵌套 Frame EntranceCtrl**(进入信号量 + 3D 状态切换):
```simtalk
if Owner != void
    @.StoppingCounter += 1
    waituntil Owner = void
    Owner := @
    @.StoppingCounter -= 1
else
    Owner := @
    _3D.hideGraphicGroup("Free")
    _3D.showGraphicGroup("Busy")
end
```

**嵌套 Frame ExitCtrl**(退出释放):
```simtalk
if Owner = @
    Owner := void
end
if Owner = void
    _3D.showGraphicGroup("Free")
    _3D.hideGraphicGroup("Busy")
end
```

**关键 SimTalk 字面契约**:
- `@.StoppingCounter += 1` / `waituntil Owner = void` — semaphore 互斥等待
- `@` 在 EntranceCtrl 内是当前 Frame 自身,`Owner := @` 设置锁持有者
- `_3D.showGraphicGroup("Free")` / `hideGraphicGroup("Busy")` — 3D 状态视觉化

## Workaround / 结论
- **Frame-as-Semaphore vs RCS**:小型仿真用单 Frame + 2 Variables 实现 semaphore 简单;**不**支持多 AGV 协调 / 任务优先级;大场景用 RCS 集中 DataTable 状态机。
- **callback 注入 vs 隐式事件**:Init 显式 `agv.DestCtrl = &DestCtrl` 是 dispatcher 主动注入,与 PortalCrane/SevenAxisRobot 隐式 Station callback(OnPull/OnExit)形成对比。
- **`existsObject("X")` 防御编程**:RecalcLayout 中 `if existsObject("X") then ... end` 防止子对象缺失时报错,适合"可选子对象"模式。
- **`Owner` Variable + `StoppingCounter`**:双 variable semaphore — Owner 持有当前 AGV,StoppingCounter 累计等待数(可能是 GUI 状态显示)。
- **嵌套 Frame 4 副本 vs Class+Instance 复用**:用户用 4 个独立 Frame 复制,不用 `UserObjects/MarkerCrossing` + 4 instances 模式 — 与 Factory51 `Production` + `P1/P2` 范式不同,**简化**但失去扩展性。

## see also
- `04-agent-memory/student-memory/2026-09-02-MarkerCrossing-crossing-semaphore-deepdive.md`(完整 130 对象实例 + 全部 6 个 Method 源码)
- 横向对比:`2026-09-10_station-onpull-spectrum-5-models.md`(Frame-as-Semaphore 是 7-Frame 集三种 callback 模式之一)
- `@plant-simulation-knowledge-synthesizer 评审`:`02-domain-know-how/04-modeling-example/frame-as-semaphore-cell.md` 完整教学案例

## 反思
Frame-as-Semaphore 是 PS 教学 cell 的标准互斥模式,但 student 0 次实跑仿真验证(只 dump 源码)— 真正落地前 expert 必须实跑验证 `StoppingCounter` 实际行为 + `RecalcLayout` 何时被调用。
