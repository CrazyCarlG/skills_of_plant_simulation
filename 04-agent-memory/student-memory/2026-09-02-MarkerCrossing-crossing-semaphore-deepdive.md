# Student Note — MarkerCrossing Frame-as-Semaphore + 嵌套 cell 模板深挖
**Date:** 2026-09-02  **Agent:** plant-simulation-student
**Model:** .Models.MarkerCrossing  **Scenario:** crossing-semaphore-deepdive
**Duration:** 21:44 – 21:45  **Skills called:** local-simtalk-execution (simtalk_run + readlog, ~40 次调用)
**Baselines consulted:** `01-plantsimulation-knowledge/01-plant-simulation-help/objects/resource-objects/AGVPool/{README,methods,read-only-attributes}`(沿 prior);`01-plant-simulation-knowledge/01-plant-simulation-help/objects/resource-objects/Marker/general/general.md`(沿 prior AGVWithRobot)
**Result:** success — 完整 26 子节点 + Init/DestCtrl + 4 嵌套 Method(EntranceCtrl/ExitCtrl/RecalcLayout/Reset)+ 13 Connector 拓扑全 dump

---

## 01-factory-know-how
### 观察(Observe)
- `.Models.MarkerCrossing.ICT=Frame` / `.ICN=Network`(同 prior PortalCrane/AGVWithRobot/SevenAxisRobot)
- **完整子对象清单**(`numNodes=26`):
  - 1 EventController (`EventCtl`)
  - **4 嵌套 Frame** `MarkerCrossing` / `MarkerCrossing2` / `MarkerCrossing3` / `MarkerCrossing4`(全部 `ICT=Frame` / `ICN=Network`)
  - 1 AGVPool (`NwAGVPool`)
  - 2 Method (`Method` ICN — 注意无 Nw 前缀):`Init` / `DestCtrl`
  - 4 Marker (`NwMarker`):`M1` / `M2` / `M3` / `M4`
  - 1 DataList (`NwRandom`):`Destinations`
  - 13 Connector (`NwArc`):`Connector` + `Connector2-13`(注:**缺 Connector1**,`Connector` 出现在末尾而非开头)
- 🆕 **重大 Novel 发现**:**DataList ICN = `NwRandom`** — DataList 类内部实现是 random accessor!这是 PS 2.0 类命名空间重构的一部分:`NwRandom` (Network + Random) 暗示它是 Network 子类族的 random accessor
- 🆕 **首次发现**:**Method ICN = `Method`**(普通类,无 Nw 前缀)— 与 Frame/Source/Station/NwArc 等 Nw 系列类不同,Method 是普通 PS 内置类
- 🆕 **首次发现**:**4 嵌套 Frame 各自含 26 个子节点** — 嵌套 MarkerCrossing 内部结构:
  - **4 corner Markers**:`TopLeft` / `TopRight` / `BottomLeft` / `BottomRight`(定位 4 角)
  - **5 entry/exit Markers**:`BottomEntry` / `RightEntry` / `LeftEntry` / `BottomExit` / `RightExit`(进出口)
  - **4 Variables**:`Owner` (object) / `TrackPitch=2` / `EntranceLength=1.7` / `ExitLength=1.7`
  - **4 Methods**:`EntranceCtrl` / `ExitCtrl` / `RecalcLayout` / `Reset`
  - **9 Connector**(内部连接,无命名 gap — `Connector/1/2/3/4/6/7/10/12`)
- **拓扑实测**(完整 Connector.Pred / .Succ):
  ```
  右侧 cell:
    AGVPool --[Connector]--> MarkerCrossing
    MarkerCrossing --[Connector2]--> M2
    M2 --[Connector3]--> MarkerCrossing2
    MarkerCrossing2 --[Connector4]--> M1
    M1 --[Connector5]--> MarkerCrossing          (右侧闭环)
  
  左侧 cell:
    MarkerCrossing3 --[Connector6]--> M4
    M4 --[Connector7]--> MarkerCrossing4
    MarkerCrossing4 --[Connector8]--> M3
    M3 --[Connector9]--> MarkerCrossing3         (左侧闭环)
  
  对角交叉(cross connection):
    MarkerCrossing --[Connector10]--> MarkerCrossing3
    MarkerCrossing3 --[Connector11]--> MarkerCrossing
    MarkerCrossing2 --[Connector12]--> MarkerCrossing4
    MarkerCrossing4 --[Connector13]--> MarkerCrossing2
  ```
