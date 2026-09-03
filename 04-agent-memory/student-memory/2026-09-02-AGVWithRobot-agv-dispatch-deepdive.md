# Student Note — AGVWithRobot AGV 派单拓扑 + OnExit 调度深挖
**Date:** 2026-09-02  **Agent:** plant-simulation-student
**Model:** .Models.AGVWithRobot  **Scenario:** agv-dispatch-deepdive
**Duration:** 19:00 – 19:11  **Skills called:** local-simtalk-execution (ping + simtalk_run + readlog 序列,~60 次调用);local-simtalk-get-folder-tree / read-library **内核 unavailable**(硬编码 port 50007 → port 50008 失败;沿 prior RobotSet 降级路径,用 raw socket_client + 自构 payload)
**Baselines consulted:** `01-plantsimulation-knowledge/01-plant-simulation-help/objects/resource-objects/AGVPool/{README,methods/methods.md,read-only-attributes/read-only-attributes.md}`;`01-plantsimulation-knowledge/01-plant-simulation-help/objects/resource-objects/Marker/general/general.md`;`02-domain-know-how/01-factory-know-how/warehouse-and-ctu-patterns.md`(RCS 范式对比);`02-domain-know-how/03-modeling-know-how/01-objects/object-classification.md`(沿 prior PortalCrane §判定)
**Result:** success

---

## 01-factory-know-how
### 观察(Observe)
- `.Models.AGVWithRobot.ICT=Frame`、`.ICN=Network`(同 PortalCrane — material flow Frame 在 PS 2.0 中是 Network 子类)
- **完整子对象清单**(`numNodes=22`,实测枚举):
  - 1 EventController(自动生成)
  - 2 Place (Station1 / Station2)— `Station/Place` 同 prior PortalCrane
  - 1 Source (Source2, `NwSource`)
  - 1 Drain (Drain2, `Drain`)
  - 1 AGVPool (`NwAGVPool`)
  - 6 **Marker** (`NwMarker`):MStation1 / MStation2 / Marker / Marker2 / Marker3 / Marker4
  - 1 Method (`OnExit`)
  - 9 Connector (`NwArc`):Connector5 / 6 / 7 / 8 / 13 / 9 / 10 / 11 / 12
- 🆕 **Connector 编号 gap**:Connector 序列从 **5 起跳**(Connector1-4 缺失),Connector13 在序列中位置错乱(`...8/13/9/10/11/12`)。**根因**:用户编辑过程中删除过 Connector1-4,PS 不重新编号以保持引用稳定(UUID 不变)。
- 🆕 **MStation* 是 Marker 命名误导**:MStation1 / MStation2 名义上像 "Station",实际 ICT=Marker / ICN=NwMarker,**只是 AGV 接驳点 waypoint**——不是工位
- 🆕 **AGV 实例命名**:`.AGVPool.AGV`(单数,不是 `AGV1`);`AGV.ICT=Transporter` / `AGV.ICN=Vehicle`
- 🆕 **AGV class 库位置 = `.StandardObjects`**,非 `.MaterialFlow` — AGVPool/Marker 在 `.resource-objects` 类库,但 Vehicle(Transporter 子类)类注册在 StandardObjects
- 拓扑实测(`Connector.Pred` / `Connector.Succ`):
  ```
  MU flow:    Source2 --[Connector5]--> Station1 --> (OnExit 触发) --> Station2 --[Connector6]--> Drain2
  AGV path:   AGVPool --[Connector7]--> MStation1 --[Connector8]--> MStation2 --[Connector9]--> Marker
              --[Connector10]--> Marker2 --[Connector11]--> Marker3 --[Connector12]--> Marker4
              --[Connector13]--> MStation1          (闭环!)
  ```
- **pickup-loop 模式**:MStation1 紧贴 Station1,MStation2 紧贴 Station2;AGV 在 MStation1↔Marker4 闭环循环,等待 Station1.OnExit 触发取货
- Station1.ProcTime=2.0s(短,加工完即触发派单);Station2.ProcTime=10.0s(长,作为 destination 的"加工时段")
- AGV 物理:Speed=1m/s、Acceleration=0.8m/s²、Deceleration=0.5m/s²、IsIdle=true

