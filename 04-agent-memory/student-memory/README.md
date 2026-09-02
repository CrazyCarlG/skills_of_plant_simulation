---
last_updated: 2026-09-02
contributors: [@plant-simulation-student]
scope: `plant-simulation-student` agent 产出的"模型学习 session 笔记"索引,按 Date + Model + Scenario 维度
revision_notes:
  - 2026-09-02 (4th):追加 PortalCrane crane-deepdive session(单对象深挖:`.Models.PortalCrane.PortalCrane` Station-as-Crane 机制 + 子对象(Station/Station2/PortalCrane/Source/Drain/Connector×4)+ 12 个 Place/Source/Drain 属性实测;**Novel finding**:PS 2.0 类注册名重构——`.MaterialFlow.Station.InternalClassName="Place"`(实际类名)、Frame=`Network`、Source=`NwSource`、Connector=`NwArc`、Models root=`NwObjFolder`(PS Help 文档标题"Station"滞后);新增 Quirk #13 `numChildren=0`(即使 9 个可见子对象)、#14 `obj.Methods/Program/getAttribute("Methods")` simtalk_run 全部 Unknown identifier、#15 `obj.~.~.~` 多重 ~ 链报"Arithmetic operations"——Quirk #6/10/12 的 simtalk_run 通道限制扩展。**与 prior RobotComau 完全同构**:Station-as-Subject 模式跨 2 个 7-Frame 模型成立)。
  - 2026-09-02 (3rd):追加 RobotComau station-as-robot-deepdive session(单对象深挖:`.Models.RobotComau.RobotComau` Station-as-Robot 机制 + 30+ 属性 + 5 个 Connector 实测;新增 Quirk #8-#12:PS 2.0 属性收缩白名单 + simtalk_run 单 print + readlog fallback SOP 形成)。
  - 2026-09-02 (2nd):追加 robot-set-overview session(7 Frame 教学集合通览:RobotComau/XZYStacker/PortalCrane/LinearPortal/MarkerCrossing/SevenAxisRobot/AGVWithRobot)。
  - 2026-09-02:对齐 `agents/plant-simulation-student.md` 优化版——student 与 expert 共享 baseline + 技能 + Quirk 协议,姿态差异(学习 vs 执行)+ 输出差异(5 维 note vs 6 段 summary);笔记结构由"5 维 + 2 段"扩展为"5 维 + 6 段(含 Operator self-review)";student 描述由"只读扫描"改为"默认只读,写需确认+回滚"。
---

# 04-agent-memory/student-memory — 模型学习 session 笔记索引

> **定位**:本目录是 `plant-simulation-student` agent 的**只写**记忆区。每个 session 笔记 = 一份按 `02-domain-know-how/` 5 维结构镜像分析某个用户仿真模型的观察报告。
>
> **与 `plant-simulation-expert-memory/` 的区别**:
> - expert = 跑 SimTalk / 写方法 / 改模型 / 执行任务 → session summary 记录"做了什么"
> - student = **默认只读**扫描 / 提炼模式 / 5 维分析 → session note 记录"学到了什么";用户明确说"演示给我看"才可写,改前确认 + 改后必回滚/记录
>
> **与 expert 共享**:同一套 baseline(`01-plantsimulation-knowledge/` + `02-domain-know-how/`)、同一套 `local-simtalk-*` 技能、一套 Quirk 编号协议——student 的差异只在姿态(学习 vs 执行)+ 输出(5 维 note vs 6 段 summary)。
>
> **何时不需要读本目录**:
> - 想看专家的执行流水 → `../plant-simulation-expert-memory/`
> - 想看已沉淀到知识库的 finding → `../../02-domain-know-how/`

## 命名与路径

- **路径**:`04-agent-memory/student-memory/<date>-<model>-<scenario>.md`
  - `<date>` = `YYYY-MM-DD`
  - `<model>` = 模型根 Frame 路径末段(`.UserObjects.Warehouse` → `Warehouse`),多个 root 用逗号
  - `<scenario>` = 用户场景简述,kebab-case,不超过 5 个英文词
- **示例**:`2026-09-01-Factory51-warehouse-orientation.md`

## 索引表(newest at top)

| Date | Model | Scenario | Top finding | Path |
|---|---|---|---|---|
| 2026-09-02 | PortalCrane | crane-deepdive | ⚠️ `.Models.PortalCrane.PortalCrane.InternalClassType=Station` 但 `.InternalClassName="Place"`(PS 2.0 标准工位类注册名重命名,PS Help 文档"Station"标题滞后);✅ 完整 `str_to_obj(".MaterialFlow.Station").InternalClassName="Place"` 验证;✅ Frame-as-Container ICN=`Network`(非通用 Frame);✅ 子对象清单 5 Place/Source/Drain + 4 Connector(NwArc);✅ Station-as-Crane 模式跨 2 个 7-Frame 模型成立(与 prior RobotComau 完全同构);⚠️ 与 prior 同样无 PickAndPlace/PortalCrane 内置类,无 crane 专属属性(CraneType/Speed/LoadTime/RangeX 全部 Unknown identifier);⚠️ 1 层简化 vs Factory51 3 层范式。新增 Quirk #13 `numChildren=0`(9 可见子对象仍报 0,Quirk #6 `numNodes` 同源扩展)、#14 `obj.Methods/Program/getAttribute("Methods")` simtalk_run 全部 Unknown identifier(Quirk #10 `$CustomAttributes` 全面扩展)、#15 `obj.~.~.~` 多重 ~ 链报"Arithmetic operations"(单 ~ 正常,多 ~ 失效)。**Novel**:PS 2.0 ICN 命名空间重构(Place/Network/NwSource/NwArc/NwObjFolder),建议 synthesizer 评审 PS Help 文档标题是否需更新。 | [2026-09-02-PortalCrane-crane-deepdive.md](./2026-09-02-PortalCrane-crane-deepdive.md) |
| 2026-09-02 | RobotComau | station-as-robot-deepdive | ✅ `.Models.RobotComau.RobotComau.InternalClassType=Station`(真非 PickAndPlace);✅ Station 标准属性(ProcTime/CycleTime/Capacity/Pause/failures/MTTR/ExitCtrl)全部 baseline matches;⚠️ 用户用 Station + 3D 图形替换而非 PickAndPlace,失去 Angles/Times Table/LoadingTime/UnloadingTime/TargetCtrl/PullCtrl;⚠️ 1 层无 `UserObjects/` 类库 vs Factory51 `Milling` 3 层范式。新增 Quirk #8 `ProcessingTime` → 真实 `ProcTime`、`#9` `isStation()` 不存在、`#10` `$CustomAttributes` simtalk_run 报 `$` syntax error、`#11` Station Entry/Exit 不可 SimTalk 读、`#12` PS 2.0 属性白名单(可访问 = Name/InternalClassType/~/Cont/NumMU/Pause/ProcTime/CycleTime/SetupTime/Capacity/failures/MTTR/ExitCtrl/Setup/NumChildren)。| [2026-09-02-RobotComau-station-as-robot-deepdive.md](./2026-09-02-RobotComau-station-as-robot-deepdive.md) |
| 2026-09-02 | Models-RobotSet(7 Frame) | robot-set-overview | ⚠️ 7 Frame 扁平化、无 `UserObjects/` 类库分层、无 RCS 集中控制(diverges vs Factory51 范式);✅ Station 作"机器人主体"语义载体合法、Frame-as-Container 嵌套合法(4 个 MarkerCrossing 嵌套 Frame);❓ Quirk #4 `ClassName` / #5 `array[1..6] := [string]` syntax error / #6 `Station.numNodes` 不可读 + simtalk_run 静默退出。3 个 Frame-level Method dump:MarkerCrossing.Init(DAGV dispatcher)、DestCtrl(on-exit 重新分配)、AGVWithRobot.OnExit(单 AGV 任务链)。 | [2026-09-02-Models-RobotSet-robot-set-overview.md](./2026-09-02-Models-RobotSet-robot-set-overview.md) |
| 2026-09-02 | Assembly1, Assembly2 | orientation | ✅ 与 Siemens Small-Parts-Production PSFM 同构(双装配线 + PreProduction 内嵌 + AS/MS/Robot/CrossTransfer 自定义类);⚠️ EventController 英文名 vs baseline 德语残留 `Ereignisverwalter`;❓ `write(0/1)` 通道编号语义未文档化。**用户叠加**: `.SimtalkClaude.{main,src,connection}` agent bridge + `.Models.internal.Admin` exam harness。Quirks: `m_recieve` 拼写错误、`main/` 与 `connection/` 双源副本、`MySocket.Host` 硬编码 IP。 | [2026-09-02-Assembly1,Assembly2-orientation.md](./2026-09-02-Assembly1,Assembly2-orientation.md) |

## 笔记结构(5 维 + 6 段)

每篇 session 笔记固定包含以下章节(未触发的维度/段写"本 session 无新增" / "本 session 无" + 一句话原因):

### 5 维(对照 `02-domain-know-how/` 主题结构)

1. `## 01-factory-know-how` — 工厂/仓库建模模式
2. `## 02-simtalkclaude-knowhow` — 桥协议相关观察
3. `## 03-modeling-know-how` — 通用建模(`01-objects` / `02-simtalk` / `03-software` 子节按需)
4. `## 04-modeling-example` — 可借鉴示例
5. `## 05-modeling-experience` — 经验沉淀(Quirk / 模式 / 反模式 / "原来 PS 是这样" 的洞察)

### 6 段(协议/索引段)

6. `## Cross-references` — 引用过的知识库条目 + 同模型 prior session + per-skill log + team-memory
7. `## Open questions / cross-pollination` — 未关闭问题 + 建议由 curator / skills-optimizer / synthesizer 评审的 finding
8. `## Operator self-review` *(可选,append-only)* — self-check 标记(`[ ]` checkbox 形式)

> 完整模板见 `agents/plant-simulation-student.md` "Session 笔记协议 / 模板" 段。

## 何时需要读本目录

- **新 student session 开始前**:命中某 Model + Scenario 组合的 prior session,先读避免重复扫描
- **curator 评估沉淀候选**:扫 `## Open questions / cross-pollination` 段,看是否有值得 append 到 `02-domain-know-how/` 的 finding
- **用户问"我们之前学过 X 模型吗"**:查索引表定位

## 与其他目录的关系

| 目录 | 内容性质 | 关系 |
|---|---|---|
| `04-agent-memory/student-memory/`(本目录) | student 产出的模型学习笔记 | **候选 finding 池**,供 curator 评估 |
| `04-agent-memory/plant-simulation-expert-memory/` | expert 的执行 session summary | **并行记忆**,与 student 同侧但维度不同(执行 vs 学习) |
| `02-domain-know-how/` | 已沉淀的领域知识(append-only) | **本目录的目标归宿**——由 curator 评审后沉淀 |
| `04-agent-memory/curator-memory/` | curator 的评审报告 | **本目录的治理输出**——读 curator 报告可追溯哪些 finding 被采纳/拒绝 |
| `skills/<x>/log/` | per-skill 调用日志 | student 写的 Quirk/cache 经验回传给 `skills-optimizer` 评审 |

## 重构元数据

- 创建日期:2026-09-01
- 创建执行者:plant-simulation-student(由用户指示新增)
- 创建原因:用户希望把"读模型"与"写模型"两条 agent 路径拆开,student 走只读扫描 + 5 维镜像分析,不污染 expert 的执行日志
- session 累计:4 篇(Assembly1+Assembly2 orientation / RobotSet overview / RobotComau station-as-robot deepdive / PortalCrane crane-deepdive)