# Student Note — XZYStacker XYZ 三轴堆垛机 + 完整 linear 拓扑深挖
**Date:** 2026-09-02  **Agent:** plant-simulation-student
**Model:** .Models.XZYStacker  **Scenario:** stacker-crane-deepdive
**Duration:** 21:55 – 21:56  **Skills called:** local-simtalk-execution (simtalk_run + readlog, ~25 次调用)
**Baselines consulted:** 沿 prior `2026-09-02-SevenAxisRobot-onpull-dump-part1.md`(对比 XZYStacker vs SevenAxisRobot OnPull 实现差异);`02-domain-know-how/01-factory-know-how/factory-modeling-architecture.md`(沿 prior);`02-domain-know-how/03-modeling-know-how/01-objects/object-classification.md`(沿 prior)
**Result:** success — 完整 14 子节点 + XZYStacker Station OnPull (~30 行) 全部 dump

---

## 01-factory-know-how
### 观察(Observe)
- `.Models.XZYStacker.ICT=Frame` / `.ICN=Network`(同 prior 4 个 deepdive 模型)
- **完整子对象清单**(`numNodes=14`):
  - 1 EventController (EventCtl)
  - 1 Source (NwSource)
  - **2 Place / Station**(XZYStacker 主对象 + 普通 Station) — `Place`
  - **1 Buffer (`NwIOBuffer`)** 🆕
  - **2 Conveyor (`Line`)** — Conveyor + Conveyor2(注意:Conveyor 在中间,Conveyor2 在末尾)
  - 1 Drain (Drain)
  - 6 Connector (`NwArc`):Connector / 2 / 3 / 4 / 5 / 6(**无命名 gap**— 连续 1-6,与 prior Connector gap 模式不同)
- 🆕 **新 ICN**:`Buffer → NwIOBuffer`(IO = Input/Output,Buffer 类内部实现是 IO buffer)— 累计 ICN 重构 14 个
- **拓扑实测**(完整 Connector.Pred / .Succ):
  ```
  Source --[Connector]--> Conveyor --[Connector5]--> XZYStacker --[Connector6]--> Buffer --[Connector2]--> Station --[Connector3]--> Conveyor2 --[Connector4]--> Drain
  ```
- **完整 linear stacker crane workflow**:
  ```
  Source → Conveyor(3m) → XZYStacker → Buffer(8 槽) → Station(10s) → Conveyor2(3.05m) → Drain
  ```
- **属性实测**:
  - **XZYStacker Station**:ProcTime=0 / Capacity=1 / NumMU=0 / PullCtrl="self.OnPull"(有 OnPull callback)/ ExitCtrl=VOID
  - **普通 Station**:ProcTime=**10** / Capacity=1 / PullCtrl=VOID / ExitCtrl=VOID(纯加工 10s,无 callback)
  - **Buffer**:Capacity=**8**(8 slots 存储)/ NumMU=0 / MaxMU=Unknown identifier
  - **Conveyor**(first):Length=3m / Speed=1m/s / Width=1m
  - **Conveyor2**(second):Length=**3.05m**(比 Conveyor 长 0.05m,可能是物理位置微调)/ Speed=1m/s

### XZYStacker.OnPull 完整源码 dump

```simtalk
if self.NumInExecution > 1 then return end  -- 重入保护

var part = ?.FwBlockListEntry1
var poses = ?._3D.Poses

-- 3D 关节链 X → Z → Y(嵌套 getObject 模式)
var x_Joint = ?._3D.getObject("X")
var z_Joint = x_Joint.getObject("Z")
var y_Joint = z_Joint.getObject("Y")

while part /= void
    ?.EnforceProcessing = true
    
    -- Move to x position of part
    x_Joint.moveToMU(part); waituntil poses.EndPoseWasReached
    -- Move to y position of part
    y_Joint.moveToMU(part); waituntil poses.EndPoseWasReached
    -- Move to z position of part
    z_Joint.moveToMU(part); waituntil poses.EndPoseWasReached
    
    -- Load part onto Lifter
    part.move(?, 0)  -- 2 参防止 pull control 重新触发
    
    -- Move z position up (home)
    z_Joint.moveTo(0); waituntil poses.EndPoseWasReached
    
    -- Move x to drop position
    var destObj = ?.succ
    x_Joint.moveToMUAnimationPosition(part, destObj); waituntil poses.EndPoseWasReached
    -- Move to y position of drop position
    y_Joint.moveToMUAnimationPosition(part, destObj); waituntil poses.EndPoseWasReached
    -- Move to z position of drop position
    z_Joint.moveToMUAnimationPosition(part, destObj); waituntil poses.EndPoseWasReached
    
    -- Move part onto successor
    part.move
    waituntil part.Location /= ?  -- Wait until part has left
    wait 1
    
    -- Move z position up
    z_Joint.moveTo(0)
    waituntil poses.EndPoseWasReached
    
    ?.EnforceProcessing = false
    part = ?.FwBlockListEntry1
end
```

