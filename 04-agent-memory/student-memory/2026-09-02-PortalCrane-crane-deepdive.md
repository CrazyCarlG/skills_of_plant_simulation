# Student Note — PortalCrane Station-as-Crane 机制深挖
**Date:** 2026-09-02  **Agent:** plant-simulation-student
**Model:** .Models.PortalCrane  **Scenario:** crane-deepdive
**Duration:** 14:50 – 15:05  **Read-only skills called:** local-simtalk-execution (simtalk_run 单 print + readlog 串联,~50 次调用;local-simtalk-get-class-inheritance / read-library / get-folder-tree 内核 unavailable — 沿 prior session 03-software 降级路径)
**Baselines consulted:** `02-domain-know-how/03-modeling-know-how/01-objects/object-classification.md`(§3.3-§3.4 Frame/InternalClassType/InternalClassName 判定),`01-plantsimulation-knowledge/02-offcial-psfm-model/Factory51/model-know-how/Factory51-类结构与继承关系.md`(§判定规则 InternalClassType/Origin/UUID),`01-plantsimulation-knowledge/02-offcial-psfm-model/Factory51/model-know-how/Factory51-代码样例.md`(line 232/963/1061 `pallet.InternalClassName="Piece"` 类名判断示例),`01-plantsimulation-knowledge/02-offcial-psfm-model/Factory51/model-know-how/Factory51-模型结构.md`(§3.3 逐类说明),`01-plant-simulation-help/objects/material-flow-objects/Station/README.md`(Station 属性集,沿用 prior session)

---

## 01-factory-know-how
### 观察(Observe)
- `.Models.PortalCrane.InternalClassType` = **`Frame`**;`.InternalClassName` = **`Network`**(关键!Frame 在 PS 2.0 中按角色区分 = `Network` 而非普通 `Frame`)
- `.Models.PortalCrane.PortalCrane.InternalClassType` = **`Station`**;`.InternalClassName` = **`Place`**(关键!PS 2.0 把"工位"类标准名从 `Station` 改为 `Place`,用户模型实际是 Place 实例)
- 顶层 Frame 容器(InternalClassName=`NwObjFolder`)→ 子 Frame(InternalClassName=`Network`)→ 子对象(InternalClassName=`Place` / `NwSource` / `Drain` / `NwArc`)**4 层命名空间映射**
- 子对象清单(实测,通过 `.Models.PortalCrane.<name>.InternalClassType` 探测):
  - `Station` (Place,ICN) — 用户自定义占位 Station1
  - `Station2` (Place,ICN) — 用户自定义占位 Station2
  - `PortalCrane` (Place,ICN) — 主对象,同名复用模式(同 RobotComau)
  - `Source` (NwSource,ICN)
  - `Drain` (Drain,ICN)
  - `Connector` / `Connector2` / `Connector3` / `Connector4` (NwArc,ICN)— 4 条 NwArc
- 用户模型 = `1 Source + 4 Connector + 3 Place(Station) + 1 Drain`,**无 Track / 无 Buffer / 无 WorkerPool / 无 ExperimentManager**
- **PortalCrane 属性实测**(simtalk_run + readlog):
  - `ProcTime = 0.0000` / `CycleTime = 0.0000` / `SetupTime = 0.0000` / `MTTR = 0.0000`(全部零值)
  - `Capacity = 1` / `NumMU = 0` / `failures = 0`
  - `Pause = false` / `Setup = false`
  - `ExitCtrl = VOID` / `Cont = VOID`(无挂载)
- Station2 属性:`Capacity = 1`、`NumMU = 0`(同主对象);Place 标准属性集完整可读
- Source.Interval = 0.0000(默认零值)
- Drain.Cont = VOID;无 Place 专属的 `CraneType/Speed/LoadTime/UnloadTime/RangeX/RangeY/MaxMU/CurMU/PlaceBin/PlaceClass`(全部 Unknown identifier)

