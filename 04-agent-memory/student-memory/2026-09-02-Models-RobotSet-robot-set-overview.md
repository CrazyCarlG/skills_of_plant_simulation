# Student Note — 7 Frame 机器人示例集合通览
**Date:** 2026-09-02  **Agent:** plant-simulation-student
**Model:** .Models.{RobotComau,XZYStacker,PortalCrane,LinearPortal,MarkerCrossing,SevenAxisRobot,AGVWithRobot}  **Scenario:** robot-set-overview
**Duration:** 14:24 – 14:30  **Read-only skills called:** local-simtalk-execution (simtalk_run + readlog only; get-folder-tree / read-library / get-class-inheritance 内核 unavailable — 见 03-software)
**Baselines consulted:** `02-domain-know-how/01-factory-know-how/factory-modeling-architecture.md`、`02-domain-know-how/01-factory-know-how/warehouse-and-ctu-patterns.md`、`02-domain-know-how/03-modeling-know-how/01-objects/object-classification.md`、`01-plant-simulation-knowledge/02-offcial-psfm-model/Factory51/model-know-how/Factory51-建模思路.md`

---

## Operator self-review
- **范围**:7 Frame depth=2 通览;**只读**(无任何写动作)。
- **核心观察**:7 Frame 全是 `.Models.<Name>` 直挂 EventController + Connector 拓扑 + Source/Drain + 1 个同名 Station 作"机器人主体"——结构高度同构,几乎是把同一个模板换皮重命名。
- **跨 Frame 复用率**:7 个同名 Station 内部各自独立,**没有**走 Factory51 `Production` 类 + `P1/P2` 同构 isInstance 模式。
- **3 个 Frame-level Method 全部 dump**:MarkerCrossing.Init / MarkerCrossing.DestCtrl / AGVWithRobot.OnExit。
- **新发现 Quirk #4/#5/#6**(本次新增,见 03-software)。

---

## 01-factory-know-how
### 观察(Observe)
- 7 Frame 全部位于 `.Models.*` 下,**没有** `UserObjects/` 类库副本,**没有** BasicObjects 自包含。
- 7 个 Frame 的子对象结构高度同构:`EventController + (Source/Conveyor/Buffer 可选) + 同名 Station + Drain + 6~13 个 Connector + (AGVPool/Marker 可选)`。
- 7 个同名 Station(每个 Frame 一个 `RobotComau/XZYStacker/...` 同名子对象)InternalClassType 全部 = `Station`——不是真"机器人",是 Plant Simulation 标准 Station 对象承载"机器人"语义。
- 只有 2 个 Frame 涉及 AGV:`MarkerCrossing`(AGVPool + 4 个 Marker + Destinations DataList)和 `AGVWithRobot`(AGVPool + 6 个 Marker + OnExit Method)。
- 其他 5 Frame(RobotComau / XZYStacker / PortalCrane / LinearPortal / SevenAxisRobot)**只有 Conveyor + Station + Drain**,无 AGV/Track/Transporter。

