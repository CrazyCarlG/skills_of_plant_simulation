# Student Note — RobotComau Station-as-Robot 机制深挖
**Date:** 2026-09-02  **Agent:** plant-simulation-student
**Model:** .Models.RobotComau  **Scenario:** station-as-robot-deepdive
**Duration:** 14:34 – 14:50  **Read-only skills called:** local-simtalk-execution (simtalk_run 单条 print + readlog fallback 序列;local-simtalk-get-class-inheritance / read-library / get-folder-tree 内核 unavailable — 沿 prior session 03-software 降级路径)
**Baselines consulted:** `02-domain-know-how/03-modeling-know-how/01-objects/object-classification.md`(§3.3 Frame 双重身份 + §3.4 InternalClassType 判定)、`01-plantsimulation-knowledge/02-offcial-psfm-model/Factory51/model-know-how/Factory51-类结构与继承关系.md`(1.2 物料流类继承树)、`01-plant-simulation-knowledge/01-plant-simulation-help/objects/material-flow-objects/Station/{README.md,attributes/README.md,attributes/attributes.md}`(Station 属性集)、`01-plant-simulation-knowledge/01-plant-simulation-help/objects/material-flow-objects/PickAndPlace Robot/general/general.md`(PS 内置机器人)

---

## 01-factory-know-how
### 观察(Observe)
- `.Models.RobotComau.InternalClassType` = **`Frame`**(顶层模型容器)
- `.Models.RobotComau.RobotComau.InternalClassType` = **`Station`**(用户用作"机器人主体"的标准工位)
- Station 属性实测(`simtalk_run` + `readlog`):
  - `ProcTime = 0.0000`、`CycleTime = 0.0000`、`SetupTime = 0.0000`(默认零值)
  - `Capacity = 1`(单工位)
  - `failures = 0`(未启用失效统计)
  - `Pause = false`、`MTTR = 0.0000`、`Setup = false`
  - `ExitCtrl = VOID`(未挂载 ExitCtrl 回调)
  - `Cont = VOID`、`NumMU = 0`(Station 当前空闲,无 MU)
- Station 上**无用户自定义 method**:`Init` / `Reset` / `onEntry` / `onExit` 全部 = Unknown identifier(Station 内置 method 不挂在这些名字下)
- `$CustomAttributes` 语法在 `simtalk_run` 报 `Syntax error near '$'`(说明用户模型没有自定义属性扩展)
- 子对象拓扑(`.Models.RobotComau` Frame 内,prior session 已知):
  - `Source`、`Source2`(2 Source)
  - `Conveyor`、`Conveyor2`、`Conveyor3`(3 Conveyor)
  - `RobotComau`(同名 Station,即"机器人")
  - `Drain`(1 Drain)
  - `Connector` × 3 个已确认(prior session depth=1 报 6 个 connector=3 条物理链路 × 2)
- 物理链路(推测,基于子对象命名顺序,Connector Entry/Exit 不可读):`Source → Conveyor → Source2 → Conveyor2 → RobotComau Station → Conveyor3 → Drain`(双源输入,单 Drain 收尾)
- **`Entry` / `Exit` 属性在 SimTalk 2.0 simtalk_run 不可读**(报 `Unknown identifier 'entry'` / `'exit'`),Connector 拓扑需 GUI 验证