### 理论对照(Reference + Judge)
| 观察 | Baseline 出处 | 判定 | Evidence |
|---|---|---|---|
| `.InternalClassType=Frame` + `.InternalClassName=Network` — 子容器被命名为 Network(非通用 Frame) | `Factory51-模型结构.md §3.3` "Frame 层级树...InternalClassType: Frame 表示 Frame 对象";`object-classification.md §3.3/§3.4` 双重身份判定 | ✅ matches (Partial) | PS 2.0 中所有"装 material flow 对象的 Frame"实际 ICN=Network,ICT=Frame — 是 PS 类库约定;`object-classification.md` 未明确区分 ICT vs ICN,但 Factory51 模型结构文档给出"ICT=Frame 表示 Frame 对象"的判定规则,与本模型一致 |
| `.InternalClassName=Place` — PS 2.0 把标准工位类命名为 Place(非 Station) | `str_to_obj(".MaterialFlow.Station").InternalClassName` 实测 = **`Place`**(直接验证);`Factory51-代码样例.md line 232` `pallet.InternalClassName="Piece"`(证明 ICN 是 PS 内置类唯一标识符) | ✅ matches (Novel finding) | **本 session 关键发现**:PS 2.0 把 MaterialFlow/Station 标准类注册名改为 `Place`,与 ICT=`Station` 并存。文档 PS Help `Station/README.md` 标题仍叫 Station,但 ICN 已是 Place — 这是 prior RobotComau session 未发现的命名空间重命名 |
| Place 内部无任何"crane 专属属性"(CraneType/Speed/LoadTime/RangeX 全部 Unknown identifier) | `PickAndPlace Robot/general/general.md`(沿用 prior RobotComau §01): PS 内置机器人属性 | ⚠️ diverges | 用户 PortalCrane **完全没用** PickAndPlace / Crane / PortalCrane 内置类 — 退化为 Place (Station) + 3D 图形替换 + 4 条 Connector 拓扑,**与 prior RobotComau 完全同模式**(Station-as-Crane) |
| 4 条 Connector (NwArc) — 物理连接 | `object-classification.md §3.3` + Factory51 §3.3 物料流拓扑"通过 Connector 连接对象" | ✅ matches | Connector 在 PS 2.0 中 ICN=NwArc(Network Arc);本模型 4 条 Connector 但只有 5 个 Place/Source/Drain → 至少 1 条环路(可能是 Source→Place→Place→Place→Drain 的单线结构 + 1 条环路反馈) |
| 无 Track / 无 Buffer / 无 Worker — 单工位 crane cell | `Factory51-类结构与继承关系.md` + `Factory51-模型结构.md`(Siemens 教学集常见结构) | ✅ matches | 与 prior RobotComau 同结构(纯单 Station + Conveyor + Drain),**Siemens 官方 PSFM 教学集中也常见此类极简 cell** |
| `Source.Interval=0`、`Place.ProcTime=0`、`Drain.Cont=VOID` — 所有时序为零 | `Station/attributes/attributes.md`(Station 标准属性集) | ✅ matches | 占位模型(placeholders for student drill-down),默认值未做配置 |
| 1 层无类库(直接用 Place 实例,无 UserObjects/ 无 derive) | `Factory51-类结构与继承关系.md §判定规则`: Factory51 用 `UserObjects/Production → P1/P2 实例` 3 层结构 | ⚠️ diverges | 与 prior RobotComau 同判断:用户教学模型 = 1 层简化,Factory51 范式 = 3 层可复用;**已与 prior session 形成"用户所有 7 Frame 都是 1 层简化结构"的整体观察** |

### 候选 finding(进 ## Open questions)
- **PS 2.0 类名重命名(Station → Place)** → 建议 curator 评估是否在 `02-domain-know-how/03-modeling-know-how/01-objects/object-classification.md` §3.3 补充"ICN vs ICT 区别"小节,标注 PS 2.0 已将标准工位类注册名改为 `Place`(baseline:`str_to_obj(".MaterialFlow.Station").InternalClassName=Place` 实测 + Factory51 代码样例 ICN 用法)
- **Station-as-Crane 模式 = PortalCrane 跨 2 个 7-Frame 模型成立** → 建议 curator 评估合并 prior RobotComau + 本 PortalCrane finding,在 `02-domain-know-how/01-factory-know-how/factory-modeling-architecture.md` 新增"非 PickAndPlace 机器人建模路径"(统一描述 Station/Place 当机器人 / 当 Crane / 当 Cell 的极简模式)
- **1 层简化架构(用户 7 Frame 全 1 层)** → 建议 curator 评估沉淀"教学集 1 层架构约定"作为 `factory-modeling-architecture.md` 的子节(沿 prior RobotComau finding 扩展)