### 理论对照(Reference + Judge)
| 观察 | Baseline 出处 | 判定 | Evidence |
|---|---|---|---|
| 7 Frame 全部走 `.Models.*` 直挂,无 `UserObjects/` 类库分离 | `factory-modeling-architecture.md §1.1` Factory51 范式 `UserObjects/Production` + `Models/Factory51/P1/P2` 二级复用 | ⚠️ diverges | 用户做法扁平化,所有逻辑塞 `.Models.*`;无"类 vs 实例"分层。可能因为这是"教学示例集",每个 Frame 自解释;但与本仓库沉淀的工厂范式不一致。 |
| 同名 Station 在每个 Frame 复制一份,无 isInstance 复用 | `factory-modeling-architecture.md §1.3` "一条线定义、两条线实例化"(Production 类 + P1/P2 同构) | ⚠️ diverges | 7 个 Station 全部独立 Station 实例,Origin 应是 `.MaterialFlow.Station`(基类)但**没有**用户自定义类层。简化但失去扩展性。 |
| 2 个含 AGV 的 Frame 没建 RCS DataTable 集中控制 | `warehouse-and-ctu-patterns.md §2.1` RCS 11 个 DataTable 集中可变状态 | ⚠️ diverges | MarkerCrossing 只有 1 个 `Destinations` DataList,无任务池/状态机/AGV state;OnExit 用直接调用 `driveToMarker`/`loadPart`,无 RCS 调度层。简化但与 P4_CTU 范式不一致。 |
| 7 Frame 没有 Hardware/Software 分层 | `factory-modeling-architecture.md §3` P4_CTU 模式 `AdvancedObject/Hardware` 与 `Software` 分层 | ⚠️ diverges | 整组模型无控制中枢概念,Station 即"机器人",无 RCS/MapGenerator 抽象层。教学模型可接受。 |
| Station 作"机器人"语义载体是合法用法 | `01-plant-simulation-help/objects/material-flow-objects/Station/README.md`(由 object-classification §3.4 `InternalClassType="Station"` 反推) | ✅ matches | PS Help Station 默认行为可用作"加工/等待"模拟器;用户语义里"机器人"是抽象语义标签。 |

### 候选 finding(进 ## Open questions)
- 7 Frame 扁平化 + 无类库分层 → 建议 curator 评估是否补一份"教学示例集合的简化架构约定"作为新模式到 `factory-modeling-architecture.md`(独立小节,标注"非生产范式")。
- 简化 AGV 控制(OnExit 直驱式 vs RCS 中心式) → 建议 curator 评估在 `warehouse-and-ctu-patterns.md` 增加"无 RCS 的简化调度"小节作为反面/低阶对照。

---

## 02-simtalkclaude-knowhow
### 观察(Observe)
- 桥协议 `.SimtalkClaude.*` 本次 session 0 调用(未触发)。prior session 已知 Quirk #1/#2/#3(本 session 自动继承)。
- **新发现 Quirk #4**:`o.ClassName` 不是合法 SimTalk identifier —— `print o.ClassName` 报 `Unknown identifier 'ClassName'`。
- **新发现 Quirk #5**:`var arr: array[1..6] := [string]; arr[1] := "...";` 这种先声明维度再赋值字符串元素的写法,在 Plant Simulation 2.0 simtalk_run 报 `Syntax error near line 1 at 'array'`。
- **新发现 Quirk #6**:`Station.numNodes` 在 SimTalk 里读不到(`to_str(s1.numNodes)` 让 simtalk_run 在 "ICT:Station" 那行后被砍,无错误行)。推测 Station 是 leaf-like 对象,`numNodes` 属性不可直接访问。

### 理论对照(Reference + Judge)
| 观察 | Baseline 出处 | 判定 |
|---|---|---|
| Quirk #4 `ClassName` 不可用 | `01-plant-simulation-help/simtalk/predefined-functions-iii-type-query-inputoutput-conversion-debug/README.md`(未深读,本 session 不强判定) | ❓ unknown — `getClassName` 是否存在待查 |
| Quirk #5 `array[1..6] := [string]` 报错 | 同上 | ❓ unknown — 怀疑是 v2.0 编译器对显式类型 + 隐式 string literal 的严格化 |
| Quirk #6 `Station.numNodes` 不可读 | `object-classification.md §3.2` "Frame.NumChildren 含义:结构子节点数(**不含** 2D 视图里的 placed 实例)" —— 反推:Station 不是 Frame/Folder,无 NumChildren | ⚠️ diverges(预期) — Station 是 leaf,无子节点容器;不能用 `numNodes` 迭代 |

### 候选 finding(进 ## Open questions)
- Quirk #5/#6 → 建议 `@skills-optimizer` 评审是否在 `local-simtalk-execution/SKILL.md` 补一段 "常见 syntax 失败 + 静默退出" 的诊断清单。

---

