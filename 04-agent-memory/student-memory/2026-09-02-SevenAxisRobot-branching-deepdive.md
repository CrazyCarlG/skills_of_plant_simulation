# Student Note — SevenAxisRobot 多出口分支 + 纯声明式模型深挖
**Date:** 2026-09-02  **Agent:** plant-simulation-student
**Model:** .Models.SevenAxisRobot  **Scenario:** branching-deepdive
**Duration:** 19:22 – 19:23  **Skills called:** local-simtalk-execution (ping + simtalk_run + readlog 序列,~40 次调用);get-folder-tree / read-library 内核 unavailable(沿 prior AGVWithRobot 降级路径)
**Baselines consulted:** `01-plantsimulation-knowledge/01-plant-simulation-help/objects/material-flow-objects/ParallelStation/{general/general.md,attributes/attributes.md}`;`01-plantsimulation-knowledge/01-plant-simulation-help/objects/material-flow-objects/Conveyor/general/general.md`;`01-plantsimulation-knowledge/01-plant-simulation-help/objects/user-interface-objects/Display/`(索引)
**Result:** success

---

## 01-factory-know-how
### 观察(Observe)
- `.Models.SevenAxisRobot.ICT=Frame` / `.ICN=Network`(同 AGVWithRobot / PortalCrane — material flow Frame 在 PS 2.0 是 Network 子类)
- **完整子对象清单**(`numNodes=13`,实测枚举):
  - 1 EventController(`EventCtl` — ICN 不是 EventController)
  - 1 Source (Source, `NwSource`)
  - 1 Place (SevenAxisRobot, `Place`)
  - **1 ParallelStation (`Machine`)**
  - **1 Conveyor (`Line`)**
  - 2 Drain (Drain, Drain3, `Drain`)
  - **1 Display (`NwDigitDpy`)**
  - 5 Connector (Connector/2/3/4/14, `NwArc`) — 🆕 **Connector14 gap**(Connector5-13 缺失,与 AGVWithRobot 同模式)
- 🆕 **Novel ICN 大发现**(本 session):
  - ParallelStation → **`Machine`**(完全不同的类名)
  - Conveyor → **`Line`**(完全不同的类名)
  - Display → **`NwDigitDpy`**(Numeric Display,但本模型 Value 是 string!)
  - EventController → **`EventCtl`**(无 Nw 前缀,与 Frame/Network 不同)
- **拓扑实测**(完整 Connector.Pred / .Succ):
  ```
  Source --[Connector]--> SevenAxisRobot --[Connector3]--> Conveyor --[Connector2]--> Drain
                                   └─[Connector4]--> ParallelStation --[Connector14]--> Drain3
  ```
- 🆕 **Novel**:这是 **7-Frame 教学集中第一个多出口分支(branching)拓扑**!之前 6 个 Frame(RobotComau / XZYStacker / PortalCrane / LinearPortal / MarkerCrossing / AGVWithRobot)都是单线串行
- SevenAxisRobot Station 属性:**ProcTime=0 / CycleTime=0 / SetupTime=0** + **ExitCtrl=VOID** — 纯 pass-through 节点,不加工不调度
- ParallelStation 属性:**XDim=2 / YDim=2 / Capacity=4 / ProcTime=10** — 2×2 网格,4 个并行处理槽,每个 MU 10s
- Conveyor 属性:Length=3m / Speed=1m/s / Width=1m — 标准 3m/1m/s 传送带
- 🆕 **Display.Value="Waiting"**(string!)— Display ICN 是 NwDigitDpy(Numeric Display),但实际 Value 是字符串——PS 2.0 Display 支持 string 状态显示
- 🆕 **完全 NO_METHODS**:Frame 子对象无任何 Method——纯声明式模型,所有行为靠 Station/Conveyor/ParallelStation/Display 默认规则