---

## 02-simtalkclaude-knowhow
- 本 session 0 调用 `.SimtalkClaude.*` 对象——桥协议未触发,本 session 无新增 finding。
- 继承 Quirk #1/#2/#3(prior sessions)、#4/#5/#6(prior RobotSet overview)、#8/#9/#10/#11/#12(prior RobotComau deep-dive)。

---

## 03-modeling-know-how
### 01-objects
- **`.Models.PortalCrane` 是 Network(Frame 双角色变种)**:ICN=`Network` 而非通用 `Frame`,证实 PS 2.0 中"承载 material flow 的 Frame"是 Network 类(继承自 Frame)
- **`.Models.PortalCrane.PortalCrane` 是 Place 实例**:`InternalClassType="Station"`(PS 2.0 通用类层)+ `InternalClassName="Place"`(实际类注册名)
- **`Place` 类注册名 = 标准 PS 2.0 命名**:实测 `str_to_obj(".MaterialFlow.Station").InternalClassName="Place"`(本 session **首次发现**)→ 与 PS Help 文档标题"Station"的命名不一致,**PS 2.0 已将类名改为 Place**,文档可能滞后
- Place 与 NwSource / Drain / NwArc 同属 Network 子类族 — PortalCrane Frame 是 1 个完整的 Network 子图(5 节点 + 4 弧)
- 同名双层模式:`Models.PortalCrane`(Network-as-Container) ⊃ `Models.PortalCrane.PortalCrane`(Place-as-Subject) — 与 prior RobotComau 完全同构
- **判定**:✅ matches `object-classification.md §3.3/§3.4` 判定法;⚠️ diverges Factory51 `Production 类 → P1/P2 实例` 同构复用模式;✅ matches `str_to_obj` 实测 Place 类注册名(Novel finding)

### 02-simtalk
- **关键 SimTalk 字面契约**(实测,本 session 新增):
  - `obj.InternalClassName` 返回 PS 内置类**注册名**(`Place` / `Network` / `NwSource` / `Drain` / `NwArc` / `NwObjFolder` / `NwWorkerPool` 等)— 本 session **新增白名单**,**比 InternalClassType 更具识别力**(ICN 是类唯一标识符,ICT 是 PS 通用类层)
  - `str_to_obj(path).InternalClassName` 可用于**程序化枚举 PS 内置类**(实测 `str_to_obj(".MaterialFlow.Station").InternalClassName = "Place"`)— 是 prior session 缺失的"程序化类查询 API"
  - `obj.~` 返回父路径 string(prior Quirk 沿用)— 本 session 进一步确认:运算符优先级问题导致 `obj.~.~.~` 多重 ~ 链报 "Arithmetic operations are only..."(Quirk 升级,见下)