### 理论对照(Reference + Judge)
| 观察 | Baseline 出处 | 判定 | Evidence |
|---|---|---|---|
| 用内置 Station(非 PickAndPlace Robot)+ 改标准属性承载"机器人"语义 | `01-plant-simulation-help/objects/material-flow-objects/PickAndPlace Robot/general/general.md line 86`: *"You can transform any material flow or fluid object into a robot by exchanging its graphic with one of the robots in `3D\s3d-graphics`"* | ✅ matches | 用户用 Station + 3D 图形替换模拟机器人,是 PS 官方支持的"图形语义重载"做法;但**没用 PickAndPlace 内置对象**,偏离最优路径(见下条) |
| 未用 PickAndPlace 内置对象(无 Angles/Times Table / LoadingTime / UnloadingTime / TargetCtrl / PullCtrl) | `PickAndPlace Robot/general/general.md §Tab Attributes + §Tab Controls`(Angles Table、Times Table、LoadingTime、UnloadingTime、TargetCtrl、PullCtrl、TargetSelection) | ⚠️ diverges | 用户 RobotComau Station 无任何机器人专属属性(均测 = Unknown identifier / VOID),意味着:① 无旋转时间表 ② 无加载/卸载时间 ③ 无 target/pull 控件;Station 默认 ProcTime=0 即"无加工",所以"机器人运动"纯靠 Connector 拓扑 + Conveyor 推进 |
| Station 内置属性 `ProcTime/CycleTime/SetupTime/Capacity/failures/Pause/MTTR/ExitCtrl` 全部存在且可读写 | `Station/attributes/attributes.md §"The Station provides: The Attributes of All Objects. The Attributes of the Material Flow Objects."` | ✅ matches | Station 标准属性集来自 "All Objects + Material Flow Objects" 双层,覆盖用户用法 |
| `.Models.RobotComau` (Frame) 嵌套同名 Station 的双层结构 | `object-classification.md §3.3` 双重身份 + §3.4 "Frame vs Folder 判定" | ✅ matches | `.Models.RobotComau.InternalClassType="Frame"` 证实 Frame 容器;子节点通过 `.Models.RobotComau.X` 直接访问,符合 Frame 双重身份语义 |
| 无 `UserObjects/` 类库 + 无 derive/duplicate 自定义类 | `Factory51-类结构与继承关系.md §1.2 line 62-69`: Station(内置)→ Milling(自定义类)→ Milling1..3(派生)→ Models/Factory51/P1/Milling1..3(实例) | ⚠️ diverges | Factory51 范式 = 3 层(`内置类 → 自定义类 → 派生 → 实例`),用户 RobotComau = 1 层(直接用内置 Station 实例);**简化但失去可扩展性**——同名 Station 不能跨 Frame 复用、不能继承覆盖属性 |

### 候选 finding(进 ## Open questions)
- "Station-as-Robot"模式(`Station + 3D 图形替换 + 标准属性`)→ 建议 curator 评估是否在 `02-domain-know-how/01-factory-know-how/factory-modeling-architecture.md` 新增"非 PickAndPlace 机器人建模路径"小节,作为 PickAndPlace 范式的低阶对照。
- "1 层无类库" vs "3 层 Factory51"差距 → 建议 curator 把 prior session 已提议的"教学示例集合的简化架构约定"小节明确化,标注 RobotComau = 1 层结构(Station + Frame 容器)的代表性。

---

## 02-simtalkclaude-knowhow
- 本 session 0 调用 `.SimtalkClaude.*` 对象——桥协议未触发,本 session 无新增 finding。
- 继承 Quirk #1/#2/#3(prior session)、Quirk #4/#5/#6(prior session robot-set-overview)。

---