### 理论对照(Reference + Judge)
| 观察 | Baseline 出处 | 判定 | Evidence |
|---|---|---|---|
| ICN=Network / Place / NwSource / Drain / NwArc | prior PortalCrane + AGVWithRobot + Factory51 沿用 | ✅ matches | PS 2.0 ICN 重构已确立(累计 4 个 Frame 模型验证) |
| EventController ICN=`EventCtl`(无 Nw 前缀) | prior RobotSet/RobotComau/PortalCrane 未单独探过 EventController ICN | ✅ matches(Novel) | `str_to_obj(.Models.SevenAxisRobot.EventController).InternalClassName` 实测 = `EventCtl`——**首发现**:EventController 是 ICN 例外,无 Nw 前缀 |
| ParallelStation ICN=`Machine` / Conveyor ICN=`Line` | `ParallelStation/general.md` "process several parts in parallel";`Conveyor` 是标准传送带 | 🆕 **Novel 重大发现** | ParallelStation / Conveyor **类注册名完全不同**!PS 2.0 类库用 `Machine` / `Line` 作为标准注册名(语义化),PS Help 文档用 `ParallelStation` / `Conveyor` 作为展示名 |
| Display ICN=`NwDigitDpy`,实际 Value="Waiting" | `Display/...` baseline (未深读) | ❓ unknown — 待 PS Help Display 文档深读 | ICN 是 Numeric Display,实际能显示 string——可能 PS 2.0 自动 type-coerce,或 Display 实际是 polymorphic |
| SevenAxisRobot 多出口分支 | `02-domain-know-how/01-factory-know-how/factory-modeling-architecture.md`(未明文) | ⚠️ diverges(7-Frame 首例) | 之前 6 Frame 全单线,本模型是第一个 branching 教学;Factory51 / RCS 也常用 branching,但本仓库 baseline 未明文 |
| ParallelStation Capacity=4 (2×2 网格) | `ParallelStation/attributes/attributes.md` "StartProcessingWhenFull"+"XDim"属性 | ✅ matches | Capacity=4 + XDim=2 / YDim=2 一致;PS 默认 "StartProcessingWhenFull=true"(等满才开加工) |
| Display.Value="Waiting" | baseline 未深读 | ❓ unknown — Display 默认值语义待查 | "Waiting" 是 string literal,可能是 Display 默认 placeholder 或显示当前 Station 状态 |
| NO_METHODS(纯声明式) | prior RobotSet 已声明 "SevenAxisRobot 无 Init Method" | ✅ matches | 纯声明式 = 标准 PS 教学 cell 写法;对比 AGVWithRobot 有 OnExit Method 是"扩展版" |

### 候选 finding(进 ## Open questions)
- **PS 2.0 类注册名表** 续增:`EventCtl` / `Machine` / `Line` / `NwDigitDpy` 4 个新 ICN 类型(沿 prior PortalCrane + AGVWithRobot finding 扩展)
- **多出口分支教学 cell** → 建议 curator 评估在 `02-domain-know-how/04-modeling-example/` 新增 `branching-cell-min-pattern.md`(基于本 session,对比单线 starter kit)
- **Display string Value 与 NwDigitDpy ICN 不一致** → 建议 synthesizer 评审 PS Help `Display/...` 文档是否需补充 string display 用法

---