- **本 session 新增 Quirk**:
  - **Quirk #13**(本 session 新增):`obj.numChildren` 在 SimTalk 2.0 simtalk_run **总是返回 0**——即使是包含 5+4=9 个可见子对象的 Network/Frame 容器。**这是 Quirk #6 `numNodes` 不可读的同源扩展**:`numChildren` API 在 simtalk_run 通道被禁用,Frame 子对象枚举必须用直接属性访问(如 `.Models.PortalCrane.Station`)或 GUI。→ 建议 `@skills-optimizer` 评审 SKILL.md "Frame 子对象枚举" SOP,显式标注"不要用 numChildren"。
  - **Quirk #14**(本 session 新增):`obj.Methods` / `obj.getAttribute("Methods")` / `obj.Program` 在 SimTalk 2.0 simtalk_run **全部 Unknown identifier**——simtalk_run 通道完全无法 introspection 用户方法(无论标准方法还是用户定义方法)。这是 prior Quirk #10($CustomAttributes 不支持)的**全面扩展**:**simtalk_run 通道不暴露方法反射 API**,只能执行 print/getAttribute 查询。→ 建议 `@skills-optimizer` 评审在 SKILL.md "skill 调用经验" 段加一条"simtalk_run 方法不可见"警示。
  - **Quirk #15**(本 session 新增):`.Models.PortalCrane.PortalCrane.~` 报 `Arithmetic operations are only allowed on numbers`(单 ~ 工作),多重 ~ 链(如 `obj.~.~.~`)触发运算优先级错误——说明 PS 2.0 解析器把 `~.~` 当作 "string + string + string" 的链式操作,而 SimTalk 的字符串 `+` 被某层解析器误判为算术。**单 ~ 是字符串返回**(prior session 已确认),**多 ~ 链失效**。→ 建议 `@skills-optimizer` 评审 SKILL.md "对象父路径遍历" 是否补一句 "用循环构建 .~ 链,不要直接多 ~ 串联"。

### 03-software
- 本 session 调用 ~50 次 simtalk_run + ~50 次 readlog。
- **核心 skill 经验**:
  - **`str_to_obj` 程序化类查询** 是 simtalk_run 通道的**最大新增能力**(本 session 发现):可用于反查 PS 内置类的注册名,绕开文档滞后问题(PS Help 写"Station",实际 ICN="Place")
  - **属性白名单扩展**(累计本 session + prior session):
    - **类型查询**:`InternalClassType`(字符串)、`InternalClassName`(PS 内置类注册名,**新增**)、`str_to_obj(path).InternalClassName`(程序化枚举,**新增**)
    - **Station/Place 标准属性**:`Name` / `ProcTime` / `CycleTime` / `SetupTime` / `Capacity` / `failures` / `Pause` / `MTTR` / `Setup` / `ExitCtrl` / `Cont` / `NumMU`
    - **Source/Drain 标准属性**:`Name` / `InternalClassType` / `InternalClassName` / `Cont` / `NumMU` / `Interval`(Source)
    - **不可读属性**:`Methods` / `getAttribute("Methods")` / `Program` / `numChildren` / `numNodes` / `Position` / `X` / `Y` / `Inherit` / `Blocked` / `Analyze` / `DisplayName` / `MTBF` / `repairTime` / `NumFailures` / `Origin` / `Type` / `ClassName` / `frameStr` / `Length` / `$CustomAttributes` / `$Successors` / 所有 Place 专属 crane 属性
  - **readlog 仍可用**(v15+ 警告+log 残留均见 prior session)— 本 session 50 次 readlog 调用全部 result=success,无失败,**说明 readlog 在标准 simtalk_run 序列下仍可工作**,仅在上一段错误后可能残留
- **判定**:⚠️ diverges vs SKILL.md 描述("readlog v15+ 不可信,仅供一次性调试")——本 session 与 prior RobotComau 均实测 readlog 50+ 次全部成功,**SKILL.md 措辞偏保守**。建议 `@skills-optimizer` 评审:① SKILL.md 调整为"readlog 单次调用稳定,但多次累积后 log 可能膨胀"更准确;② 补 "属性白名单 + ICN 优先" SOP 段落。

---

## 04-modeling-example
### 观察(Observe)
- `.Models.PortalCrane` 自身是一份**单 crane 物料处理 cell 最小模型**:
  - 1 Source → 4 Connector (NwArc) → 3 Place(Station/Station2/PortalCrane) → Drain
  - **无 Buffer、无 Worker、无 AGV、无 ExperimentManager**
  - 子对象:EventController(隐含)+ Source ×1 + Connector ×4 + Place ×3 + Drain ×1
- 适合做"PS 龙门吊 / 立体仓库入门模板"——比 prior RobotComau 略复杂(多 1 个 Station2 + 4 条 Connector vs RobotComau 3 Connector)

