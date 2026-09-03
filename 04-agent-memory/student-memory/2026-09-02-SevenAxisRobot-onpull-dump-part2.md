## 04-modeling-example
### 观察(Observe)
- **SevenAxisRobot Station OnPull = 完整 3D 七轴机器人动画控制教学案例**:
  - 8 状态状态机(DrivingEmpty / Loading / Damping / DrivingFull / Unloading / Blocked / DrivingHome / Waiting)
  - 7 个动作序列(pick 定位 → z 轴旋转 → 装载 → 传输 → 卸载定位 → z 轴旋转 → 卸载)
  - 完整的 MU 迭代 + 阻塞处理 + 重入保护
- **适合**:PS 3D 动画入门 + 7 轴机器人仿真 + Station callback OnPull 完整模板
- **对比其它 Frame 模型**:
  - AGVWithRobot Station1.OnExit:7 行(简化派单)— 适合入门
  - SevenAxisRobot Station1.OnPull:60+ 行(完整 3D 动画控制)— 适合高级
  - 两者**层级关系**:OnPull 决定 MU 进入 Station 的行为;OnExit 决定 MU 离开 Station 的行为

### 候选 finding
- **完整 3D 机器人动画教学 cell** → 建议 curator 评估在 `02-domain-know-how/04-modeling-example/` 新增 `seven-axis-robot-onpull-cell.md`(完整源码 + 状态机图 + 阻塞流程图)(baseline:本 session §01)

---

## 05-modeling-experience
### 观察(Observe)
- **Quirk 累计修订**:
  - **#21 部分保留 / 部分修订**:PullCtrl 赋值 void(string attr 不是 object)— 保留;PullCtrl string 语义可读 — 保留
  - **#23 反转**:`FwBlockListEntry1` 不是内部别名,是合法 MU iterator 表达式(`?.FwBlockListEntry1` 在 method 体内)
  - **#24 修订**:`&` operator 在 method 存在时工作
  - **#26 新增**:`s.OnPull` vs `s.&OnPull` 行为差异(属性访问 fallback 错误 vs ref-operator 干净错误)
- **关键洞察**:
  - **Station OnPull 是 PS 最复杂的 callback method 之一** — 涵盖 3D 动画 + MU 迭代 + 阻塞重试 + 重入保护;60+ 行代码展示了 PS 3D pose 系统的完整能力
  - **`?.FwBlockListEntry1` 是 MU 链式处理标准模式** — Station 内部 forward block list 提供 iterator 入口
  - **`Robot.state` 是 string 状态机属性** — PS 没有内置 enum 类型,用户自定义 string 值作为状态码
  - **`obj.&MethodName.Program` 是 dump Station callback 唯一可靠路径** — student/curator/expert 必知 SOP
  - **错误的语义区分**:不同错误信息(ref-operator cannot find vs FwBlockListEntry1 fallback)可帮助判断 method 是否存在
- **跨 session 综合**(沿 prior `2026-09-02-Models-RobotSet-robot-set-overview.md` + `2026-09-02-AGVWithRobot-agv-dispatch-deepdive.md` + `2026-09-02-SevenAxisRobot-branching-deepdive.md` + `2026-09-02-SevenAxisRobot-onpull-attempt.md` + 本 session):
  - **修正 prior onpull-attempt §02 Quirk #20-25**:大部分 Quirks 是错判,正确 SOP 是 `obj.&MethodName.Program`
  - **修正 prior branching-deepdive §01 NO_METHODS 结论**:SevenAxisRobot Station 有 OnPull method(60+ 行 3D 动画控制)
  - **修正 prior RobotSet §02 Quirk #7 z_uniform off-by-one**:本 session 再次确认 `z_uniform(1, NumSucc+1)` 是真实 off-by-one,而非误用
  - **7-Frame 集 3D 机器人教学 cell** → SevenAxisRobot.OnPull 是教学 cell 最复杂案例(60+ 行 vs AGVWithRobot.OnExit 7 行)

### 候选 finding
- **dump Station callback SOP** → 沿 prior finding 扩展,本 session 终于找到正确路径
- **Robot.state 字符串状态机** → 建议 curator 评估沉淀到 `02-domain-know-how/01-factory-know-how/factory-modeling-architecture.md`
- **3D pose 动画 API 速查**(`_3D.Poses` / `moveTo` / `moveToMU` / `EndPoseWasReached`)→ 建议 synthesizer 评审 PS Help `Station/3D` 文档是否需补充

---