## 03-modeling-know-how
### 01-objects
- 7 Frame 内部对象清单如下(每 Frame 一次):
  - **RobotComau**:EventController + Source + Conveyor + Source2 + Conveyor2 + `RobotComau` Station + Conveyor3 + Drain + Connector×6(14 nodes)
  - **XZYStacker**:EventController + `XZYStacker` Station + Source + Conveyor + Buffer + Station + Conveyor2 + Drain + Connector×6(14)
  - **PortalCrane**:EventController + Source + Station + Station2 + Drain + `PortalCrane` Station + Connector×4(10)
  - **LinearPortal**:EventController + Source + Drain + Conveyor×2 + `LinearPortal` Station + Connector×3(9)
  - **MarkerCrossing**:EventController + 4 个 MarkerCrossing(嵌套 Frame)+ AGVPool + Init Method + M1~M4 Marker + Destinations DataList + DestCtrl Method + Connector×13(26)
  - **SevenAxisRobot**:EventController + Source + `SevenAxisRobot` Station + ParallelStation + Conveyor + Drain + Display + Drain3 + Connector×5(13)
  - **AGVWithRobot**:EventController + Station1 + Source2 + Station2 + Drain2 + AGVPool + MStation1/2 + Marker~Marker4 + OnExit Method + Connector×9(22)
- **判定**:⚠️ diverges vs Factory51(无 Hardware/Software 分层);✅ matches PS Help(各对象 ICT 与 PS 内置 Station/Source/Drain/Conveyor/Buffer/AGVPool 一致)。
- **特殊观察**:`MarkerCrossing` 内嵌 4 个同名嵌套 Frame(`MarkerCrossing`/`2`/`3`/`4`)——属"Frame-as-Container"模式,与 `object-classification.md §3.3` 双重身份描述一致(✅ matches)。

### 02-simtalk
- **3 个 Frame-level Method 源码 dump**:
  - `MarkerCrossing.Init`: `while true { var agv = AGVPool.getIdleAGV; if agv = void then exitloop end; agv.DestCtrl = &DestCtrl; agv.Destination = Destinations[z_uniform(1, Destinations.Dim+1)]; wait 10 }` ——**AGV dispatcher**,无限循环派单。
  - `MarkerCrossing.DestCtrl`: `wait 10; ?.Destination = Destinations[z_uniform(1, Destinations.Dim+1)]` ——**on-exit 重新分配目的地**(MU 离开 Station 时触发)。
  - `AGVWithRobot.OnExit`: `waituntil AGVPool.NumIdleAGVs > 0; var agv = AGVPool.getIdleAGV; agv.driveToMarker(MStation1); agv.loadPart(?.Cont); agv.driveToMarker(MStation2); agv.unloadPartTo(Station2); agv.IsIdle = true` ——**单 AGV 任务链**。
- **判定**(SimTalk 字面契约):
  - `agv.DestCtrl = &DestCtrl` —— 用 `&` 取方法引用作 callback,✅ matches PS Help `Method Reference` 语义(`02-simtalk/access-to-toolbox-and-folder-library/README.md` 应有定义,本 session 未深读)。
  - `z_uniform(1, Destinations.Dim+1)` —— ⚠️ **diverges(可疑 Quirk)**:`z_uniform(a,b)` 是闭区间 `[a,b]`,array index 上限应为 `Dim` 而非 `Dim+1`(后者偶尔越界返 string 类型异常)。`language-quirks-reference.md` 未涵盖,记 ❓ unknown。
  - `agv.IsIdle = true` —— 直接赋 boolean 给属性,无 `:=`。✅ matches SimTalk 2.0 隐式赋值语法(并非所有赋值必须 `:=`,`=` 在属性赋值语境合法)。
  - `waituntil AGVPool.NumIdleAGVs > 0` —— ✅ matches PS Help EventController pull pattern。

