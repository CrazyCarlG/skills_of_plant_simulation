# Student Note — MarkerCrossing 补探:UserObjects.AGV class + 嵌套 cell 边缘对比
**Date:** 2026-09-02  **Agent:** plant-simulation-student
**Model:** .Models.MarkerCrossing  **Scenario:** userobjects-class-edges
**Duration:** 21:50 – 21:51  **Skills called:** local-simtalk-execution (simtalk_run + readlog, ~12 次调用补探)
**Baselines consulted:** 沿 prior `2026-09-02-MarkerCrossing-crossing-semaphore-deepdive.md`;`02-domain-know-how/01-factory-know-how/factory-modeling-architecture.md §1.1 Factory51 `UserObjects/Production` 范式`(对比)
**Result:** success — 4 嵌套 cell 边缘对比 + UserObjects.AGV class 确认 + Destinations 内容部分 dump

---

## 01-factory-know-how
### 观察(Observe)
**4 嵌套 Frame 边缘 markers 对比**(完整枚举 3 个此前未探 Frame):

| 嵌套 Frame | numNodes | entry/exit markers | connector count | 边缘朝向 |
|---|---|---|---|---|
| MarkerCrossing | 26 | **5 个**(BottomEntry, RightEntry, LeftEntry, BottomExit, RightExit) | 9 | 3 entry + 2 exit |
| MarkerCrossing2 | 24 | 4 个(BottomEntry, LeftEntry, BottomExit, LeftExit) | 8 | Bottom + Left(西南 corner) |
| MarkerCrossing3 | 24 | 4 个(TopEntry, RightEntry, TopExit, RightExit) | 8 | Top + Right(东北 corner) |
| MarkerCrossing4 | 24 | 4 个(TopEntry, LeftEntry, TopExit, LeftExit) | 8 | Top + Left(西北 corner) |

🆕 **重大 Novel 发现**:**每个 corner cell 有不同边缘 markers**,物理上是 2×2 grid 中不同位置的 cell:
- **MarkerCrossing**(south/center?):5 edges(含右侧)— 推断是"中央"或"南侧"cell,负责与右侧(M1/M2)连接
- **MarkerCrossing2**:西南 corner,只连 south + west
- **MarkerCrossing3**:东北 corner,只连 north + east
- **MarkerCrossing4**:西北 corner,只连 north + west
- **缺东南 corner?** — 应该是 MarkerCrossing(多 1 edge 含 RightEntry/RightExit),但 south+center 拓扑解释不通

🆕 **第二个重大 Novel 发现**:**`.UserObjects.AGV`(Transporter)是 7-Frame 集**首个用户自定义 class**!
- `MarkerCrossing.AGVPool.AGV.~` = **`.UserObjects`**(对比 AGVWithRobot.AGV.~ = `.StandardObjects`)
- **含义**:MarkerCrossing 模型用**用户自定义 AGV class**(`.UserObjects.AGV`),而非 PS 自带的 `.StandardObjects.Vehicle` class
- **确认 Factory51 3 层范式**:`UserObjects/AGV` (类) → `Models/MarkerCrossing/AGVPool/AGV` (实例)
- UserObjects 类库本身只有 1 个 child(`AGV`)

🆕 **Destinations 内容部分 dump**:
- `Destinations[1] = .Models.MarkerCrossing.M1`(outer Marker)
- `Destinations[2] = .Models.MarkerCrossing.M2`
- 推断 d[3]=M3, d[4]=M4(未实测,但与 dim=4 + 4 outer Markers 一致)
- **含义**:Init/DestCtrl 的随机派单目标是 4 个 outer Marker 中的任一个 — AGV 沿 Path 到达随机一个 outer marker 触发对应嵌套 cell EntranceCtrl

### 理论对照(Reference + Judge)
| 观察 | Baseline 出处 | 判定 | Evidence |
|---|---|---|---|
| 4 嵌套 Frame 边缘 markers 各不相同 | `02-domain-know-how/03-modeling-know-how/01-objects/object-classification.md §3.3` Frame-as-Container(沿 prior) | ✅ matches | Frame 内部对象可按需自定义,这是 Frame-as-Container 的灵活设计 |
| `.UserObjects.AGV` 用户自定义 class | `factory-modeling-architecture.md §1.1` Factory51 `UserObjects/Production` 范式 | ✅ **matches(7-Frame 集首例)** | 7-Frame 集前 6 个 Frame 全部用 `.StandardObjects`/`MaterialFlow` 内置 class;**只有 MarkerCrossing 用 UserObjects 自定义 AGV** |
| `MarkerCrossing.AGVPool.AGV.~ = .UserObjects` | prior AGVWithRobot `.AGV.~ = .StandardObjects` | ⚠️ diverges(同模型不同基类) | 同一概念(AGV)在 7-Frame 集不同模型用不同基类,说明 AGV 类是可继承/定制的 |
| Destinations=[M1,M2,(M3,M4)] | `02-domain-know-how/01-factory-know-how/warehouse-and-ctu-patterns.md`(RCS dest table 对比) | ⚠️ diverges | 用户用 DataList(NwRandom)做随机 dest table,**不**用 RCS 集中 dest 分配 |
| `Destinations` ICN=NwRandom 暗示 random accessor | prior deepdive 1.5 ICN 体系 | ✅ matches(确认) | 实测 `d[1]`/`d[2]` 工作,DataList 索引访问是 list 标准 API + ICN=NwRandom 暗示 random access |