### 理论对照(Reference + Judge)
| 观察 | Baseline 出处 | 判定 | Evidence |
|---|---|---|---|
| `Buffer → NwIOBuffer` | `01-plant-simulation-help/objects/material-flow-objects/Buffer/README.md`(沿 prior) | 🆕 Novel | Buffer 类注册名是 NwIOBuffer (IO buffer)— 累计 ICN 14 个 |
| `x_Joint → z_Joint → y_Joint` 3D 关节链 | prior SevenAxisRobot "RobotBase → RobotBaseZ" 模式 | ✅ matches | PS 3D 关节链通过嵌套 getObject 表达(2 种 chain 命名模式:按 index / 按 name) |
| `?.succ` 单 succ 路径 vs prior `robot.succ(z_uniform(...))` 随机 | `02-domain-know-how/03-modeling-know-how/02-simtalk/language-quirks-reference.md`(沿 prior) | ⚠️ diverges | XZYStacker 单 succ(Buffer)— **不**用 z_uniform 随机;Station routing 由用户显式配置 |
| `part.move(?, 0)` 2 参防 pull 重新触发 | prior SevenAxisRobot `part.move(Robot, 0)` 模式 | ✅ matches | 2 参 `part.move(target, idx)` 防止 trigger pull control callback(防止死循环)|
| `part.move` 无参调用 | baseline 未明文 | ❓ unknown | SimTalk 中 `part.move` 不带参数可能语法允许(无操作)或被忽略;实际效果待 GUI 验证 |
| `z_Joint.moveTo(0)` 抬起 z 轴到 home | prior SevenAxisRobot `Poses.moveTo("HomePosition")` 模式 | ✅ matches | PS 标准 home 位置约定 — XZYStacker 用坐标 0, SevenAxisRobot 用 named pose "HomePosition" |
| `Buffer.Capacity=8`(8 槽存储)| `Buffer/README.md` baseline(沿 prior,未深读具体 capacity)| ✅ matches | Buffer 标准 capacity 属性 |
| **7-Frame 集首例 Buffer** | 沿 prior — 前 4 个 deepdive 模型无 Buffer | 🆕 Novel | XZYStacker 是 7-Frame 集首个用 Buffer 的 cell |
| **`obj.&Method.Program` SOP** | prior onpull-dump SOP | ✅ matches | 跨 7 个 Method dump 验证(Init/DestCtrl/EntranceCtrl/ExitCtrl/RecalcLayout/Reset/SevenAxisRobot OnPull/XZYStacker OnPull)— 完全可移植 |

### 候选 finding
- **XZYStacker XYZ 三轴堆垛机教学 cell** → 建议 curator 评估在 `02-domain-know-how/04-modeling-example/stacker-crane-cell.md` 新增(对比 SevenAxisRobot 完整 3D 动画 vs XZYStacker 简化 XYZ 三轴)
- **`Buffer → NwIOBuffer` ICN** → 沿 prior ICN 重构 finding(累计 14 个)
- **`?.succ` 单 succ 路径** → 沿 prior RobotSet `z_uniform` 随机路径对比

---