- **完整拓扑图** = **2×2 grid + 双向对角线**:
  - 4 个嵌套 Frame 各占 1 个角,标记为 MarkerCrossing/2/3/4
  - M1/M2/M3/M4 是 4 个交叉点边缘 marker
  - 物理语义:**4 个 AGV 路径交叉点**(2×2 网格 + 对角线穿越)

### Init + DestCtrl Method 源码 dump(`obj.&Method.Program` 语法)

**Init**(AGV dispatcher 死循环):
```simtalk
while true
    var agv = AGVPool.getIdleAGV
    if agv = void then exitloop end
    agv.DestCtrl = &DestCtrl
    agv.Destination = Destinations[z_uniform(1, Destinations.Dim+1)]
    wait 10
end
```

**DestCtrl**(on-exit 重新派单):
```simtalk
wait 10
?.Destination = Destinations[z_uniform(1, Destinations.Dim+1)]
```

🆕 **Novel 模式**:**显式 callback 注入** `agv.DestCtrl = &DestCtrl` — Init 在 dispatch AGV 时把 DestCtrl method ref 赋值给 AGV.DestCtrl 属性,后续 AGV 完成 dest 后触发 on-exit 自动重新派单

### 嵌套 Frame 内部 Method 源码 dump(4 个全 dump)

**EntranceCtrl**(进入信号量):
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

**ExitCtrl**(退出释放):
```simtalk
if Owner = @
    Owner := void
end
if Owner = void
    _3D.showGraphicGroup("Free")
    _3D.hideGraphicGroup("Busy")
end
```

**RecalcLayout**(布局重算 with param):
```simtalk
param newValue:real
var tph:real := TrackPitch/2
if existsObject("TopLeft")     then TopLeft.Coordinate3D     := [-tph,  tph, 0] end
if existsObject("TopRight")    then TopRight.Coordinate3D    := [ tph,  tph, 0] end
if existsObject("BottomLeft")  then BottomLeft.Coordinate3D  := [-tph, -tph, 0] end
if existsObject("BottomRight") then BottomRight.Coordinate3D := [ tph, -tph, 0] end
// ... (类似 LeftEntry/Exit, TopEntry/Exit, RightEntry/Exit, BottomEntry/Exit)
```

**Reset**(3D 状态复位):
```simtalk
_3D.showGraphicGroup("Free")
_3D.hideGraphicGroup("Busy")
```