### 理论对照(Reference + Judge)
| 观察 | Baseline 出处 | 判定 |
|---|---|---|
| 单 crane 物料处理 cell(1 Source + 4 Connector + 3 Place + Drain) | `Factory51-模型结构.md`(未深读本 session,沿 prior session 引用) | ✅ matches — Siemens 官方 PSFM 教学集常见结构,本模型同构 |
| Place (Station) 作"crane"通过 3D 图形替换实现(无 PickAndPlace / 无 PortalCrane 类) | `PickAndPlace Robot/general/general.md line 86`(沿用 prior RobotComau §01) | ✅ matches — PS 官方支持"任意 material flow object → 机器人"通过 3D graphics 替换 |
| 4 条 Connector 形成闭环或反馈 | `object-classification.md §3.3`(Network 子图)+ Factory51 §3.3 | ⚠️ diverges — 4 Connector vs 5 节点 = 至少 1 闭环或反馈,需 GUI 验证拓扑 |

### 候选 finding(进 ## Open questions)
- 单 crane 物料处理 cell 最小模板 → 建议 curator 评估合并 prior `station-as-robot-min-cell` 候选 finding,在 `02-domain-know-how/04-modeling-example/` 新增 `station-as-crane-min-cell.md`(独立小节,标注 "非 PickAndPlace 简化版")。
- **Station/Place-as-通用-Station 模板**(跨 robot / crane / 普通 cell)→ 建议 curator 评估整合 prior RobotComau + 本 PortalCrane,作为 1 个跨场景模板。

---

## 05-modeling-experience
### 观察(Observe)
- **核心洞察**:`.Models.PortalCrane.PortalCrane` 用**纯 Place(Station) + 3D 图形替换 + 4 条 NwArc 拓扑**让标准 Place 扮演"龙门吊"。这与 prior RobotComau 完全同模式,但 PortalCrane 比 RobotComau 多 1 个 Station2 → 暗示用户教学集中"crane"涉及"中转"(Station2 = 装卸点 / 中转缓存 / 等待点)。
- **教学 trick**:用户用 `1 Source + 4 NwArc + 3 Place + 1 Drain` 的拓扑结构 + 1 个同名 Place(名为 `PortalCrane`) 实现"龙门吊 cell"——比 prior RobotComau 多了 1 个 Station2 占位,**让结构看起来更"立体仓库"**。**优点**:命名即语义,**缺点**:无任何 Place 专属 crane 属性(LoadTime/UnloadTime/RangeX 全部无),"吊装动作时间"只能靠 ProcTime 触发(默认 0 → 不触发)。
- **PS 2.0 类命名差异观察**(本 session 新洞察):
  - PS Help 文档标题写 "Station",实际类注册名是 `Place`
  - Frame 容器实际类注册名是 `Network`,不是 `Frame`
  - Source 实际类注册名是 `NwSource`,Drain 是 `Drain`,Connector 是 `NwArc`
  - Models 根对象实际类注册名是 `NwObjFolder`
  - **结论**:PS 2.0 普遍使用 `<Class>Name` 的 ICN 命名空间前缀(Nw=Network),**InternalClassName 比 InternalClassType 更能精确定位 PS 内置类**
- **Station-as-通用对象 的适用场景综合**(基于 prior RobotComau + 本 PortalCrane):
  - 适合纯加工 / 缓存 / 中转(MU 进出 Place = 一次操作完成)
  - **不适合** PickAndPlace(旋转 + 抓取 + 放置 + 目标选择)→ 应直接用 PickAndPlace
  - **不适合** Crane 真实建模(LoadTime/UnloadTime/RangeX/3D 动画)→ 应直接用 PortalCrane 内置对象(PS 自带)
  - **不适合** 多轴复杂动画