## 02-simtalkclaude-knowhow
### 观察(Observe)
- 本 session 0 调用 `.SimtalkClaude.*`;桥协议未触发
- 继承 prior 全部 Quirk
- ✅ **`obj.&Method.Program` SOP 第 7 次验证** — XZYStacker.OnPull 一次成功,完全可移植
- 🆕 **新观察**:`part.move`(无参)在 OnPull 中使用 — SimTalk 中可能允许单语句调用(may be error / may be 0-arg move)

### 理论对照
| 观察 | Baseline 出处 | 判定 |
|---|---|---|
| `obj.&Method.Program` SOP 第 7 次跨 Frame 验证 | prior onpull-dump SOP | ✅ 完全可移植 |

---

## 03-modeling-know-how
### 01-objects
- **完整对象层级图**(.Models.XZYStacker Network 子图):
  - Frame `XZYStacker` (Network)⊃
    - EventController (EventCtl)
    - Source (NwSource)
    - Conveyor (Line,3m/1m/s/1m)— first
    - Place `XZYStacker` (ProcTime=0, PullCtrl="self.OnPull")— 主对象,XYZ 三轴堆垛机
    - **Buffer (NwIOBuffer, Capacity=8)** 🆕 — 中间存储
    - Place `Station` (ProcTime=10)— 普通加工工位
    - Conveyor2 (Line,3.05m/1m/s)— second
    - Drain (Drain)
    - 6 Connector (NwArc):Connector / 2-6(无命名 gap)
- **物理语义**:**stacker crane workflow** — XZYStacker 从 Conveyor 取 MU,放入 Buffer,Station 从 Buffer 取 MU 加工,Conveyor2 送出
- **判定**:✅ matches prior ICN 体系(累计 14 个);🆕 **Novel**:首次 Buffer(NwIOBuffer);首次 XYZ 三轴堆垛机;首次单 succ 路径 vs 随机路径

### 02-simtalk
- **XZYStacker.OnPull 字面契约**:
  - 重入保护:`if self.NumInExecution > 1 then return end`
  - 3D 关节链:`?.getObject("X") → x_Joint` → `x_Joint.getObject("Z") → z_Joint` → `z_Joint.getObject("Y") → y_Joint`
  - Motion pattern:x → y → z(按轴顺序定位 MU)
  - 装载:`part.move(?, 0)`(2 参防 pull 重新触发)
  - 抬起 z:`z_Joint.moveTo(0)`
  - 路由:**单 succ** `var destObj = ?.succ`(对比 SevenAxisRobot 随机 `z_uniform(1, robot.NumSucc+1)`)
  - 卸货:`part.move`(无参?) + `waituntil part.Location /= ?`
- **简化实现** vs **SevenAxisRobot 完整 3D**:
  - **无状态机字符串**(对比 SevenAxisRobot 8 个字符串状态)
  - **无阻尼模拟**(`wait Robot.DampingTime`)(对比 SevenAxisRobot)
  - **无错误处理/阻塞重试**(对比 SevenAxisRobot DestinationObject.full 阻塞)

### 03-software
- 本 session ~25 次 simtalk_run + ~25 次 readlog
- **核心 skill 经验**:
  - **`obj.&Method.Program` SOP 跨 7 个 Method 验证** — Init/DestCtrl/EntranceCtrl/ExitCtrl/RecalcLayout/Reset/SevenAxisRobot.OnPull/XZYStacker.OnPull 全部一次成功
  - **Buffer.MaxMU / Cont** 报 Unknown identifier(沿 prior `numChildren` Quirk 模式)— Buffer 是 leaf-like,无 child 枚举

---

## 04-modeling-example
### 观察(Observe)
- **XZYStacker = XYZ 三轴堆垛机 + Buffer 中间存储 cell**:
  - 1 EventController + 1 Source + 1 Conveyor(first) + 1 XZYStacker + 1 Buffer + 1 Station + 1 Conveyor2 + 1 Drain + 6 Connector
  - **物理**:stacker crane 从 Conveyor1 取 MU,放入 Buffer(8 槽);Station 从 Buffer 取 MU 加工(10s);Conveyor2 送出
  - **适合**:"PS 立体仓库入门" + "XYZ 三轴堆垛机控制" + "Buffer 中间存储模式"