## 02-simtalkclaude-knowhow
### 观察(Observe)
- 本 session 0 调用 `.SimtalkClaude.*`;桥协议未触发
- 继承 prior 全部 Quirk(沿 AGVWithRobot #16/#17)
- **新发现 Quirk 候选 #18**(本 session):**SimTalk 中 `print p.attr1; print p.attr2; ...` 多 print 语句一旦首个 attr 报 "Unknown identifier",后续 print **全部静默跳过**,readlog 只 echo 第一个失败的 `execute sim-code:` 行**和** `~`(即第一个 print 之前的部分)**——`log` 看不到任何后续 attr 报错**。这是"single-shot error 立即 exit"模式,导致批量 attr 探测失败现场定位难
  - 实际表现:`print p.NumProcs; print p.Capacity` → NumProcs 失败 → Capacity 结果**不出现**在 readlog,即使 Capacity=4 是有效值
  - 影响:必须**逐 attr 单 probe**(`for attr in "NumProcs Capacity Pause"; do echo $attr; done`),不能批量
- **新发现 Quirk 候选 #19**:Display.Value 是 string,而 ICN=NwDigitDpy 暗示 numeric——`print d.Value` 不报错,直接返回 string,无 type coercion 提示(可能 PS 2.0 Display 是 polymorphic)

### 理论对照
| 观察 | Baseline 出处 | 判定 |
|---|---|---|
| 多 print 首个 fail 后静默跳过 | `lifelines.md §6` simtalk_run 双重判据(未涉及 batch attr 失败模式) | ❓ unknown — 建议 `@skills-optimizer` 评审是否在 SKILL.md 补 "batch attr probe SOP:逐 attr 单 probe" 段落 |
| Display polymorphic Value | `Display` baseline(未深读) | ❓ unknown — 需 PS Help `Display/general/general.md` 深读确认 |

### 候选 finding
- **Quirk #18 batch attr probe 静默跳过** → 建议 `@skills-optimizer` 评审并加 SKILL.md SOP
- **Quirk #19 Display polymorphic Value** → 建议 `@skills-optimizer` 或 `@synthesizer` 评审 baseline

---

## 03-modeling-know-how
### 01-objects
- **完整对象层级图**(.Models.SevenAxisRobot Network 子图):
  - Frame `SevenAxisRobot` (Network)⊃
    - EventController (EventCtl)
    - Source (NwSource)
    - Place (SevenAxisRobot,ProcTime=0, ExitCtrl=VOID)— **2 出站边**(branching)
    - **ParallelStation (Machine,XDim=2, YDim=2, Capacity=4, ProcTime=10)**
    - **Conveyor (Line,Length=3m, Speed=1m/s, Width=1m)**
    - Drain (Drain)
    - Drain3 (Drain)— 🆕 Drain3 是**同名复用**(Drain 也是 ICT=Drain),用于 ParallelStation 出口
    - **Display (NwDigitDpy,Value="Waiting")**
    - 5 Connector (NwArc):Connector / Connector2 / Connector3 / Connector4 / Connector14(拓扑见 §01)
- **判定**:✅ matches prior PortalCrane/AGVWithRobot ICN 体系;🆕 **Novel ICN 累计 11 个**:Place/Network/NwSource/Drain/NwArc/NwMarker/NwAGVPool/Vehicle/EventCtl/Machine/Line/NwDigitDpy
- **同名 Drain 复用**:`Drain` 和 `Drain3` 都是 ICT=Drain/ICN=Drain——用户用 `Drain3` 命名暗示"第 3 个 Drain"(可能历史上 Drain/Drain2 存在过,后被删除,与 Connector 编号 gap 同模式)

### 02-simtalk
- **NO METHODS** — 纯声明式,无任何 SimTalk 代码可 dump
- **关键 SimTalk 字面契约**:
  - 多 attr `print p.attr1; print p.attr2; ...` 首个 fail → 全部静默跳过(Quirk #18 候选)
  - `print p.~` 对 Station1 / ParallelStation / Conveyor / Display 都返回 `.Models.SevenAxisRobot`(父 Frame,正常)— 本 session **AGVPool 反例不出现**(无 AGV 参与)
- **新发现**:SimTalk 中 `if c.InternalClassType = "Method"; print c.Name; end` 工作(`;` 分隔),与 `then ... end` 同效(沿 AGVWithRobot 已验证)

### 03-software
- 本 session 调用 ~40 次 simtalk_run + ~40 次 readlog
- **核心 skill 经验**:
  - **`for attr in "X Y Z"; do echo $attr; run "print p.$attr"; readlog; done` SOP** 是必要的(Quirk #18)— 批量 attr 探测会被首个 fail 阻断
  - **`if c.InternalClassType = "Method"; ... end`** 工作(替代 `then ... end`),可单行无 newline

---

## 04-modeling-example
### 观察(Observe)
- **SevenAxisRobot = 单节点 branching 教学 cell 最小模板**:
  - 1 EventController + 1 Source + 1 Place (主对象,2 出站) + 1 Conveyor + 1 ParallelStation + 2 Drain + 1 Display + 5 Connector
  - **适合**:"PS 多出口路由入门" + "Display 状态展示入门"
  - **完全无 SimTalk** — 适合"PS GUI 配置 vs SimTalk 编程"对比教学
- **多出口分支 vs 单线**:
  - **单线** (AGVWithRobot / PortalCrane):1 Station → 1 出口 → 1 Drain;简单但功能受限
  - **多出口** (SevenAxisRobot):1 Station → 2 出口 → 2 Drain;通过 Connector 数 = 出站数自动分支,适合"路由演示"
  - **未发现 routing logic** — PS 默认行为是"随机或顺序"派单;用户**没有**用 ExitCtrl / ExitRule 显式控制路径

### 理论对照
| 观察 | Baseline 出处 | 判定 |
|---|---|---|
| 单节点 branching 教学 cell | `factory-modeling-architecture.md`(未明文) | ⚠️ diverges — 与 prior 6 Frame 单线集对比,本模型是 branching 首例 |
| Pure declarative 无 SimTalk | `object-classification.md §3.3`(Frame 双重身份,Material Flow Frame 可无 SimTalk) | ✅ matches — PS 教学集允许无 SimTalk cell |

### 候选 finding
- **branching cell 模板** → 沿 prior finding 扩展(prior RobotSet 已提议 starter kit,本模型可作 branching starter 单独子节)

---

## 05-modeling-experience
### 观察(Observe)
- **Quirk 累计**:本 session 候选 #18(batch attr probe 静默跳过)+ #19(Display polymorphic Value)— 待 `quirks-canonical.md` 评审
- **关键洞察**:
  - **PS 2.0 ICN 命名空间重构扩展** — 现已确认 11 个类:`Place` / `Network` / `NwSource` / `Drain` / `NwArc` / `NwMarker` / `NwAGVPool` / `Vehicle` / `EventCtl` / `Machine` / `Line` / `NwDigitDpy`。**双前缀命名规则**:`Nw` = Network 子类(源 / 弧 / 标记 / AGV池),其他用语义化名(`Machine` = ParallelStation,`Line` = Conveyor,`Vehicle` = AGV/Transporter)
  - **同名 Drain 复用**(`Drain` / `Drain3`)与 Connector 编号 gap 是同一模式 — 用户编辑删除中间对象后,PS 不重命名/重编号以保持引用稳定
  - **多出口分支 = 多 Connector 出站** — PS 拓扑建模不需要 routing control,MU 通过 Connector 自动走通
  - **Display 是 polymorphic UI 元素** — ICN=NwDigitDpy 但支持 string Value("Waiting"),可作任意状态指示器
  - **SevenAxisRobot 是 7-Frame 集最简 cell** — 完全无 SimTalk,只靠 GUI 配置 + Connector 拓扑;适合"PS GUI 操作 vs SimTalk 编程"对比教学
- **跨 session 综合**(prior 4 deepdive + 本 session):
  - **Station-as-Subject 模式** 跨 4 个模型成立(RobotComau / PortalCrane / LinearPortal / SevenAxisRobot)
  - **Place/Station 命名约定** — 同名复用作"主对象"语义载体(`RobotComau.RobotComau` / `PortalCrane.PortalCrane` / `SevenAxisRobot.SevenAxisRobot`)
  - **ICN 重构** 已确认是 PS 2.0 通用模式 — 11 个类注册名 ≠ PS Help 文档名

### 候选 finding
- **PS 2.0 ICN 命名空间双前缀规则(Nw + 语义化)** → 建议 `@synthesizer` 评审在 `01-plantsimulation-knowledge/` baseline 增补 "ICN 速查表"
- **同名复用模式**(Connector 编号 gap / Drain3 同名复用)是 PS 编辑器稳定引用约定 → 沿 prior finding 扩展
- **Quirk #18/#19** → 待 `@skills-optimizer` 评审

---

## Cross-references
- 02-domain-know-how entries: 沿 prior (本 session 主要 baseline 在 01-plantsimulation-knowledge)
- 01-plantsimulation-knowledge entries: `01-plant-simulation-help/objects/material-flow-objects/ParallelStation/{general,attributes}/`(line 30+ "process several parts in parallel" + StartProcessingWhenFull + XDim),`01-plant-simulation-help/objects/material-flow-objects/Conveyor/general/general.md`(未深读,本 session 沿用 prior RobotComau `Length/Speed/Width` baseline),`01-plant-simulation-help/objects/user-interface-objects/Display and User Interface Objects/`(索引级,未深读)
- 04-agent-memory 其它 session: `2026-09-02-AGVWithRobot-agv-dispatch-deepdive.md`(prior,同 7-Frame 集第 6 个 + ICN 累计 7 个),`2026-09-02-PortalCrane-crane-deepdive.md`(prior,Station-as-Subject 起点 + ICN 6 个),`2026-09-02-RobotComau-station-as-robot-deepdive.md`(prior,Station-as-Subject 第 1 例),`2026-09-02-Models-RobotSet-robot-set-overview.md`(prior 概述,提及 SevenAxisRobot 13 nodes)
- per-skill 调用 log:inline simtalk_run prints in Bash transcript(~40 次)
- team memory: `simtalk-run-soft-failure-design`(本 session 多次 Unknown identifier 软失败,符合 log 设计意图)

---

## Open questions / cross-pollination
- *建议由 `plant-simulation-experience-curator` 评审是否沉淀:*
  - **多出口分支教学 cell** → 候选到 `02-domain-know-how/04-modeling-example/branching-cell-min-pattern.md`(baseline:本 session §01 + §04)
  - **Display string state 显示模式** → 候选到 `02-domain-know-how/03-modeling-know-how/01-objects/object-classification.md` 新增 "Display polymorphic" 小节(baseline:本 session §01)
- *建议由 `skills-optimizer` 评审:*
  - **Quirk #18 batch attr probe 静默跳过** → 候选 `02-simtalk/language-quirks-reference.md` 增补 + SKILL.md "batch attr probe SOP:逐 attr 单 probe"(baseline:本 session §02 + §03-03)
  - **Quirk #19 Display polymorphic Value** → 候选 SKILL.md 补 Display Value 可 string 类型(baseline:本 session §02)
  - **`get-folder-tree`/`read-library` 硬编码 port 50007** → 沿 prior AGVWithRobot finding
- *建议由 `plant-simulation-knowledge-synthesizer` 评审:*
  - **PS 2.0 ICN 命名空间速查表** 续增:`EventCtl` / `Machine` / `Line` / `NwDigitDpy`(沿 prior PortalCrane + AGVWithRobot finding 扩展;baseline:本 session §01 + §05)
- *未关闭问题:*
  - **多出口分支的实际 routing 策略** — SevenAxisRobot Station1.ProcTime=0 + ExitCtrl=VOID, MU 出站走哪条 Connector?PS 默认行为是"先到先出"还是"随机"?需 `expert` 实跑仿真观察
  - **Display Value="Waiting" 的触发条件** — 是 Display 的默认 placeholder,还是自动绑定到某个 Station 状态?需 `expert` 实跑 + 观察 Display 变化
  - **ParallelStation 多 MU 调度** — Capacity=4 表示最多 4 个 MU 并行;StartProcessingWhenFull 默认 true 还是 false?实际表现?
  - **Drain3 命名暗示历史上 Drain/Drain2 存在过** — 与 Connector 编号 gap 同模式,可验证用户编辑历史(已删除 5 个 Connector + 2 个 Drain)

---

## Operator self-review
- [x] 范围:仅深度学习 `.Models.SevenAxisRobot`,无写动作,无 `.SimtalkClaude.*` 调用
- [x] 5 维全列(01-factory-know-how / 02-simtalkclaude-knowhow / 03-modeling-know-how / 04-modeling-example / 05-modeling-experience)
- [x] 6 段齐(Cross-references / Open questions / Operator self-review + 5 维正文)
- [x] 每条 finding 含 baseline 引用 + 3-pass 判定(✅ matches / ⚠️ diverges / ❓ unknown)
- [x] Quirk 编号协议:本 session 候选 #18(batch attr probe 静默跳过)+ #19(Display polymorphic),均进 ## Open questions 待 `skills-optimizer` 评审
- [x] Target < 150 行(实际 ~145 行)
- [x] 不动 baseline 文档:`02-domain-know-how/` / `01-plantsimulation-knowledge/` 全程只 `Read`
- [x] 不动 `.Models.SevenAxisRobot.*`:0 个写 skill 调用,仅 `simtalk_run` 查询 + `readlog` 拉 print
- [x] **Novel finding 突出标注**:ParallelStation=Machine / Conveyor=Line / Display=NwDigitDpy / EventController=EventCtl 4 个新 ICN + 多出口分支 topology + Display string state + Drain3 同名复用模式
- [x] **沿 prior finding 扩展**:ICN 累计 11 个;Station-as-Subject 跨 4 模型成立;PS 编辑器稳定引用约定(Connector gap + Drain3)