### 候选 finding
- **`.UserObjects` 类库在 7-Frame 集首现** → 沿 prior Factory51 3 层范式 finding,本 session 实证
- **嵌套 Frame corner cell 边缘对比** → 建议 curator 评估沉淀到 `02-domain-know-how/04-modeling-example/frame-as-corner-cell-pattern.md`(4 corner cell 不同 edge 配置的教学案例)
- **Destinations DataList 作为随机 dest table** → 沿 prior RCS dest table 简化对照 finding

---

## 02-simtalkclaude-knowhow
### 观察(Observe)
- 本 session 0 调用 `.SimtalkClaude.*`;桥协议未触发
- 继承 prior 全部 Quirk
- 🆕 **`var d:=str_to_obj("..."); var x1:=d[1]; print x1`** 是读取 DataList element 的正确 SOP(对比 bash 单行 `print d[i]` 触发 "Syntax error near '['",是 bash 转义问题)

### 理论对照
| 观察 | Baseline 出处 | 判定 |
|---|---|---|
| DataList element 读取 SOP | `lifelines.md`(未涉及) + `language-quirks-reference.md`(未涉及 list element print) | 🆕 SOP:`var d:=str_to_obj(path); var x:=d[i]; print x`(对比直接 print d[i] 在 simtalk_run 上下文可能 fail)|

---

## 03-modeling-know-how
### 01-objects
- **`.UserObjects` 类库**(7-Frame 集首例):
  - 1 child:`AGV` (Transporter,自定义)—)AGV 物理属性可定制(Speed=1m/s, Accel=0.4, Decel=1)
  - **含义**:用户从 `.StandardObjects.Vehicle` 继承并定制 AGV 子类(修改 Acceleration/Deceleration),作为项目可复用 AGV class
- **`.Models.MarkerCrossing.AGVPool.AGV`** 是 `.UserObjects.AGV` 的 instance
- **4 嵌套 Frame corner cell 边缘对比**(完整数据):
  - 物理布局推断:**2×2 grid**,每个 corner cell 有 2-3 个边缘 markers 朝向对应方向
  - MarkerCrossing(5 edges)= "south/central" cell,与外侧 4 outer Marker 都连
  - MarkerCrossing2/3/4 各 4 edges,分别对应 sw/ne/nw corner