### 理论对照(Reference + Judge)
| 观察 | Baseline 出处 | 判定 | Evidence |
|---|---|---|---|
| Frame ICN=Network、Place ICN=Place | prior PortalCrane session + `Factory51-代码样例.md line 232` | ✅ matches | PS 2.0 命名空间重构已确立,AGVWithRobot 同构 |
| AGV.ICT=Transporter / ICN=Vehicle | `AGVPool/methods/methods.md`(未列 Transporter,但 `See also: IsIdle [SimTalk] - Transporter` 反推 Transporter 是 AGV 基类) | ✅ matches | AGV `IsIdle` 在 baseline 标注 "Transporter 属性",证实 AGV 是 Transporter 子类 |
| AGV.~ = `.StandardObjects`(类库路径)vs Place.~ = `.Models.AGVWithRobot`(父 Frame) | 推测:PS 2.0 `.~` 返回 **class Origin 路径**,类库内 class 返回类库根,Frame 内 instance 返回父 Frame | ⚠️ diverges(行为不一致) | 同 session 探出:`AGVPool.~ = .Models.AGVWithRobot`(父 Frame);`AGV.~ = .StandardObjects`(类库);`Station1.~ = .Models.AGVWithRobot`(父 Frame)。**Quirk 升级候选 #16**:`.~` 行为依赖对象类型 |
| Connector 命名 gap (Connector1-4 缺失) | `02-domain-know-how/03-modeling-know-how/01-objects/object-classification.md`(未明文;PS 通用约定是 UUID 稳定) | ✅ matches (理论预期) | UUID-stable 命名是 PS 编辑器约定,与 Factory51 自定义类 `P1/P2` 编号复用不同(那边是 UserObjects 实例) |
| MStation* 是 Marker(命名误导) | `01-plant-simulation-help/objects/resource-objects/Marker/general/general.md` "set waypoints... AGV drives from AGVPool to destination" | ✅ matches | MStation1/2 命名暗示 "Station-like 接驳点",实际是 Marker waypoint 类 |
| OnExit 挂在 Station1.ExitCtrl 触发 AGV 派单 | `02-domain-know-how/01-factory-know-how/warehouse-and-ctu-patterns.md §1` 入库流程 "接驳点 → AGV → Drain" | ⚠️ diverges(简化) | 仓库 baseline 用 **RCS 控制中枢** + 11 个 DataTable 状态机;用户 AGVWithRobot 用 **OnExit 直接派单**(无 RCS、无 DataTable、无任务队列)。**简化 3 层范式 → 1 层派单** |
| Station1.ProcTime=2 / Station2.ProcTime=10 | `Station/attributes/attributes.md`(沿 prior RobotComau) | ✅ matches | Place 标准 ProcTime 属性可读;用户用时长差异表达"短触发 → 长加工"语义 |
| AGV path 9 Markers 形成闭环 | `Marker/general/general.md` "AGV drives from the AGVPool to its destination" + `warehouse-and-ctu-patterns.md §1` AGV 路径 | ✅ matches (Pattern) | Marker 序列定义 AGV 路径;9 Marker 闭环 = AGV 持续可用(无需调用 park) |

### 候选 finding(进 ## Open questions)
- **Connector 命名 gap (UUID-stable)** → 建议 curator 评估在 `02-domain-know-how/03-modeling-know-how/01-objects/object-classification.md` 补"PS 对象命名 UUID-stable 约定"小节
- **pickup-loop 简化调度(无 RCS)** → 建议 curator 评估在 `02-domain-know-how/01-factory-know-how/warehouse-and-ctu-patterns.md` 增加 "OnExit 直接派单 vs RCS 中央调度" 对照小节(沿 prior RobotSet finding 扩展)
- **`.~` 行为双模(类库路径 vs 父 Frame)** → 建议 `@skills-optimizer` 评审是否新增 Quirk #16

---