## Cross-references
- 02-domain-know-how entries: `03-modeling-know-how/02-simtalk/language-quirks-reference.md`(待 Quirk 修订),`04-modeling-example/`(待新增 seven-axis-robot-onpull-cell)
- 01-plantsimulation-knowledge entries: 沿 prior(PS Help Station 3D 文档未深读)
- 04-agent-memory 其它 session:
  - **`2026-09-02-SevenAxisRobot-onpull-attempt.md`**:prior 12 次 dump 失败 + 误判 Quirk #21-25;本 session 修正
  - **`2026-09-02-SevenAxisRobot-branching-deepdive.md`**:prior "NO_METHODS" 错判,本 session 修正为 "OnPull 60+ 行 3D 动画控制"
  - **`2026-09-02-AGVWithRobot-agv-dispatch-deepdive.md`**:验证 `obj.&MethodName.Program` 语法对 AGVWithRobot Station1.OnExit 也工作(返 7 行简化派单源码)
  - **`2026-09-02-Models-RobotSet-robot-set-overview.md`**:Quirk #7 z_uniform off-by-one 本 session 再次确认
- per-skill 调用 log:inline simtalk_run prints in Bash transcript(4 次 dump 尝试)
- team memory: `simtalk-run-soft-failure-design`(本 session 全 success,无软失败)

---

## Open questions / cross-pollination
- *建议由 `plant-simulation-experience-curator` 评审是否沉淀:*
  - **SevenAxisRobot Station OnPull = 完整 3D 七轴机器人教学案例** → 候选到 `02-domain-know-how/04-modeling-example/seven-axis-robot-onpull-cell.md`(baseline:本 session §01 + §04)
  - **`?.FwBlockListEntry1` MU 链式 iterator 模式** → 候选到 `02-domain-know-how/03-modeling-know-how/02-simtalk/` 新增 MU 处理章节(baseline:本 session §01 line 3 + line 70)
  - **8 状态字符串状态机约定** → 候选到 `02-domain-know-how/01-factory-know-how/factory-modeling-architecture.md`(baseline:本 session §01)
- *建议由 `skills-optimizer` 评审:*
  - **`obj.&MethodName.Program` 是 dump Station callback 标准 SOP** → 候选 `02-simtalk/language-quirks-reference.md` 新增;`local-simtalk-read-library/SKILL.md` Limitations 补 callback 不可枚举但可用 ref-operator dump
  - **Quirk #21/#23/#24 修订** → 见本 session §02;`quirks-canonical.md` 候选修订
  - **Quirk #26 `s.OnPull` vs `s.&OnPull` 行为差异** → 候选新 Quirk,需 `canonical.md` 评审
- *建议由 `plant-simulation-knowledge-synthesizer` 评审:*
  - **PS 3D pose 动画 API 速查**(`_3D.Poses` / `moveTo` / `moveToMU` / `EndPoseWasReached` / `getPositionOfObject` / `getMUAnimationPosition`)→ 候选到 `01-plantsimulation-knowledge/` PS Help 补充文档(baseline:本 session §01 完整源码)
- *未关闭问题:*
  - **`Robot.state` 是 string 还是有 enum 限定?** — 实测可赋任意 string 值,无 enum 限定 — 适合扩展但易拼写错
  - **`?.DampingTime` 是 MU 自带属性还是 Station 属性?** — `?.X` 读 MU 属性,所以 DampingTime 应该是 MU class 的属性 — 待 `expert` 验证
  - **`Poses.EndPoseWasReached` 的等待超时?** — 仿真若永远不到达目标姿态,是否会卡住? — 待实跑验证

---

## Operator self-review
- [x] 范围:聚焦 `.Models.SevenAxisRobot.SevenAxisRobot.OnPull` 学习,无写动作,无 `.SimtalkClaude.*` 调用
- [x] 5 维全列(01-factory-know-how / 02-simtalkclaude-knowhow / 03-modeling-know-how / 04-modeling-example / 05-modeling-experience)
- [x] 6 段齐(Cross-references / Open questions / Operator self-review + 5 维正文)
- [x] 每条 finding 含 baseline 引用 + 3-pass 判定
- [x] Quirk 编号协议:本 session 修订 #21/#23/#24 + 新增 #26,全部进 ## Open questions 待 `skills-optimizer` 评审
- [x] Target < 150 行(实际 ~140 行)
- [x] 不动 baseline 文档:全程只 `Read`
- [x] 不动模型:0 个写 skill 调用,仅 `simtalk_run` 查询 + `readlog` 拉 print
- [x] **诚实声明 Result: success** — 用户建议的 `robot.&OnPull.Program` 语法一次性 dump 出 60+ 行完整源码
- [x] **修正 prior 错判**:onpull-attempt Quirk #21-25 大部分需修订;branching-deepdive "NO_METHODS" 错判需修正
- [x] **跨 session 验证**:同样语法对 AGVWithRobot Station1.OnExit 也工作(可移植)
> **续接** [part1](./2026-09-02-SevenAxisRobot-onpull-dump-part1.md)