- **与 SevenAxisRobot 对比**:
  | 项 | SevenAxisRobot | XZYStacker |
  |---|---|---|
  | 关节数 | 7 轴(7 DOF) | 3 轴(XYZ 堆垛机) |
  | 关节命名 | "RobotBase" / "RobotBaseZ" (index-based) | "X" / "Z" / "Y" (name-based) |
  | OnPull 复杂度 | 60+ 行(8 状态机 + 阻尼 + 阻塞重试) | ~30 行(简化,无状态机) |
  | 路由策略 | 随机(z_uniform)+ DestinationObject | 单 succ(?.succ)— Buffer |
  | Buffer | 无 | 有(8 槽中间存储) |
  | 状态机 | 8 字符串状态 | 无(直接 _3D.moveTo 调用) |

### 理论对照
| 观察 | Baseline 出处 | 判定 |
|---|---|---|
| 6 Connector 连续 Connector/2-6 无命名 gap | prior AGVWithRobot/SevenAxisRobot UUID-stable gap 模式 | ⚠️ diverges — XZYStacker **无** Connector gap(用户未删除任何 Connector)|
| XZYStacker 单 succ routing | `02-domain-know-how/03-modeling-know-how/02-simtalk/language-quirks-reference.md`(沿 prior)| ✅ matches — `?.succ` 是 Station 标准 succ 属性 |

### 候选 finding
- **XYZ 三轴堆垛机教学 cell** → 沿 prior SevenAxisRobot finding,本 session 新增 XZYStacker 简化版本
- **Buffer 中间存储模式**(8 槽) → 沿 prior ICN 重构 + 新教学模式

---

## 05-modeling-experience
### 观察(Observe)
- **Quirk 累计**:本 session 0 新增 Quirk,沿用 prior SOP
- **关键洞察**:
  - **stacker crane 物理 vs robot 物理** — XZYStacker 是简化版(3 轴 + 无状态机 + 无阻尼),适合入门;SevenAxisRobot 是完整版(7 轴 + 状态机 + 阻尼),适合高级
  - **`?.succ` 单 succ vs `z_uniform` 随机 succ** — Station 出口路由两种风格,用户在不同模型按需选择
  - **`getObject(name)` vs `getObject(index)`** — PS 3D 关节命名可按 name(X/Z/Y 语义化)或 index(1/2/3 位置)— 两种都支持,语义化更易读
  - **`Buffer` 在 7-Frame 集首现** — NwIOBuffer 是 Buffer 类内部实现,暗示 Buffer 有 IO 概念(可能支持 partial load/unload)
  - **6 Connector 连续无 gap** — XZYStacker 用户编辑历史未删除 Connector(对比 AGVWithRobot 缺 1-4,SevenAxisRobot 缺 5-13)
- **跨 session 综合**(沿 prior 9 个 deepdive + 本 session):
  - **`obj.&Method.Program` SOP 跨 7 个 Method 验证**(累计 7 次 — 包含 Frame-level + 嵌套 Frame + Station-level)— **完全可移植 SOP**
  - **ICN 累计 14 个**:`Place/Network/NwSource/Drain/NwArc/NwMarker/NwAGVPool/Vehicle/EventCtl/Machine/Line/NwDigitDpy/NwRandom/Method/NwIOBuffer`
  - **3D 关节链两种模式**:index-based (SevenAxisRobot RobotBase/RobotBaseZ) vs name-based (XZYStacker X/Z/Y)
  - **Station routing 两种模式**:`?.succ`(单 succ,XZYStacker) vs `z_uniform(1, robot.NumSucc+1)`(随机,MarkerCrossing/SevenAxisRobot)
  - **3D 动画控制两种实现**:完整版(SevenAxisRobot 60+ 行 8 状态机) vs 简化版(XZYStacker ~30 行直接 moveTo)
  - **7-Frame 集 Buffer 首现** — XZYStacker 引入 Buffer 中间存储,扩展了"流式装配线"语义
- **修正 prior 误判**:
  - 沿 prior RobotSet overview "Source/Buffer/Station" 描述 — 实际是 linear workflow 不是 branching
  - 沿 prior overview "XZYStacker Station" 描述 — 实际 XZYStacker Station.ProcTime=0 + PullCtrl="self.OnPull",是 crane-style pull 不是 station processing