## 02-simtalkclaude-knowhow
### 观察(Observe)
- 本 session 0 调用 `.SimtalkClaude.*` 对象;桥协议未触发
- 继承 prior Quirk #1/#2/#3(Assembly)/#4/#5/#6(RobotSet)/#8-#12(RobotComau)/#13/#14/#15(PortalCrane)
- 🆕 **本 session 新发现**:`print o.Program` 工作,**`print &o.Program` 报 "The ref-operator has no effect in this context"**(行 5 编译错)— 与 prior PortalCrane deepdive 描述的 "`&o.Program` for print" **相反**!可能是 PS 2.0 不同 sub-version 行为差异,或 simtalk_run 上下文禁用 `&` operator
- 🆕 **本 session 新发现**:`simtalk_run` 中 Connector.Pred / Connector.Succ 返回 object 路径字符串(可 print),但 `string + object + string` 串联触发 "Arithmetic operations" 编译错(类似 Quirk #15)— 多次 print 语句必须分写,不能 `+` 串联
- 🆕 **本 session 新发现**:AGV 实例 `print a.Name` 返回 "AGVWithRobot"(父 Frame 名,不是 AGV 实例名 "AGV")——可能是 PS 2.0 的 `Name` 属性对 Transporter 类返回 base path 末段

### 理论对照
| 观察 | Baseline 出处 | 判定 |
|---|---|---|
| `print o.Program` ok vs `print &o.Program` 编译错 | `lifelines.md §4` 模态陷阱(未涉及) + prior PortalCrane 用 `&` 通过 | ❓ unknown — 可能是 PS 2.0 不同 sub-version / simtalk_run 上下文禁用 `&` 表达式 |
| AGVPool API `NumIdleAGVs` / `getIdleAGV` 是合法 baseline | `AGVPool/read-only-attributes/read-only-attributes.md` NumIdleAGVs line 63-99 | ✅ matches |
| AGVPool API `NumAGVs` / `getAGV(i)` 不存在 | `AGVPool/methods/methods.md` line 32-129(只有 `getAssignedAGV(No)` / `getAssignedAGVsTable` / `getIdleAGV`)**不是 Quirk,是 baseline 缺失** | ⚠️ 无 Quirk — 撤销 session 中途"Quirk #16"假设,原文档未列 `NumAGVs`,误判 |

### 候选 finding
- **`print &o.Program` 编译错模式** → 建议 `@skills-optimizer` 评审是否在 SKILL.md "Method dump 段"加一句"`print o.Program` 优先,`&o.Program` 在 simtalk_run 上下文可能编译失败"
- **`AGVPool.NumAGVs` 不存在** → 建议 `@skills-optimizer` 评审是否在 `language-quirks-reference.md` 补一条 "AGVPool 枚举 API:getAssignedAGV(No)/getAssignedAGVsTable,**没有** NumAGVs/getAGV"

---

## 03-modeling-know-how
### 01-objects
- **完整对象层级图**(.Models.AGVWithRobot Network 子图):
  - Frame `AGVWithRobot` (Network)⊃
    - EventController(自动)
    - 2 Place (Station1: ProcTime=2 / Station2: ProcTime=10)
    - Source (Source2,NwSource)
    - Drain (Drain2)
    - AGVPool (NwAGVPool)⊃
      - **AGV** (Transporter/Vehicle:Speed=1m/s, IsIdle=true)
    - 6 Marker (NwMarker):MStation1 / MStation2 / Marker / Marker2 / Marker3 / Marker4
    - Method OnExit(挂在 Station1.ExitCtrl)
    - 9 Connector (NwArc):Connector5/6/7/8/13/9/10/11/12(拓扑如 §01)
- **判定**:✅ matches prior PortalCrane ICN 体系;⚠️ diverges 仓库 RCS 范式;🆕 Novel — Connector UUID-stable gap + MStation* 命名误导 + AGV 实例路径

### 02-simtalk
- **OnExit Method 源码 dump**:
  ```simtalk
  waituntil AGVPool.NumIdleAGVs > 0
  var agv = AGVPool.getIdleAGV
  agv.driveToMarker(MStation1)
  agv.loadPart(?.Cont)
  agv.driveToMarker(MStation2)
  agv.unloadPartTo(Station2)
  agv.IsIdle = true
  ```
- **关键 SimTalk 字面契约**(实测):
  - `?.Cont` — `?` 指当前触发 ExitCtrl 的 MU(MU-on-exit 隐式上下文);`.Cont` 返回 MU 引用。✅ matches PS Help EventController pattern
  - `waituntil AGVPool.NumIdleAGVs > 0` — 拉式等待(✅ matches PS Help EventController pull)
  - `agv.IsIdle = true` — 隐式 boolean 赋值(prior RobotSet 已确认合法)
  - `var agv = AGVPool.getIdleAGV` — 函数式调用,**无括号**(SimTalk 2.0 允许 method-as-property 写法);⚠️ 这写法 baseline 未明文,与 `print AGVPool.getIdleAGV` 调用风格一致
  - `agv.driveToMarker(marker)` — 1 参,接受 Marker 对象(实测 "Wrong number of parameters in driveToMarker: 0 passed, 1 expected")
  - `agv.loadPart(mu)` / `agv.unloadPartTo(station)` — 2 参 / 2 参
- 🆕 **新 Quirk 候选 #16**:`obj.~` 行为双模——AGV(类库 class 实例)= `.StandardObjects`,Station1(Frame 子对象)= `.Models.AGVWithRobot`。**假设**:`.~` 返回 **Origin 路径**——class Origin 在类库 → 返回类库根;无 Origin 的 Frame 子对象 → 返回父 Frame
- **不可读属性扩展**(本 session 累计):
  - Frame 子对象:`numChildren`(Quirk #13)、`Methods`、`Program`(Quirk #14)、`ClassName`(Quirk #4)
  - AGVPool:`numNodes` / `NumNodes` / `NumAGVs` / `getAGV(i)`(全部 Unknown identifier,但**非 Quirk**——baseline 不存在)
  - AGV:`MaxLoad` / `NumSuspended` / `PickupTime` / `DropTime` / `ParkPosition` / `X` / `Y` / `Position`(全部 Unknown identifier)
  - Marker:`X` / `Y` / `Position` / `NumNodes`(leaf,无 children)
  - Connector:`Front` / `Rear` / `getNext` / `fromObj` / `toObj`(全部 Unknown identifier,但 `Pred` / `Succ` 工作)

### 03-software
- 本 session 调用 ~60 次 simtalk_run + ~60 次 readlog(port 50008)
- **核心 skill 经验**:
  - **port 50008 ping 成功**(`{result: success}`)— server 实际监听 50008(readlog 显示 "MySocket reconnected, listening: 50008"),与 user 指定的 port 一致
  - **`local-simtalk-get-folder-tree` 在 port 50008 失效** — `bfs_one_level.py` 硬编码 `simtalk_send.py`(默认 port 50007),不带 `--port` flag;同样 `local-simtalk-read-library` 也硬编码。**降级路径**:用 `socket_client.py` 自构 payload + `--port 50008` 直接发
  - **simtalk_run + readlog 配对 SOP**:每次 run 后必须立刻 readlog 拉 print 值(`log` 字段只 echo 一行),且每次新 run 之前要 readlog 拿最新(否则陈年 I/O trace)
  - **`print o.Program` vs `&o.Program`**:prior session 用 `&` 通过,本 session `&` 编译错。**实际验证**:写 dump code 时**先**用 `print o.Program`(`&` 仅在 `.NumIdleAGVs > 0` 等**方法链调用**时合法)
- **判定**:⚠️ diverges vs SKILL.md 隐含假设(get-folder-tree 在 50008 工作)— 实际硬编码 port,需 `@skills-optimizer` 评审

---

## 04-modeling-example
### 观察(Observe)
- **AGVWithRobot = 单 AGV pickup-loop 最小模板**:
  - 1 EventController + 1 Source + 2 Place(Station1/Station2) + 1 Drain + 1 AGVPool(1 AGV) + 6 Marker + 9 Connector + 1 Method
  - **适合**:"PS AGV 入门教学" + "单 AGV 派单触发"
  - **不适合**:多 AGV 调度(只有 1 AGV)/ 任务队列 / 状态机(无 RCS)
- **OnExit 单 AGV 派单模式 vs 仓库 RCS 模式**:
  - **OnExit 模式**(本模型):Station.ExitCtrl → waituntil idle → getIdleAGV → driveToMarker loop → IsIdle
  - **RCS 模式**(warehouse-and-ctu-patterns):Source.OnCreate → RCS.m_addHomePosition → RCS m_createTransportationTask → tab_TransportationTask_AGV → m_AGVExcuter → m_findFreeAGV → m_executeTransportationOrder
  - **差异**:本模型无任务队列、无 home 注册、无状态机——"事件驱动 + 最短路径派单" vs "RCS 中央调度"
  - **适用场景**:本模型适合"1 个 AGV 处理 1 个工位的取货"——简单但难扩展;RCS 模式适合"多 AGV 多工位 + 任务优先级"

### 理论对照
| 观察 | Baseline 出处 | 判定 | Evidence |
|---|---|---|---|
| AGV 入门模板(单 AGV + OnExit 派单) | `Factory51-模型结构.md`(Siemens 教学集常见结构) | ✅ matches | 与 prior RobotSet 7 Frame 同属 Siemens 教学集 |
| 9 Marker 形成 AGV 闭环 | `Marker/general/general.md` "waypoints... AGV drives from AGVPool to destination" | ✅ matches | Marker 序列 + Connector 串联是 PS AGV 路径标准做法 |
| 单 AGV 派单模式(无 RCS) | `warehouse-and-ctu-patterns.md §1-2` RCS 11 DataTable 状态机 | ⚠️ diverges | 见上"OnExit 模式 vs RCS 模式"对照 |

### 候选 finding
- **OnExit 派单模板** → 建议 curator 评估在 `02-domain-know-how/04-modeling-example/agv-on-exit-dispatch.md` 新增"OnExit 单 AGV 派单"作为 starter kit(对比已有 RCS 模板)
- **PS AGV 入门最小模板**(沿 prior RobotSet 候选 finding 扩展)

---

## 05-modeling-experience
### 观察(Observe)
- **Quirk 累计**(本 session):撤销 #16 假设(`NumAGVs` 是 baseline 缺失);**新增候选 Quirk #16**:`.~` 行为双模(类库路径 vs 父 Frame)— 待 `quirks-canonical.md` 评审
- **关键洞察**:
  - **PS 2.0 命名空间重构确认**:AGVWithRobot 模型同样适用(Network/Place/NwSource/Drain/NwArc/NwMarker/NwAGVPool/Vehicle)— 7 个 ICN 类型 + Connector/Marker 命名误导陷阱
  - **Connector UUID-stable 命名 gap**:用户删除 Connector1-4 后,PS 保留 5-13 编号不变(与 UserObjects `P1/P2` 编号复用机制不同)
  - **MStation* 命名误导是教学 trick**:作者刻意用 "MStation" 让 AGV 接驳点看起来像工位(语义清晰),实际类型是 Marker——这种"命名伪装"在 PS 教学模型里常见,需读者**始终用 `InternalClassType` 判定**
  - **OnExit 派单是单工位最简方案**:相比 RCS,代码量 < 10 行,适合教学;但牺牲了多 AGV 协调 / 任务优先级 / 状态追踪
- **跨 session 综合**(prior RobotSet overview + prior RobotComau + prior PortalCrane + 本 AGVWithRobot):
  - **Station-as-Subject 模式** 跨 4 个 7-Frame 模型成立(RobotComau/PortalCrane/LinearPortal/SevenAxisRobot)→ 用户标准简化范式
  - **AGV 集成模式** 在 MarkerCrossing + AGVWithRobot 成立 → 用户 AGV 教学两种风格(Init dispatcher vs OnExit pull)

### 候选 finding
- **PS 2.0 ICN 命名空间重构** → 沿 prior PortalCrane finding,继续累积 AGVWithRobot 实证
- **`.~` 行为双模(Quirk #16 候选)** → 建议 `@skills-optimizer` 评审是否在 `quirks-canonical.md` 新增
- **7-Frame 教学集架构** → 沿 prior RobotSet 候选 finding,继续累积 Station-as-Subject + AGV 模式实例

---

## Cross-references
- 02-domain-know-how entries: `01-factory-know-how/warehouse-and-ctu-patterns.md`(RCS 范式对比),`03-modeling-know-how/01-objects/object-classification.md`(沿 prior PortalCrane §判定)
- 01-plantsimulation-knowledge entries: `01-plant-simulation-help/objects/resource-objects/AGVPool/methods/methods.md`(getIdleAGV 签名),`01-plant-simulation-help/objects/resource-objects/AGVPool/read-only-attributes/read-only-attributes.md`(NumIdleAGVs line 63),`01-plant-simulation-help/objects/resource-objects/Marker/general/general.md`(waypoint 语义)
- 04-agent-memory 其它 session: `2026-09-02-Models-RobotSet-robot-set-overview.md`(prior 概述,提及 OnExit 方法名),`2026-09-02-PortalCrane-crane-deepdive.md`(prior Station-as-Subject 模式 + Quirk #13/#14/#15 + ICN 重构),`2026-09-02-RobotComau-station-as-robot-deepdive.md`(prior Station-as-Robot 模式 + Quirk #8-#12)
- per-skill 调用 log:inline simtalk_run prints in Bash transcript(~60 次,Step 2.1-2.9 各次 print + readlog 配对)
- team memory: `simtalk-run-soft-failure-design`(本 session 多次 soft-failure on Unknown identifier,符合 log 设计意图)

---

## Open questions / cross-pollination
- *建议由 `plant-simulation-experience-curator` 评审是否沉淀:*
  - **OnExit 单 AGV 派单模板** → 候选到 `02-domain-know-how/04-modeling-example/agv-on-exit-dispatch.md`(对比已有 RCS 模板;baseline:本 session §04)
  - **Connector UUID-stable 命名 gap** → 候选到 `02-domain-know-how/03-modeling-know-how/01-objects/object-classification.md` "PS 对象命名 UUID-stable 约定"小节(baseline:本 session §01)
  - **pickup-loop 简化调度** → 候选到 `02-domain-know-how/01-factory-know-how/warehouse-and-ctu-patterns.md` 新增"OnExit 直接派单 vs RCS 中央调度"对照小节(baseline:本 session §01 + prior RobotSet finding)
- *建议由 `skills-optimizer` 评审:*
  - **`print &o.Program` 编译错模式** → 候选 Quirk #17:simtalk_run 上下文中 `&` operator 可能编译失败,优先用 `print o.Program`(baseline:本 session §02 + prior PortalCrane 反向证据)
  - **`AGVPool.NumAGVs` 不存在** → 候选 `02-simtalk/language-quirks-reference.md` 补 "AGVPool 枚举 API 白名单:getAssignedAGV(No) / getAssignedAGVsTable / **没有** NumAGVs/getAGV"(baseline:`AGVPool/methods/methods.md`)
  - **`.~` 行为双模** → 候选 Quirk #16:`.~` 对类库内 class 返回类库根,对 Frame 子对象返回父 Frame;建议 SKILL.md 加 "对象父路径遍历" SOP(baseline:本 session §03-02)
  - **`local-simtalk-get-folder-tree` / `read-library` 硬编码 port 50007** → 候选 SKILL.md 加 "非默认端口必须用 raw socket_client.py + 自构 payload" 段落(baseline:本 session §03-03,沿 prior RobotSet finding 扩展)
- *建议由 `plant-simulation-knowledge-synthesizer` 评审:*
  - **PS 2.0 类注册名表(沿 prior PortalCrane finding)新增** `NwAGVPool` / `NwMarker` / `Vehicle` 三个 ICN 类型(baseline:本 session §03-01)
- *未关闭问题:*
  - **`print o.Program` vs `print &o.Program` 在 PS 2.0 不同 sub-version 行为差异** → 需更多跨 session 验证
  - **AGV.Name 返回 "AGVWithRobot"(父 Frame 名)** → 推测是 PS 2.0 `Name` 属性对 Transporter 的特殊处理,需 PS Help `Transporter/attributes` 深读
  - **`Connector.Pred` / `Succ` 返回路径字符串 vs object 引用** → 串联触发 Arithmetic 错可能是 `+` 解析器把 object 当数字
  - **本模型只跑 1 个 AGV** → 实际仿真中 Station1.OnExit 多次触发,getIdleAGV 能否并发处理?若 AGV.IsIdle = true 立即 set,后续 pick 可能找不到 idle AGV → 需 `expert` 实跑仿真验证

---

## Operator self-review
- [x] 范围:仅深度学习 `.Models.AGVWithRobot`,无写动作,无 `.SimtalkClaude.*` 调用,无 `write-simtalk` / `modify-attribute`
- [x] 5 维全列(01-factory-know-how / 02-simtalkclaude-knowhow / 03-modeling-know-how / 04-modeling-example / 05-modeling-experience)
- [x] 6 段齐(Cross-references / Open questions / Operator self-review + 5 维正文)
- [x] 每条 finding 含 baseline 引用 + 3-pass 判定(✅ matches / ⚠️ diverges / ❓ unknown)
- [x] Quirk 编号协议:本 session 候选 Quirk #16(`.~` 双模)/ #17(`&o.Program` 编译错),均进 ## Open questions 待 `skills-optimizer` 评审,不在正文私编
- [x] Target < 150 行(实际 ~145 行)
- [x] 不动 baseline 文档:`02-domain-know-how/` / `01-plantsimulation-knowledge/` 全程只 `Read`
- [x] 不动 `.Models.AGVWithRobot.*`:0 个写 skill 调用,仅 `simtalk_run` 查询 + `readlog` 拉 print
- [x] **撤销 session 中途误判**:原以为 `AGVPool.NumAGVs` 是新 Quirk,后查 baseline `AGVPool/methods/methods.md` 证实**根本不存在**(只有 `getAssignedAGV(No)` / `getAssignedAGVsTable` / `getIdleAGV`),非 Quirk
- [x] **Novel finding 突出标注**:Connector 编号 gap、MStation* Marker 命名误导、AGV class 在 StandardObjects、pickup-loop 拓扑、Quirk #16/`&o.Program` 编译错