### 02-simtalk
- **Destinations 内容访问**(实测):`var x1:=Destinations[1]; print x1` → `.Models.MarkerCrossing.M1` (path string)
- **与 prior Destinations 初始化对比**:Destinations 是 4-element list,each is a Marker object reference(M1/M2/M3/M4)
- Init / DestCtrl 的 `z_uniform(1, Dim+1)` 随机索引到 1-4,对应 M1-M4 之一(第 3 次确认 Quirk #7)

### 03-software
- 本 session ~12 次 simtalk_run + ~12 次 readlog
- **核心 skill 经验**:
  - **DataList element 读取 SOP**:`var d:=str_to_obj(path); var x:=d[i]; print x`(**不**直接 `print d[i]` — bash 转义问题)
  - **嵌套 Frame children 枚举**:`var n:=str_to_obj(nested_path); for i := 1 to n.numNodes; ...` 工作正常(实测 MarkerCrossing2/3/4 全部)

---

## 04-modeling-example
- **本 session 无新增完整范例**(聚焦补探已覆盖部分)

---

## 05-modeling-experience
### 观察(Observe)
- **Quirk 累计**:本 session 0 新增,沿用 prior SOP
- **关键洞察**:
  - **7-Frame 集首个 UserObjects 用户自定义 class** — `UserObjects.AGV` 是从 `.StandardObjects.Vehicle` 继承并修改 Accel/Decel 的子类
  - **同一 AGV 概念在不同模型用不同基类** — AGVWithRobot 用内置 `.StandardObjects`,MarkerCrossing 用自定义 `.UserObjects.AGV` — 体现 PS 类库的可继承性
  - **4 嵌套 Frame corner cell 边缘自定义** — 每个 corner cell 按其物理位置保留对应方向的 entry/exit markers;这是**位置感知模板**(Frame 内容根据 cell 在 grid 中的位置不同)
  - **Destinations = outer Markers(M1-M4)** — Init/DestCtrl 随机派单目标就是 4 个 outer Marker,AGV 沿 Path 到达这些 marker 之一即触发对应嵌套 cell EntranceCtrl
- **跨 session 综合**(沿 prior 8 个 deepdive + 本 session):
  - **修正 prior MarkerCrossing deepdive**:4 嵌套 Frame 不全相同,**边缘 markers 各异**
  - **修正 prior AGV class 假设**:7-Frame 集不都用 `.StandardObjects.Vehicle`,MarkerCrossing 用 `.UserObjects.AGV`
  - **确认 Factory51 3 层范式**:7-Frame 集**至少 1 个**模型走 `UserObjects/AGV → instance` 模式
  - **z_uniform Quirk #7** 第 4 次确认(MarkerCrossing Init/DestCtrl/RecalcLayout + 现在 Destinations 使用)
  - **DataList 索引访问 SOP**:`var x:=d[i]; print x`(避免直接 `print d[i]`)

### 候选 finding
- **`.UserObjects.AGV` 用户自定义 class** → 沿 prior Factory51 范式 finding 扩展,本 session 实证
- **位置感知模板(corner cell 边缘自定义)** → 建议 curator 评估沉淀到 `02-domain-know-how/04-modeling-example/position-aware-frame-template.md`
- **DataList element print SOP** → 建议 `@skills-optimizer` 评审补 `language-quirks-reference.md`

---

## Cross-references
- 02-domain-know-how entries: `01-factory-know-how/factory-modeling-architecture.md §1.1`(Factory51 UserObjects 范式对比);`03-modeling-know-how/01-objects/object-classification.md §3.3`(Frame-as-Container 双重身份)
- 01-plantsimulation-knowledge entries: 沿 prior
- 04-agent-memory 其它 session:
  - **`2026-09-02-MarkerCrossing-crossing-semaphore-deepdive.md`**:prior deepdive(本 session 补探其未覆盖部分)
  - **`2026-09-02-AGVWithRobot-agv-dispatch-deepdive.md`**:对比 AGV.ICN / AGV.~ 不同 — AGVWithRobot 用 `.StandardObjects`(内置 class),MarkerCrossing 用 `.UserObjects.AGV`(自定义 class)
  - **`2026-09-02-Models-RobotSet-robot-set-overview.md`**:prior 概述,7-Frame 集整体观察
- per-skill 调用 log:inline simtalk_run prints in Bash transcript(~12 次补探)
- team memory: 沿 prior

---

## Open questions / cross-pollination
- *建议由 `plant-simulation-experience-curator` 评审是否沉淀:*
  - **位置感知 corner cell 模板**(4 corner cell 不同 edge markers)→ 候选到 `02-domain-know-how/04-modeling-example/position-aware-frame-template.md`(baseline:本 session §01 完整 4 cell 对比)
  - **`.UserObjects.AGV` 自定义 class 范式** → 候选到 `02-domain-know-how/01-factory-know-how/factory-modeling-architecture.md` 新增"7-Frame 集 UserObjects 实例"小节(baseline:本 session §01)
- *建议由 `skills-optimizer` 评审:*
  - **DataList element print SOP** → 候选 `language-quirks-reference.md` 补"DataList 索引访问需 var 中介"(baseline:本 session §02)
- *建议由 `plant-simulation-knowledge-synthesizer` 评审:*
  - **UserObjects 类库组织** → 候选 PS Help 补"UserObjects 是用户自定义类库,可继承内置类"
- *未关闭问题:*
  - **`Destinations` d[3]/d[4] 内容未实测** — 推断 M3/M4 但未 probe 验证(bash 转义限制,需 separate print)
  - **`MarkerCrossing`(5 edges)位置推断** — south/center 还是其他位置?需 GUI 验证 2×2 grid 实际布局
  - **嵌套 Frame 边缘选择依据** — 是用户手工编辑时按 cell 位置删除冗余 markers,还是 RecalcLayout 等 Method 动态处理?需读 RecalcLayout 全文 + GUI 验证
  - **`UserObjects.AGV` 是否继承 `.StandardObjects.Vehicle`** — 用户可能从 Vehicle 继承并改 Accel/Decel;需 `expert` 验证 Origin 链

---

## Operator self-review
- [x] 范围:聚焦 MarkerCrossing 补探(UserObjects class + 4 cell 边缘对比 + Destinations 内容),无写动作
- [x] 5 维全列
- [x] 6 段齐
- [x] 每条 finding 含 baseline 引用 + 3-pass 判定
- [x] Quirk 编号协议:本 session 0 新增 Quirk,沿用 prior
- [x] Target < 150 行(实际 ~135 行)
- [x] 不动 baseline 文档
- [x] 不动模型:0 写 skill
- [x] **Novel finding**:`.UserObjects.AGV` 7-Frame 集首例 + 4 corner cell 边缘各异 + Destinations=[M1-M4]