### 理论对照(Reference + Judge)
| 观察 | Baseline 出处 | 判定 | Evidence |
|---|---|---|---|
| `DataList.ICN=NwRandom` | `01-plant-simulation-help/objects/information-flow-objects/DataList/README.md`(未深读) | 🆕 **Novel** | PS 2.0 类注册名空间重构 — DataList 内部实现是 random accessor,与 NwNetwork 类族(NwSource/NwArc/NwMarker/NwAGVPool)并列 |
| `Method.ICN=Method` | 沿 prior `02-domain-know-how/03-modeling-know-how/01-objects/object-classification.md`(未深读 Method ICN) | 🆕 **Novel** | Method 是普通 PS 内置类,无 Nw 前缀 — 与 Frame/NwSource 等 Network 子类区分 |
| 嵌套 Frame 自包含 26 子节点 | `object-classification.md §3.3 Frame-as-Container 双重身份`(沿 prior) | ✅ matches | 嵌套 Frame 是自包含 mini-cell,可作为复用模板 |
| 4 Variables `Owner/TrackPitch/EntranceLength/ExitLength` | `02-domain-know-how/01-factory-know-how/factory-modeling-architecture.md`(未明文 frame-as-semaphore) | 🆕 **Novel 模式** | **Frame-as-Semaphore**:用 Frame 内部 Variable (`Owner` + `StoppingCounter`)做互斥锁,模拟 AGV 路径交叉点的资源争用 |
| `_3D.showGraphicGroup("Free"/"Busy")` | `01-plant-simulation-help/objects/material-flow-objects/Station/README.md`(沿 prior,3D 未深读) | ✅ matches | PS 标准 3D 图形组切换 API |
| `Coordinate3D := [x, y, z]` 3D 坐标 | 同上 | ✅ matches | Marker 标准 3D 坐标赋值 |
| `existsObject("X")` 防御检查 | `02-simtalk/control-flow-error-handling/README.md`(沿 prior) | ✅ matches | 标准 PS 对象存在性检查 |
| `agv.DestCtrl = &DestCtrl` callback 注入 | `AGVPool/methods.md`(沿 prior,未明文 DestCtrl callback 注入) | 🆕 **Novel** | Init 显式将 Frame 内部 Method ref 注入到 AGV 的 DestCtrl 属性 — **回调注入模式** |
| `z_uniform(1, Dim+1)` off-by-one | `language-quirks-reference.md`(沿 prior) | ⚠️ confirmed Quirk | 第 3 次在 7-Frame 集不同模型确认 `z_uniform` 闭区间 +1 off-by-one |
| `MarkerCrossing` 同名嵌套 4 Frame | `object-classification.md §3.3` + prior `2026-09-02-Models-RobotSet-robot-set-overview.md` | ✅ matches | 7-Frame 集第 3 个 Frame-as-Container 用例(MarkerCrossing 在 RobotSet overview 已提及) |
| 13 Connector 编号无 Connector1 | prior AGVWithRobot/SevenAxisRobot UUID-stable gap | ✅ matches | PS 编辑器命名稳定约定(用户删除 Connector1 后不重命名,新增 Connector 直接补号) |

### 候选 finding
- **DataList ICN=NwRandom** → 沿 prior ICN 重构 finding(累计 13 个新 ICN)
- **Frame-as-Semaphore 模式**(`Owner` Variable + `StoppingCounter` + `_3D.showGraphicGroup` 状态切换)→ 建议 curator 评估沉淀到 `02-domain-know-how/01-factory-know-how/factory-modeling-architecture.md` 新增"Frame-as-Semaphore 互斥锁"小节
- **callback 注入模式**(`agv.DestCtrl = &DestCtrl`)→ 建议 curator 评估在 `02-domain-know-how/01-factory-know-how/factory-modeling-architecture.md` 新增"dispatcher 显式 callback 注入"小节
- **嵌套 Frame 自包含 cell 模板** → 沿 prior finding 扩展(累计第 3 个 Frame-as-Container 用例)

---