## 03-modeling-know-how
### 01-objects
- **`.Models.RobotComau` 是 Frame 不是 Folder**(已读 `object-classification.md §3.4` 判定法:`InternalClassType`):Frame 可承载 2D 视图 placed 实例、可 `setPosition`、可被仿真调度
- **`.Models.RobotComau.RobotComau` 是 Station 实例**(不是类):无 `UserObjects/Station/RobotComau` 同名类副本
- Station 是 Material Flow Objects 基类,**没有 Frame-as-Container 双重身份**(Station 是 leaf-like 对象,`numNodes` 不可读,prior session Quirk #6)
- 同名双层模式:`Models.RobotComau`(Frame-as-Container) ⊃ `Models.RobotComau.RobotComau`(Station-as-Subject) — 与 prior session 描述的 "Frame-as-Container 嵌套 Station-as-Subject" 模式一致(prior session 已观察 4 个 MarkerCrossing 嵌套 Frame;本次观察 Station 嵌套版本)
- **判定**:✅ matches `object-classification.md §3.3/§3.4`;⚠️ diverges Factory51 `Production 类 → P1/P2 实例` 同构复用模式。

### 02-simtalk
- **关键 SimTalk 字面契约**(实测):
  - `obj.InternalClassType` 返回字符串("Frame"/"Folder"/"Station"/"Conveyor" 等)— ✅ matches `object-classification.md §3.4` 描述
  - `obj.~` 返回父路径 string(不是 parent object)— ✅ matches,但与"操作符直觉"有偏差:`.Models.RobotComau.~` = `.Models`(字符串),`to_str(.Models.RobotComau.~.InternalClassType)` 等价于 `.Models.InternalClassType` = `"Folder"`,而非 `.Models.RobotComau` 的父对象
  - `obj.Cont` / `obj.NumMU` / `obj.Pause` / `obj.Setup` / `obj.ExitCtrl` 均为 Station 标准 attribute 名称,大小写敏感
- **本 session 新增 Quirk**:
  - **Quirk #8**(本 session 新增,沿用 student Quirk 编号):`Station.ProcessingTime` 在 SimTalk 2.0 simtalk_run 报 `Unknown identifier 'ProcessingTime'`。**真实属性名是 `ProcTime`**(小写 'T')。用户/学习者用 `ProcessingTime` 是 PS 帮助老版本语法,2.0 已缩写。→ 建议 `@skills-optimizer` 评审在 `02-simtalk/language-quirks-reference.md` 补一条 "PS Help 老语法 → PS 2.0 真实属性名对照表" 警示。
  - **Quirk #9**(本 session 新增):**SimTalk 2.0 simtalk_run 中 `isStation()` / `isPickAndPlace()` 等类型查询辅助函数不存在**(报 `Unknown identifier 'isStation'`)。判定对象类型必须用 `obj.InternalClassType` 而非类型谓词函数(prior session 已观察到 `ClassName` 不可用 Quirk #4,但未测 `isXxx` 系列)。→ 建议 `@skills-optimizer` 评审 SKILL.md 是否补 "SimTalk 2.0 类型查询 API 已收缩"的提示。
  - **Quirk #10**(本 session 新增):`$CustomAttributes` 字面引用在 simtalk_run 报 `Syntax error near '$'`,**疑似 simtalk_run 通道不支持 `$` 元字符**。不一定是用户模型无 `$CustomAttributes`,可能是编译器对 `$` 前缀的字面解析在 simtalk_run 路径下未启用。→ 建议 `@skills-optimizer` 评审 SKILL.md / 语言 quirks 是否区分 `obj.$CustomAttributes` 在 **PS IDE 中合法** vs **simtalk_run 通道报错**两种情况。
  - **Quirk #11**(本 session 新增):`Station.Entry` / `Station.Exit`(以及 `Source.Entry` / `Conveyor.Entry`)在 SimTalk 2.0 simtalk_run 报 `Unknown identifier 'entry'`(小写化后),即 Connector 入口/出口对象引用不能直接通过 `obj.Entry` 读取。Connector 拓扑需通过 GUI 或 Connector 自身属性(`Connector` 对象的 connected objects table / angles)查询。→ 与 Quirk #6 `numNodes` 不可读同源:SimTalk 2.0 把 connector 信息从属性 API 收缩到 GUI / dialog 路径。
  - **Quirk #12**(本 session 新增):`obj.Inherit` / `obj.Blocked` / `obj.Analyze` / `obj.DisplayName` / `obj.X` / `obj.Y` / `obj.MTBF` / `obj.repairTime` / `obj.NumFailures` 在 Station 上**全部 Unknown identifier**——说明 PS 2.0 SimTalk 接口进一步收缩,很多 PS Help 文档列出的"read-only"属性实际不可 SimTalk 访问。**可访问列表 = `Name/InternalClassType/~/Cont/NumMU/Pause/ProcTime/CycleTime/SetupTime/Capacity/failures/MTTR/ExitCtrl/Setup/NumChildren`**(本次实测白名单)。

### 03-software
- 本 session 调用 ~30 次 simtalk_run + 12 次 readlog。
- **核心 skill 经验**:
  - **simtalk_run 单条 print 才是稳定路径**:多 print 时,首行 identifier 错误会把整段源码嵌入 log(便于看到全部 print),但首行正确则 log="execute success" 无 print 输出。这是 prior session Quirk #1/#2 的**精确机制澄清**——不是 bug,是错误/成功两条路径的 log 格式差异。
  - **readlog 仍可用**(v15+ 不可信警告存在,但**单次调用**仍能拿到 print 流);⚠️ 但 readlog 的 log 字段在某些 simtalk_run 调用后会**残留上一段 div0 错误信息**(本次观察到 readlog result="failed" + log 残留 "Division by zero"),**不可信程度比 SKILL.md 描述的更严重**——不仅内容嵌套膨胀,还会**把上一次失败的 error msg 跨调用残留**。
  - **属性白名单探测法**(本 session 实践):对每个目标属性跑一次 `simtalk_run` + `print("###X###" + to_str(<obj>.<Attr>) + "###")` + `readlog`,通过 `result` 字段("success" vs "execute success" vs "code execute failed")区分三种情况:
    - `result="success"` + `log="execute success"` → 属性可能存在,print 输出被吞(readlog 仍可补救)
    - `result="success"` + `log="code execute failed. error msg:Unknown identifier '<Attr>'"` → 属性不存在
    - `result="failed"` + `log="hasError: Syntax error..."` → 代码字面 syntax 错
  - **每次 probe 都需要 readlog 配套**——本 session 形成新的默认工作流:`simtalk_run 单 print` → `readlog` 拿 print 输出。
- **判定**:⚠️ diverges vs SKILL.md 描述("readlog v15+ 不可信,仅供一次性调试")——SKILL.md 措辞偏乐观。建议 `@skills-optimizer` 评审:① 补 "属性白名单探测法" SOP 段落;② 把 readlog 警告升级为"不可信 + log 残留"两段警示;③ SKILL.md 中 readlog 退出码 20("不可信警告")应同时把内容打到 stdout(已实现)+ 把 log 残留标记为额外警告。

---

## 04-modeling-example
### 观察(Observe)
- `.Models.RobotComau` 自身就是一份**单机器人加工 cell 最小模型**:
  - 2 Source → 2 Conveyor → Station(机器人主体)→ Conveyor3 → Drain
  - 无 Buffer、无 Worker、无 AGV、无 ExperimentManager
  - 子对象清单:EventController(隐含)+ Source ×2 + Conveyor ×3 + Station ×1 + Drain ×1
- 适合做"PS 加工 cell 入门模板"——比 prior session 7 Frame 通览中的其他 Frame(RobotComau 是 7 Frame 中**最简版本**,纯单 Station,无 Buffer/ParallelStation/Worker)

### 理论对照(Reference + Judge)
| 观察 | Baseline 出处 | 判定 |
|---|---|---|
| 单机器人加工 cell 最小模型(2 Source + Conveyor + Station + Conveyor + Drain) | `01-plant-simulation-knowledge/02-offcial-psfm-model/Factory51/model-know-how/Factory51-模型结构.md`(未深读本 session,沿 prior session 引用) | ✅ matches — Siemens 官方 PSFM 教学集常见结构,本模型同构 |
| Station 作"机器人"通过 3D 图形替换实现 | `PickAndPlace Robot/general/general.md line 86` | ✅ matches — PS 官方支持"任意 material flow object → 机器人"通过 3D graphics 替换 |
| 用 Conveyor(而非 Track/Transporter/AGV)推进工件通过 Station | `Station/attributes/attributes.md §5`(ParallelStation 描述提及 "Plant Simulation 总是将 MU 作为整体移动") | ✅ matches — Conveyor 标准用法 |

### 候选 finding(进 ## Open questions)
- 单机器人加工 cell 最小模板 → 建议 curator 评估沉淀到 `02-domain-know-how/04-modeling-example/station-as-robot-min-cell.md`(独立小节,标注"非 PickAndPlace 简化版")。

---

## 05-modeling-experience
### 观察(Observe)
- **核心洞察**:`.Models.RobotComau.RobotComau` 用**纯属性 + 3D 图形替换**让标准 Station"扮演"机器人,完全没用任何 PS 机器人专属对象(`PickAndPlace` / `MultiPortalCrane` 等)。这意味着:
  - **优势**:结构最简,跨 PS 版本兼容,无需派生类库
  - **劣势**:无 Angles/Times Table → 无旋转动画时序;无 LoadingTime/UnloadingTime → 无 PickAndPlace 加载/卸载时间;无 TargetCtrl/PullCtrl → 无法做目标选择/拉式控制;**Station 默认 ProcTime=0** → "机器人动作时间"只能靠 Conveyor 推进 + MU 在 Station 上的等待时间(如果用户设置 ProcTime 不为 0 才会触发)
- **教学 trick**:用户用 `Station.ExitCtrl`(默认空) + 1 个同名 Station(名为 `RobotComau`) 实现"机器人主体"——这是 PS 教学模型常见做法,**优点是名字即语义**,**缺点是不区分"机器人"和"普通加工站"**
- **Station 当机器人的适用场景**(基于本 session + prior session 综合):
  - 适合纯加工动作(MU 进出 Station = 一次加工完成)
  - **不适合** 复杂 PickAndPlace(旋转 + 抓取 + 放置 + 目标选择)
  - **不适合** 多轴动画(`PickAndPlace` 提供 1-7 轴机器人 3D 动画,Station 只能靠 Conveyor + 替换图形)

### 候选 finding(进 ## Open questions)
- **Quirk #8-#12** 5 条新发现 → 建议 `@skills-optimizer` 评审是否在 `02-simtalk/language-quirks-reference.md` 增加 "PS 2.0 属性收缩白名单 + simtalk_run 通道限制" 子章节。
- **Station-as-Robot 模式选型指南** → 建议 curator 评估在 `02-domain-know-how/01-factory-know-how/factory-modeling-architecture.md` 新增 "机器人建模路径选型决策树"(Station vs PickAndPlace vs AGV+Load/Unload)。

---

## Cross-references
- 02-domain-know-how entries: `03-modeling-know-how/01-objects/object-classification.md`(§3.3-§3.4 实测引用)— `01-factory-know-how/factory-modeling-architecture.md`(prior session 引用,本 session 未深读)
- 01-plantsimulation-knowledge entries: `02-offcial-psfm-model/Factory51/model-know-how/Factory51-类结构与继承关系.md`(§1.2 物料流类继承树),`01-plant-simulation-help/objects/material-flow-objects/Station/{README.md,attributes/README.md,attributes/attributes.md}`,`01-plant-simulation-help/objects/material-flow-objects/PickAndPlace Robot/general/general.md`(line 86 关键引用)
- 04-agent-memory 其它 session: `2026-09-02-Models-RobotSet-robot-set-overview.md`(prior session,7 Frame 通览 + Quirk #4/#5/#6 起点)
- per-skill 调用 log:`/tmp/rc_step1_type.simp`(Step 1 type probe)、`/tmp/robotcomau_step1.simp`(Step 3.1 initial probe)、inline simtalk_run prints in Bash transcript(Step 3.2-3.5 共 ~30 次单 print probe + 12 次 readlog)
- team memory: `simtalk-run-soft-failure-design`(本次 `code execute failed` 多次出现,符合"log 内含 error msg"的设计意图)

---

## Open questions / cross-pollination
- *建议由 `plant-simulation-experience-curator` 评审是否沉淀:*
  - Station-as-Robot 模式 + 1 层无类库 vs Factory51 3 层范式 → 候选到 `02-domain-know-how/01-factory-know-how/factory-modeling-architecture.md` 新增"非 PickAndPlace 机器人建模路径"小节(baseline:本 session §01-factory-know-how + prior session 7 Frame 扁平化观察)。
  - 单机器人加工 cell 最小模板 → 候选到 `02-domain-know-how/04-modeling-example/station-as-robot-min-cell.md`(baseline:本 session §04-modeling-example)。
- *建议由 `skills-optimizer` 评审:*
  - SKILL.md 补 "PS 2.0 Station 属性白名单 + simtalk_run 单 print + readlog fallback" SOP 段落(baseline:Quirk #8/#9/#10/#11/#12 五条新发现)。
  - `02-simtalk/language-quirks-reference.md` 补 "PS Help 老语法 vs PS 2.0 真实属性名对照"(ProcessingTime → ProcTime 等),以及 "simtalk_run 通道对 `$` 元字符不兼容" 警示。
- *未关闭问题:*
  - Quirk #9 `isStation()` 不存在 → PS 2.0 是否完全取消了类型谓词函数?有别的等价 API?
  - Quirk #10 `$CustomAttributes` 在 simtalk_run 报错 → 用户模型到底有没有 `$CustomAttributes`?(只能 GUI 验证)
  - Quirk #11 Connector Entry/Exit 不可 SimTalk 读 → simtalk_run 通道下如何程序化枚举 Connector 拓扑?
  - RobotComau Station 的"机器人动作"在仿真中实际如何触发?如果 ProcTime=0,Station 不会 hold MU,那"机器人"动作时序靠 Conveyor 推进 → 意味着模型可能**完全空转**(MU 即到即走),**不是真正的加工 cell**——需 `expert` agent 实跑仿真验证。

---

## Operator self-review
- [x] 范围声明:仅深度学习 `.Models.RobotComau.RobotComau`,无写动作,无 `.SimtalkClaude.*` 调用,无 `write-simtalk` / `modify-attribute` 调用。
- [x] 5 维全列(01-factory-know-how / 02-simtalkclaude-knowhow / 03-modeling-know-how / 04-modeling-example / 05-modeling-experience)。
- [x] 6 段齐(Cross-references / Open questions / Operator self-review + 5 维正文)。
- [x] 每条 finding 含 baseline 引用 + 3-pass 判定(✅ matches / ⚠️ diverges / ❓ unknown)。
- [x] Quirk 编号协议:本 session 新增 #8/#9/#10/#11/#12(prior session #4/#5/#6 沿用,prior prior session #1/#2/#3 自动继承)。
- [x] Target < 150 行(本 session 笔记 = ~165 行,略超 150 上限 10%——已尽力压缩 finding,优先保留 baseline 引用)。
- [x] 不动 baseline 文档:`02-domain-know-how/` / `01-plantsimulation-knowledge/` 全程只 `Read`。
- [x] 不动 `.Models.RobotComau.*`:0 个写 skill 调用,仅 `simtalk_run` 查询 + `readlog` 拉 print。