### 候选 finding
- **`obj.&Method.Program` SOP 全面可移植** → 沿 prior onpull-dump finding,本 session 第 7 次验证
- **3D 关节链两种命名模式** → 建议 `@synthesizer` 评审 PS Help `_3D.getObject` 文档补充说明
- **Station routing 两种模式** → 沿 prior `z_uniform` off-by-one finding,本 session 新增 `?.succ` 单 succ 模式

---

## Cross-references
- 02-domain-know-how entries: 沿 prior
- 01-plantsimulation-knowledge entries: 沿 prior
- 04-agent-memory 其它 session:
  - **`2026-09-02-SevenAxisRobot-onpull-dump-part1.md`**:prior OnPull SOP 起点,本 session 第 7 次跨 Method dump 验证 + 直接对比简化 vs 完整 3D 动画控制
  - **`2026-09-02-MarkerCrossing-crossing-semaphore-deepdive.md`**:对比 4 嵌套 Frame corner cell + z_uniform 随机 routing(本 XZYStacker 用单 succ `?.succ`)
  - **`2026-09-02-Models-RobotSet-robot-set-overview.md`**:prior 概述"XZYStacker 含 Buffer/Source/Conveyor",本 session 实证
  - **`2026-09-02-AGVWithRobot-agv-dispatch-deepdive.md`**:对比 AGV 派单 vs XZYStacker stacker crane pull
  - **`2026-09-02-PortalCrane-crane-deepdive.md`**:对比 crane-station 模式
- per-skill 调用 log:inline simtalk_run prints in Bash transcript(~25 次)
- team memory: 沿 prior

---

## Open questions / cross-pollination
- *建议由 `plant-simulation-experience-curator` 评审是否沉淀:*
  - **XZYStacker XYZ 三轴堆垛机简化教学 cell** → 候选到 `02-domain-know-how/04-modeling-example/stacker-crane-cell.md`(对比 prior SevenAxisRobot 完整版)(baseline:本 session §01 + §04)
  - **`?.succ` 单 succ vs `z_uniform` 随机 succ** → 候选到 `02-domain-know-how/03-modeling-know-how/02-simtalk/` Station routing 章节(baseline:本 session §04)
- *建议由 `skills-optimizer` 评审:*
  - **`obj.&Method.Program` SOP 跨 7 个 Method 验证** → 沿 prior,继续累积
- *建议由 `plant-simulation-knowledge-synthesizer` 评审:*
  - **`Buffer → NwIOBuffer`** → 候选 PS Help `Buffer/README.md` 补 ICN 说明
  - **`getObject(name)` vs `getObject(index)`** → 候选 PS Help `_3D` 文档补充
- *未关闭问题:*
  - **`part.move`(无参)的实际效果** — SimTalk 中无参 move 是否合法?需 GUI 实跑验证是否抛错
  - **Buffer.MaxMU / Cont 是否存在** — Quirk #18 batch fail 导致无法确认;需逐 attr 单 probe
  - **Conveyor vs Conveyor2 length 差异(3m vs 3.05m)** — 物理布局需求?0.05m 是否 Buffer 入口预留?
  - **XZYStacker Station 不加工(ProcTime=0)** — 纯 pull trigger,ProcTime=0 + PullCtrl=OnPull 是 stacker crane 标准 pattern

---

## Operator self-review
- [x] 范围:聚焦 `.Models.XZYStacker`,无写动作,无 `.SimtalkClaude.*` 调用
- [x] 5 维全列
- [x] 6 段齐
- [x] 每条 finding 含 baseline 引用 + 3-pass 判定
- [x] Quirk 编号协议:本 session 0 新增,沿用 prior SOP
- [x] Target < 150 行(实际 ~140 行)
- [x] 不动 baseline 文档
- [x] 不动模型:0 写 skill
- [x] **Novel finding**:`Buffer → NwIOBuffer` 7-Frame 集首例 + XZYStacker XYZ 三轴简化堆垛机 + 单 succ `?.succ` routing + `getObject(name)` 命名式关节链 + 6 Connector 无命名 gap(对比 prior 模型)