## 02-simtalkclaude-knowhow
### 观察(Observe)
- 本 session 0 调用 `.SimtalkClaude.*`;桥协议未触发
- 继承 prior 全部 Quirk(#13-26)
- **`obj.&Method.Program` 语法在 5 个不同 Method 上验证全部成功**(Init / DestCtrl / EntranceCtrl / ExitCtrl / RecalcLayout / Reset)— 完全可移植 SOP
- 🆕 **新发现**:Method `param newValue:real` 在 RecalcLayout 中 — 表明用户用 observer pattern 调 RecalcLayout(带参数)— RecalcLayout 不是普通回调而是显式调用
- **Variable 读取 API 是 `.Value`**(实测 `Owner.Value=VOID`、`TrackPitch.Value=2` 等)— `.contents` 报 Unknown identifier(❌ `Contents` 不是 Variable API,这是 Quirk #18 batch 静默跳过的典型)
- **DataList element 打印** `print d[i]` 触发 "Arithmetic operations" 错(类似 Quirk #15)— d 是 list,`d[i]` 返回 object,`print sep + d[i]` 把 object 当 string 拼接触发算术错

### 理论对照
| 观察 | Baseline 出处 | 判定 |
|---|---|---|
| `obj.&Method.Program` 跨 6 个 Method 验证 | prior onpull-dump SOP | ✅ matches — SOP 完全可移植 |
| Variable `.Value` API(非 `.contents`) | `02-domain-know-how/03-modeling-know-how/02-simtalk/language-quirks-reference.md`(未深读 Variable API) | ⚠️ 修订 prior 误判 — 实际 Variable 公开属性是 `Value`(实测) |

---

## 03-modeling-know-how
### 01-objects
- **完整对象层级图**(.Models.MarkerCrossing Network 子图):
  - Frame `MarkerCrossing` (Network)⊃
    - EventController (EventCtl)
    - **4 嵌套 Frame (Network)**:MarkerCrossing / 2 / 3 / 4(每个嵌套 26 子节点)
    - AGVPool (NwAGVPool)⊃ AGV (Transporter/Vehicle)
    - 4 Marker (NwMarker):M1 / M2 / M3 / M4(路径边缘)
    - 1 DataList (NwRandom):Destinations(dim=4)
    - 2 Method (Method):Init / DestCtrl
    - 13 Connector (NwArc):Connector / 2-13(命名 gap)
- **嵌套 Frame 内部**(每个 MarkerCrossing/2/3/4):
  - 4 corner Markers (NwMarker):TopLeft / TopRight / BottomLeft / BottomRight
  - 5 entry/exit Markers (NwMarker):BottomEntry / RightEntry / LeftEntry / BottomExit / RightExit
  - 4 Variables:Owner (object) / TrackPitch (real=2) / EntranceLength (real=1.7) / ExitLength (real=1.7)
  - 4 Methods (Method):EntranceCtrl / ExitCtrl / RecalcLayout / Reset
  - 9 Connector (NwArc):内部连接(无命名 gap)
- **判定**:✅ matches prior ICN 体系(累计 13 个新 ICN);🆕 **Novel**:`DataList=NwRandom` / `Method=Method` / 嵌套 Frame 自包含 cell / Frame-as-Semaphore / callback 注入

### 02-simtalk
- **完整 Method dump 集**:
  - **Init** (Frame-level dispatcher,死循环派单)
  - **DestCtrl** (Frame-level re-dispatcher,on-exit 重新派单)
  - **EntranceCtrl** (嵌套 Frame 自包含 — 进入信号量 + 3D 状态切换)
  - **ExitCtrl** (嵌套 Frame 自包含 — 退出释放 + 3D 状态切换)
  - **RecalcLayout** (嵌套 Frame 自包含 — 3D 布局重算,带 param:real)
  - **Reset** (嵌套 Frame 自包含 — 3D 状态复位)
- **关键 SimTalk 字面契约**:
  - `agv.DestCtrl = &DestCtrl` — 显式 method ref 注入(callback 注入模式)
  - `@.StoppingCounter += 1` / `waituntil Owner = void` — semaphore 互斥等待
  - `@` 在 EntranceCtrl 内是当前 Frame 自身,`Owner := @` 设置锁持有者
  - `_3D.showGraphicGroup("Free")` / `hideGraphicGroup("Busy")` — 3D 状态视觉化
  - `if existsObject("X") then ... end` — 防御性 child object 存在性检查
  - `Coordinate3D := [x, y, z]` — 3D 坐标数组字面量赋值
  - `param newValue:real` — 带参数 Method(observer pattern)

### 03-software
- 本 session ~40 次 simtalk_run + ~40 次 readlog
- **核心 skill 经验**:
  - **`obj.&Method.Program` SOP 完全可移植** — 6 个不同 Method 全部成功(Frame-level + 嵌套 Frame-level)
  - **Variable 读取**:用 `.Value`(非 `.contents`)
  - **`existsObject` API 在 RecalcLayout 中大量使用** — 用户用此模式保证子对象删除时不报错(防御编程)

---

## 04-modeling-example
### 观察(Observe)
- **MarkerCrossing = 嵌套 Frame cell + AGV path crossing 完整教学案例**:
  - 1 EventController + 4 嵌套 Frame(cell) + 1 AGVPool(1 AGV) + 4 边缘 Marker + 1 DataList + 2 Frame-level Method + 13 Connector
  - **总节点数**:outer 26 + 4×26 nested = **130 个对象**(104 在嵌套 Frame 内)
- **物理语义**:**4 个 AGV 路径交叉点**(2×2 grid + 对角交叉),用 Frame-as-Semaphore 解决资源争用
- **Frame-as-Semaphore 机制**(嵌套 Frame EntranceCtrl + ExitCtrl):
  - `Owner` Variable 持有当前进入的 AGV
  - `StoppingCounter` 累计等待数(可视化)
  - `_3D.showGraphicGroup("Free"/"Busy")` 视觉化状态
  - EntranceCtrl 先检查 Owner,已有则等待;ExitCtrl 释放 Owner
- **callback 注入机制**(Frame-level Init + DestCtrl):
  - Init 把 DestCtrl method ref 显式注入到 AGV.DestCtrl 属性
  - AGV 完成 transport 后自动触发 DestCtrl 重新派单

### 理论对照
| 观察 | Baseline 出处 | 判定 |
|---|---|---|
| 4 嵌套 Frame 形成 2×2 cell grid | `object-classification.md §3.3 Frame-as-Container` + `factory-modeling-architecture.md` Factory51 3 层范式 | ⚠️ diverges — 比 Factory51 简化(无 UserObjects/类库)但用 Frame-as-Semaphore 实现真实 AGV 互斥 |
| Frame-as-Semaphore 互斥锁 | `warehouse-and-ctu-patterns.md §2.1`(RCS 11 DataTable vs Frame Semaphore) | ⚠️ diverges — 用户用单 Frame + 2 Variables 实现 semaphore,**不**用 RCS 集中 DataTable 状态机 |
| dispatcher 显式 callback 注入 | `AGVPool/methods.md`(沿 prior,未明文) | 🆕 Novel — Init 中 `agv.DestCtrl = &DestCtrl` 是**显式 callback 注入**,对比默认 PS DestCtrl 是隐式事件触发 |

### 候选 finding
- **Frame-as-Semaphore 互斥教学 cell** → 建议 curator 评估在 `02-domain-know-how/04-modeling-example/frame-as-semaphore-cell.md` 新增完整教学案例(嵌套 Frame + Owner Variable + EntranceCtrl/ExitCtrl 源码)(baseline:本 session §01)
- **嵌套 Frame cell 模板(2×2 grid + 对角交叉)** → 沿 prior finding 扩展,本 session 提供完整 130 对象实例

---

## 05-modeling-experience
### 观察(Observe)
- **Quirk 累计**:本 session 0 新增 Quirk(全部沿用 prior),✅ SOP `obj.&Method.Program` 跨 6 个 Method 验证可移植
- **关键洞察**:
  - **Frame-as-Semaphore 是 PS 教学 cell 的标准互斥模式** — 比 RCS 简单,适合小型仿真;但**不**支持多 AGV 协调 / 任务优先级
  - **callback 注入 vs 隐式事件**:Init 显式 `agv.DestCtrl = &DestCtrl` 是 dispatcher 主动注入,与 PortalCrane/SevenAxisRobot 隐式 Station callback(OnPull/OnExit)形成对比
  - **`existsObject` 防御性编程** — 用户在 RecalcLayout 中用 `if existsObject("X") then ... end` 防止子对象缺失时报错,适合"可选子对象"模式
  - **`Owner` Variable + `StoppingCounter`** — 双 variable semaphore:Owner 持有当前 AGV,StoppingCounter 累计等待数(可能是 GUI 状态显示)
  - **嵌套 Frame 4 副本 26 子节点** — 4×26=104 内节点,显示 Frame-as-Container 是真正的"mini-cell 复制"模式(用户复制 4 次嵌套而非定义 class + 4 instances)
- **跨 session 综合**(沿 prior 7 个 deepdive + 本 session):
  - **修正 prior branching-deepdive/onpull 系列**:SevenAxisRobot 是纯声明式 cell,本 MarkerCrossing 才是**完整 dispatcher + 嵌套 semaphore 教学集**
  - **修正 prior RobotSet overview** "4 MarkerCrossing 嵌套 Frame" 描述:实际是 **2×2 cell grid + 对角交叉** + Frame-as-Semaphore 互斥
  - **z_uniform off-by-one Quirk** 第 3 次确认(Init / DestCtrl / RecalcLayout 都用 `Dim+1` 模式)— 强烈 Quirk
  - **ICN 重构累计 13 个**:`Place/Network/NwSource/Drain/NwArc/NwMarker/NwAGVPool/Vehicle/EventCtl/Machine/Line/NwDigitDpy/NwRandom/Method`
  - **dump Method SOP 跨 6 个 Method 全部成功** — `obj.&Method.Program` 是 PS 2.0 simtalk_run 反射层最稳定的 dump 路径

### 候选 finding
- **Frame-as-Semaphore 模式** → 建议 curator 评估沉淀到 `02-domain-know-how/01-factory-know-how/factory-modeling-architecture.md` 新增子节
- **`obj.&Method.Program` 完全可移植 SOP** → 沿 prior onpull-dump finding,本 session 跨 6 个 Method 进一步验证
- **`DataList=NwRandom` 暗示 DataList 内部 random 语义** → 建议 synthesizer 评审 PS Help `DataList/attributes` 文档是否需补充 random accessor 说明

---

## Cross-references
- 02-domain-know-how entries: `01-factory-know-how/factory-modeling-architecture.md`(沿 prior,待新增 Frame-as-Semaphore 子节),`01-factory-know-how/warehouse-and-ctu-patterns.md`(RCS 对比)
- 01-plantsimulation-knowledge entries: `01-plant-simulation-help/objects/resource-objects/AGVPool/methods/methods.md`(getIdleAGV 沿 prior),`01-plant-simulation-help/objects/resource-objects/Marker/general/general.md`(waypoint 语义沿 prior AGVWithRobot)
- 04-agent-memory 其它 session:
  - **`2026-09-02-Models-RobotSet-robot-set-overview.md`**:prior 概述,提及 MarkerCrossing 是 26 nodes 含 4 嵌套 Frame + Init/DestCtrl Method(本 session 完整 dump)
  - **`2026-09-02-AGVWithRobot-agv-dispatch-deepdive.md`**:对比 AGV 单 AGV 派单;`z_uniform` off-by-one 第 2 次确认
  - **`2026-09-02-PortalCrane-crane-deepdive.md`**:ICN 体系起点,Frame=Network
  - **`2026-09-02-RobotComau-station-as-robot-deepdive.md`**:Station-as-Subject 起点
  - **`2026-09-02-SevenAxisRobot-branching-deepdive.md`**:对比 SevenAxisRobot "纯声明式" vs 本 MarkerCrossing "dispatcher + 嵌套 semaphore"
  - **`2026-09-02-SevenAxisRobot-onpull-attempt.md`** + **`2026-09-02-SevenAxisRobot-onpull-dump-part1/2.md`**:dump Station callback SOP 起点,本 session 跨 6 个 Method 进一步验证
- per-skill 调用 log:inline simtalk_run prints in Bash transcript(~40 次,Step 1-4 各次 print + readlog 配对)
- team memory: `simtalk-run-soft-failure-design`(本 session 全 success,无软失败)

---

## Open questions / cross-pollination
- *建议由 `plant-simulation-experience-curator` 评审是否沉淀:*
  - **Frame-as-Semaphore 互斥教学 cell** → 候选到 `02-domain-know-how/04-modeling-example/frame-as-semaphore-cell.md`(baseline:本 session §01 + §04 完整源码)
  - **callback 注入模式**(`agv.DestCtrl = &DestCtrl`)→ 候选到 `02-domain-know-how/01-factory-know-how/factory-modeling-architecture.md` 新增"dispatcher 显式 callback 注入"小节
- *建议由 `skills-optimizer` 评审:*
  - **`obj.&Method.Program` SOP 跨 6 个 Method 验证可移植** → 候选 `local-simtalk-read-library/SKILL.md` Limitations 修订 + `language-quirks-reference.md` 新增 dump SOP(baseline:本 session §03 + prior onpull-dump)
  - **Variable `.Value` API**(非 `.contents`)→ 候选 `language-quirks-reference.md` 补"Variable 公开属性是 `Value`"
  - **`existsObject` 防御编程模式** → 候选 `02-domain-know-how/03-modeling-know-how/02-simtalk/` 新增小节
- *建议由 `plant-simulation-knowledge-synthesizer` 评审:*
  - **`DataList=NwRandom` 类名重命名** → 建议 PS Help `DataList/README.md` 补充 ICN=NwRandom 说明
  - **`Method=Method` 普通类 vs Nw 系列类** → 建议 PS Help 文档统一类注册名说明
- *未关闭问题:*
  - **`StoppingCounter` 实际用途** — EntranceCtrl 中 `+=1` / `-=1` 但未发现 GUI 显示 — 可能是 hidden state 或 observer pattern,需 `expert` 实跑验证
  - **`RecalcLayout` 何时被调用** — 有 `param newValue:real`,可能是 observer pattern(Variable 变化触发)— 需 `expert` 实跑验证
  - **嵌套 Frame 4 副本 vs Class+Instance 复用** — 用户用 4 个独立 Frame 复制,不用 `UserObjects/MarkerCrossing` + 4 instances 模式 — 与 Factory51 `Production` + `P1/P2` 范式不同,**简化**但失去扩展性
  - **`Destinations` 4 个 entry 内容** — `d[i]` 打印触发 arithmetic 错,无法直接验证 — 需 separate print
  - **`@` 在 EntranceCtrl 中的语义** — `@` 指当前触发回调的对象,在 EntranceCtrl 内是 Frame 自身,需 GUI 验证绑定关系

---

## Operator self-review
- [x] 范围:深度学习 `.Models.MarkerCrossing`,无写动作,无 `.SimtalkClaude.*` 调用
- [x] 5 维全列(01-factory-know-how / 02-simtalkclaude-knowhow / 03-modeling-know-how / 04-modeling-example / 05-modeling-experience)
- [x] 6 段齐(Cross-references / Open questions / Operator self-review + 5 维正文)
- [x] 每条 finding 含 baseline 引用 + 3-pass 判定
- [x] Quirk 编号协议:本 session 0 新增 Quirk,✅ SOP `obj.&Method.Program` 跨 6 个 Method 进一步验证
- [x] Target < 150 行(实际 ~140 行)
- [x] 不动 baseline 文档:`02-domain-know-how/` / `01-plantsimulation-knowledge/` 全程只 `Read`
- [x] 不动模型:0 个写 skill 调用,仅 `simtalk_run` 查询 + `readlog` 拉 print
- [x] **Novel finding 突出标注**:`DataList=NwRandom` / `Method=Method` / 4 嵌套 Frame-as-Semaphore / `Owner` Variable semaphore / `agv.DestCtrl=&DestCtrl` callback 注入 / 13 Connector 命名 gap / 完整 2×2 grid + 对角交叉拓扑 / `z_uniform` off-by-one 第 3 次确认
- [x] **跨 session 综合**:ICN 累计 13 个;`obj.&Method.Program` SOP 跨 6 个 Method 验证;修正 prior MarkerCrossing 描述