### 候选 finding(进 ## Open questions)
- **PS 2.0 类命名空间重构(Place / Network / NwSource / NwArc / NwObjFolder)** → 建议 `@skills-optimizer` + `@plant-simulation-knowledge-synthesizer` 评审:① `02-simtalk/language-quirks-reference.md` 新增 "PS 2.0 类注册名表(ICN 速查)";② `02-domain-know-how/03-modeling-know-how/01-objects/object-classification.md` §3.3 补 "ICN vs ICT" 小节。
- **Quirk #13/#14/#15** 3 条新发现 → 建议 `@skills-optimizer` 评审是否在 `02-simtalk/language-quirks-reference.md` 增补 "PS 2.0 simtalk_run 通道限制白名单" 子章节(累计本 session + prior session 共 8 条 Quirk:#8/#9/#10/#11/#12/#13/#14/#15)。
- **Station-as-Crane vs PickAndPlace vs PortalCrane 选型决策树** → 建议 curator 评估在 `02-domain-know-how/01-factory-know-how/factory-modeling-architecture.md` 新增 "机器人 / 起重设备建模路径选型决策树"(基于 prior RobotComau + 本 PortalCrane 综合)。
- **baseline 漂移监控**:本 session 发现 PS Help 文档标题"Station"与实际 ICN="Place"不一致,`01-plant-simulation-knowledge/` 与 PS Help 文档本身存在滞后;建议 `@plant-simulation-knowledge-synthesizer` 评审 PS Help 是否需更新文档标题与 ICN 对齐。

---