### 03-software
- 本 session 调用 11 次 simtalk_run + 8 次 readlog,5 次失败(Quirk #4/#5/#6)。
- **核心 skill 经验**:
  - **simtalk_run 的 `log` 字段只 echo 第一条 print 后续被砍**——必须**配合 `readlog` 通道**才能拿到完整 print 流。这是 prior session 已发现的 Quirk,但本次再次验证。
  - **simtalk_run 异常时静默退出**——`log` 字段只有 `"execute sim-code: '...'"` + 第一行 print,后续 print 全部丢失,**无错误行**。这让 debugging 难度大。
  - **`local-simtalk-get-folder-tree` / `read-library` / `get-class-inheritance` 三个 SKILL 脚本 internal error**:`bfs_one_level.py --no-infobox .Models` 报 `readlog envelope not JSON`——内部用 readlog 解析但格式不匹配。本 session 改用 `local-simtalk-execution` 的 raw socket_client 直接构造 simtalk_run + readlog 序列绕开。
- **判定**:⚠️ diverges vs SKILL.md 设计意图(三个 SKILL 都假设 readlog 能 parse),实际 readlog 通道在某些调用栈下格式不符。建议 `@skills-optimizer` 评审 SKILL.md 是否补 "fallback 到 socket_client + 自构 simtalk_run + readlog" 段落。

---

## 04-modeling-example
### 观察(Observe)
- 这 7 Frame 本身就是一份**教学示例集合**(Siemens 官方 PSFM 在 `01-plantsimulation-knowledge/02-offcial-psfm-model/` 另有完整 1592 对象版)。
- 每个 Frame 演示一种"机器人"语义:
  - **RobotComau** — 6 轴铰接机器人(简单 Source/Conveyor/Station/Drain)
  - **XZYStacker** — XYZ 三轴堆垛机(Source/Buffer/Station/Drain)
  - **PortalCrane** — 龙门吊(Source/Station/Station2/PortalCrane Station/Drain)
  - **LinearPortal** — 直线龙门(Source/Drain/Conveyor×2/LinearPortal Station)
  - **MarkerCrossing** — AGV 路径交叉演示(26 nodes 含 AGVPool + Markers + DataList)
  - **SevenAxisRobot** — 7 轴机器人 + ParallelStation + Display
  - **AGVWithRobot** — AGV 协同 Station 演示(22 nodes 含 OnExit Method)

### 理论对照(Reference + Judge)
| 观察 | Baseline 出处 | 判定 |
|---|---|---|
| 7 Frame 教学示例集合 | `01-plantsimulation-knowledge/02-offcial-psfm-model/Factory51/model-know-how/Factory51-模型结构.md`(用户另立教学集合) | ✅ matches — Siemens 自带多个 PSFM 教学集,本模型同构 |
| `MarkerCrossing` 用 `DataList` 而非 `DataTable` | `01-plant-simulation-help/objects/information-flow-objects/DataList/README.md`(应存在,本 session 未读) | ✅ matches — DataList 是 PS 内置对象,可作简单 destination 列表 |
| `SevenAxisRobot.ParallelStation` 与 `Station` 并列 | `01-plant-simulation-help/objects/material-flow-objects/ParallelStation/README.md` | ✅ matches — PS 内置 ParallelStation 用作多处理位 |

### 候选 finding(进 ## Open questions)
- 建议 curator 把"7 Frame 教学集合的最小可复用模板"(1 Source + 1 Station + 1 Drain + 2 Connector)加入 `04-modeling-example/` 作为 starter kit。

---

## 05-modeling-experience
### 观察(Observe)
- 7 Frame 几乎全是 "单 Station + 上下游 Buffer/Conveyor" 的最小加工模型,适合初学者快速理解 PS 物料流基础。
- **Quirk 累计**:本次新增 #4/#5/#6,与 prior session Quirk #1/#2/#3 一并记录在 `## 02-simtalkclaude-knowhow`。
- **跨 Frame 命名规律**:`<RobotType>` 同名 Station 在各 Frame 内部作为"机器人主体"——这种"语义重载 Station 类名"是常见教学 trick。
- **AGVWithRobot 演示的 pull pattern**:`waituntil AGVPool.NumIdleAGVs > 0` 后单 AGV 串行执行 4 步——清晰展示 PS AGV API (`driveToMarker`/`loadPart`/`unloadPartTo`)。
- **MarkerCrossing 的 dispatcher pattern**:Init 死循环 + on-exit 重新派单,演示"事件驱动 + 后台轮询"混合范式。

### 候选 finding(进 ## Open questions)
- **Quirk #7(本 session 内观察)**:`z_uniform(1, Dim+1)` 是疑似 off-by-one → 建议 `@skills-optimizer` 评审是否在 `language-quirks-reference.md` 补一条 "uniform 上限闭合区间 vs array index 半开区间" 警示。
- 7 Frame 教学集合结构 → 建议 curator 评估是否沉淀到 `04-modeling-example/starter-robot-cell-pattern.md`。

---

## Cross-references
- 02-domain-know-how entries: `01-factory-know-how/factory-modeling-architecture.md`、`01-factory-know-how/warehouse-and-ctu-patterns.md`、`03-modeling-know-how/01-objects/object-classification.md`(全部只读引用,非沉淀)
- 01-plantsimulation-knowledge entries: `02-offcial-psfm-model/Factory51/model-know-how/Factory51-建模思路.md`、`01-plant-simulation-help/objects/material-flow-objects/Station/README.md`(仅路径引用,未深读)
- 04-agent-memory 其它 session: `2026-09-02-Assembly1,Assembly2-orientation.md`(prior session,Assembly 装配线;与本次模型不同,Quirk #1/#2/#3 自动复用)
- per-skill 调用 log:`/tmp/student_d1.json`(depth=1 7 Frame counts)、`/tmp/student_d2.json`(depth=2 children list,内嵌 readlog)、`/tmp/student_ci4.json`(Quirk #4 失败现场)、`/tmp/student_lm2b.json`(Quirk #5 失败现场)、`/tmp/student_ci5.json`(Quirk #6 失败现场)

---

## Open questions / cross-pollination
- *建议由 `plant-simulation-experience-curator` 评审是否沉淀:*
  - 7 Frame 扁平化 + 无类库分层 → 候选到 `02-domain-know-how/01-factory-know-how/factory-modeling-architecture.md` 新增"教学示例集合的简化约定"小节(baseline 出处:本 session 整体观察 + Factory51 范式对比)。
  - 简化 AGV 控制(OnExit 直驱式 vs RCS 中心式) → 候选到 `02-domain-know-how/01-factory-know-how/warehouse-and-ctu-patterns.md` 新增"无 RCS 的简化调度"小节。
  - 7 Frame 教学集合结构 → 候选到 `02-domain-know-how/04-modeling-example/starter-robot-cell-pattern.md` 新增 starter kit。
- *建议由 `skills-optimizer` 评审:*
  - SKILL.md 补 "simtalk_run 静默退出 + readlog fallback" 段落(基于 Quirk #4/#5/#6 三个失败现场)。
  - SKILL.md 补 "Quirk #7:`z_uniform(1, Dim+1)` 疑似 off-by-one" 到 `02-simtalk/language-quirks-reference.md`。
- *未关闭问题:*
  - `Quirk #4`:`ClassName` 不可用,`getClassName` 是否存在待 PS Help 深读。
  - `Quirk #5`:`array[1..6] := [string]; arr[1] := "..."` 报 syntax error 的根因(数组字面量 vs 显式维度声明冲突?)。
  - `Quirk #6`:`Station.numNodes` 不可读的根因(Station 非 Container?PS 2.0 改 API?待查)。

---

## 经验 Log (append-only by student on emergency)
- ⚠️ @plant-simulation-student emergency 2026-09-02 14:30:
  - Quirk #4:`o.ClassName` 报 Unknown identifier(实测 simtalk_run on `.Models.RobotComau.RobotComau`)。
  - Quirk #5:`var arr: array[1..6] := [string]; arr[1] := "..."` 报 `Syntax error near line 1 at 'array'`(实测 simtalk_run)。
  - Quirk #6:`Station.numNodes` 在 simtalk_run 中读不到,后续 print 静默被砍,无错误行(实测 simtalk_run on Station 对象)。
  - 建议 `@skills-optimizer` 在 SKILL.md 中补一段"simtalk_run 静默退出 + readlog fallback"的诊断指引;具体失败现场见本文件 `## Cross-references` 的 per-skill log 路径。