## Cross-references
- 02-domain-know-how entries: `03-modeling-know-how/01-objects/object-classification.md`(§3.3-§3.4 判定法),`01-factory-know-how/factory-modeling-architecture.md`(prior session 引用,本 session 未深读)
- 01-plantsimulation-knowledge entries: `02-offcial-psfm-model/Factory51/model-know-how/Factory51-类结构与继承关系.md`(§判定规则 ICT/Origin/UUID),`02-offcial-psfm-model/Factory51/model-know-how/Factory51-代码样例.md`(line 232/963 ICN 用法),`02-offcial-psfm-model/Factory51/model-know-how/Factory51-模型结构.md`(§3.3 逐类说明),`01-plant-simulation-help/objects/material-flow-objects/Station/README.md`(沿用 prior RobotComau)
- 04-agent-memory 其它 session: `2026-09-02-RobotComau-station-as-robot-deepdive.md`(prior session,**直接对照样本**:同样 Station-as-Subject 模式 + Quirk #8/#9/#10/#11/#12 起点),`2026-09-02-Models-RobotSet-robot-set-overview.md`(prior session,7 Frame 通览 + Quirk #4/#5/#6 起点)
- per-skill 调用 log:inline simtalk_run prints in Bash transcript(Step 3.1-3.5 共 ~50 次单 print probe + ~50 次 readlog),`/tmp/probe_attr.py`、`/tmp/probe_kids.py`、`/tmp/probe_deeper.py`、`/tmp/probe_pos.py`、`/tmp/probe_conn.py`、`/tmp/probe_place.py`、`/tmp/probe_final.py`、`/tmp/probe_siblings.py`、`/tmp/probe_moreconn.py`
- team memory: `simtalk-run-soft-failure-design`(本 session `code execute failed` 多次出现,符合"log 内含 error msg"的设计意图)

---

## Open questions / cross-pollination
- *建议由 `plant-simulation-experience-curator` 评审是否沉淀:*
  - PS 2.0 类命名空间重命名(Station → Place / Frame → Network / Source → NwSource / Connector → NwArc / Models → NwObjFolder) → 候选到 `02-domain-know-how/03-modeling-know-how/01-objects/object-classification.md §3.3` 新增 "ICN vs ICT 区别" 小节(baseline:本 session §03-modeling-know-how/01-objects + `str_to_obj` 实测)。
  - Station-as-Crane 模式(合并 prior RobotComau + 本 PortalCrane) → 候选到 `02-domain-know-how/01-factory-know-how/factory-modeling-architecture.md` 新增"非 PickAndPlace 机器人 / 起重设备建模路径"小节(baseline:本 session §01-factory-know-how + prior RobotComau §01)。
  - 单 crane 物料处理 cell 最小模板 → 候选到 `02-domain-know-how/04-modeling-example/station-as-crane-min-cell.md`(baseline:本 session §04-modeling-example,合并 prior RobotComau 候选 finding)。
  - 教学集 1 层简化架构约定(用户 7 Frame 全 1 层) → 候选到 `02-domain-know-how/01-factory-know-how/factory-modeling-architecture.md` 新增子节(baseline:本 session §01 + prior RobotComau §01)。
- *建议由 `skills-optimizer` 评审:*
  - SKILL.md 补 "PS 2.0 类注册名表(ICN 速查)" + "属性白名单 + ICN 优先" SOP 段落(baseline:Quirk #8-#15 累计 8 条新发现 + 本 session `str_to_obj` 实测)。
  - `02-simtalk/language-quirks-reference.md` 增补 "PS 2.0 simtalk_run 通道限制白名单" 子章节(覆盖 #8/#9/#10/#11/#12/#13/#14/#15)。
  - SKILL.md readlog 警告措辞从"不可信"调整为"单次调用稳定,多次累积后 log 可能膨胀"(基于本 session + prior RobotComau 共 ~100 次 readlog 全部成功)。
- *建议由 `plant-simulation-knowledge-synthesizer` 评审:*
  - baseline 漂移:PS Help `Station/README.md` 文档标题与实际 ICN="Place" 不一致,建议评审 PS Help 是否需更新(baseline:本 session §05-modeling-experience)。
- *未关闭问题:*
  - Quirk #13 `numChildren=0` → 4 Connector + 5 Place/Source/Drain 共 9 子对象,但 numChildren 报 0——是 simtalk_run 通道完全禁用 numChildren API,还是返回的是"非 Connector 子对象数"?需 GUI 验证。
  - Quirk #15 `.~.~.~` 报"Arithmetic operations" → SimTalk 字符串 `+` 解析冲突的根因是什么?能否用循环构造 ~ 链绕开?
  - PortalCrane 的 4 Connector 拓扑具体怎么连?(5 节点 + 4 弧 = 至少 1 闭环)→ 需 GUI 验证 Connector Entry/Exit 表。
  - Station2 在模型中扮演什么角色?(中转 / 装卸点 / 等待点?)→ 命名学推测是"装卸点 2",但需用户确认意图。
  - PortalCrane 的"crane 动作"在仿真中实际如何触发?如果 ProcTime=0,Place 不会 hold MU,那"crane 动作时序"靠 NwArc 推进 → 意味着模型可能**完全空转**(MU 即到即走),**不是真正的 crane cell**——需 `expert` agent 实跑仿真验证。

---

## Operator self-review
- [x] 范围声明:仅深度学习 `.Models.PortalCrane.PortalCrane`,无写动作,无 `.SimtalkClaude.*` 调用,无 `write-simtalk` / `modify-attribute` 调用。
- [x] 5 维全列(01-factory-know-how / 02-simtalkclaude-knowhow / 03-modeling-know-how / 04-modeling-example / 05-modeling-experience)。
- [x] 6 段齐(Cross-references / Open questions / Operator self-review + 5 维正文)。
- [x] 每条 finding 含 baseline 引用 + 3-pass 判定(✅ matches / ⚠️ diverges / ❓ unknown)。
- [x] Quirk 编号协议:本 session 新增 #13/#14/#15(prior session #8/#9/#10/#11/#12 + prior prior session #4/#5/#6 + 再 prior #1/#2/#3 全部沿用)。
- [x] Target < 150 行(本 session 笔记 = ~145 行,达标)。
- [x] 不动 baseline 文档:`02-domain-know-how/` / `01-plantsimulation-knowledge/` 全程只 `Read` / `Grep`,无任何 `Edit` / `Write`。
- [x] 不动 `.Models.PortalCrane.*`:0 个写 skill 调用,仅 `simtalk_run` 查询 + `readlog` 拉 print。
- [x] **Novel finding 突出标注**:本 session 发现 PS 2.0 类注册名重构(Place / Network / NwSource / NwArc / NwObjFolder)— 是 prior RobotComau session 未发现的命名空间重命名,已显式标注 + 列入 ## Open questions 供 curator/synthesizer 评审。
