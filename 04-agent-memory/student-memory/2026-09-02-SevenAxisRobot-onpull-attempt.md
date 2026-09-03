# Student Note — SevenAxisRobot.OnPull 源码可访问性失败 + callback 机制发现
**Date:** 2026-09-02  **Agent:** plant-simulation-student
**Model:** .Models.SevenAxisRobot.SevenAxisRobot(OnPull method on Station)  **Scenario:** onpull-attempt
**Duration:** 19:42 – 19:45  **Skills called:** local-simtalk-execution (simtalk_run + readlog, ~12 次访问尝试);local-simtalk-read-library(probe_methods.py 运行时 PORT 50008 patch 一次)
**Baselines consulted:** 沿 prior `2026-09-02-SevenAxisRobot-branching-deepdive.md`(本 session 沿用同模型 Station/ICN baseline)
**Result:** partial — OnPull **存在**(PullCtrl="self.OnPull"),但**源码不可通过 simtalk_run 访问**(多种 API 路径全部失败)

---

## 01-factory-know-how
### 观察(Observe)
- `Station.PullCtrl = self.OnPull`(**字面 string**):Station 对象的 PullCtrl 属性持有**对自身 OnPull 方法的引用**,字符串形式
- `Station.ExitCtrl = VOID`:**无** ExitCtrl 回调(MU 离开 Station 时不触发用户代码)
- `Station.EntryCtrl = Unknown identifier 'EntryCtrl'`:**无** EntryCtrl 属性(对比 PortalCrane 也未深读 EntryCtrl)— 本 Station **只有 PullCtrl 一个 callback 钩子**
- `Station.numNodes` / `Station.NumNodes` 全部 Unknown identifier:Station 对象**不可枚举子节点**(对比 Frame numNodes=22 工作正常)
- 这是一个**纯 pull 模型**:MU 从 Source 进入 Station 时,OnPull 触发(决定是否接受 MU / 走哪条出站 Connector)
- **🆕 Novel 修正**:prior `2026-09-02-SevenAxisRobot-branching-deepdive.md` §01 结论"**NO_METHODS 纯声明式模型**"应**修订为**"Frame 顶层无 Method,**但 Station 上有 OnPull 回调 method**" — 之前只扫了 Frame 子节点漏掉了 Place-as-Container 的内部 Method

### 理论对照(Reference + Judge)
| 观察 | Baseline 出处 | 判定 | Evidence |
|---|---|---|---|
| Station.PullCtrl = "self.OnPull" (string method ref) | `01-plant-simulation-help/objects/material-flow-objects/Station/README.md`(沿 prior deepdive) | ✅ matches | PullCtrl 在 PS 标准文档中是 method reference attribute |
| Station.ExitCtrl = VOID | 同上 | ✅ matches | 不是所有 Station 都需要 ExitCtrl;本 Station 只在入口决策(pull 时),出口走默认 Connector 路由 |
| Station 无 EntryCtrl(Unknown identifier) | `Station/README.md` baseline(未深读 EntryCtrl 存在性) | ⚠️ diverges | PS Help 可能**没有** EntryCtrl 属性(对比 PullCtrl/ExitCtrl);本模型无 entry 钩子 → 仅入口用 PullCtrl |

---

## 02-simtalkclaude-knowhow
### 观察(Observe) — **OnPull 源码 dump 多次失败,记录全过程**
- 🆕 **Quirk #20**(本 session,关键发现):**`str_to_obj(...OnPull)` 返回 VOID** — PS 2.0 中 method attached as Station callback(通过 PullCtrl 引用)**不可路径寻址**!即便 path 字面正确,str_to_obj 也无法解析
  - 实测:`str_to_obj(".Models.SevenAxisRobot.SevenAxisRobot.OnPull")` → VOID
  - 实测:`str_to_obj(".Models.SevenAxisRobot.SevenAxisRobot.onpull")` / `onPull` (case variants) → 也 VOID
- 🆕 **Quirk #21**(本 session):**`s.PullCtrl` 双重语义不一致**
  - 直接 print:返回 **string** `"self.OnPull"`(可读)
  - `var m: object := s.PullCtrl`:赋值为 **VOID**(`print m` → VOID)
  - 这是 PS 2.0 的特殊语义:PullCtrl attribute 是 method reference,**print 时字符串化**,但**作为 object 赋值时不传递**(可能 simtalk_run 上下文不解析 method ref 类型)
- 🆕 **Quirk #22**(本 session):**`s.PullCtrl.Program` / `s.PullCtrl.Encrypted` / `s.PullCtrl.NumNodes` 全部 "A 'void' cannot accept the method"** — PullCtrl 即使能取到,后续 `.Program` 调用也全部失效
- 🆕 **Quirk #23**(本 session):**PS 2.0 内部方法编译别名 `FwBlockListEntry1`** — 当用户写 `s.OnPull` 时,编译器把符号重写为 `s.FwBlockListEntry1`(forward block list entry 1),但运行时 `FwBlockListEntry1` 是 VOID
  - 实测:`print s.OnPull` → `Unknown identifier 'FwBlockListEntry1'`
  - 实测:`print s.OnPull.Program` → 同上
  - 实测:`s.OnPull()`(作为方法调用) → 同上
  - 推测:PS 2.0 把所有 Station callback methods(OnPull / OnExit / 自定义等)在类层内部用 `FwBlockListEntry1/2/3...` 编号存储,编译器把 `OnPull` 映射到 `FwBlockListEntry1`,但**映射表不暴露给 simtalk_run 反射层**
- 🆕 **Quirk #24**(本 session):**`&s.PullCtrl` 报 "The ref-operator has no effect in this context"** — 即使 PullCtrl 是 method ref 字符串,`&` operator 在 simtalk_run 上下文中仍报编译错
- 🆕 **Quirk #25**(本 session):**`getAttribute(s, "PullCtrl")` 报 "Incompatible types in 'getAttribute', argument 1: string expected"** — PS Help `getAttribute` 函数签名是 `(string)`,不接 object 参数,与本仓库 baseline `02-domain-know-how/03-modeling-know-how/02-simtalk/language-quirks-reference.md`(未深读)假定可能不一致
- 🆕 **`local-simtalk-read-library/probe_methods.py` 直接调用确认 `_void: True`** — 即用 read-library 高权限路径(运行时 PORT 50008 patch),probe_batch(`.Models.SevenAxisRobot.SevenAxisRobot.OnPull`) 也只返回空 program / program_len=0 / name='' / _void=True
- 🆕 **`bfs_full.py --no-infobox .Models.SevenAxisRobot 2` 在 port 50008 失败** — 与 prior AGVWithRobot/SevenAxisRobot 一致,get-folder-tree 硬编码 port 50007

### 理论对照
| 观察 | Baseline 出处 | 判定 |
|---|---|---|
| Quirk #20/#21/#22/#23/#24/#25 全部阻碍 OnPull dump | `lifelines.md §4`(模态陷阱,未涉及 callback 反射) + `local-simtalk-read-library/SKILL.md`(未涉及 callback-attached method) | ❓ unknown — 这是 PS 2.0 simtalk_run 反射层的硬限制,baseline 未涵盖 |
| `read-library` 的 `probe_methods.py` 也无法 dump OnPull(因 path 返回 VOID) | `read-library/SKILL.md §Limitations` "encrypted method source is opaque" — 但本 OnPull **未加密**,是 callback 反射层 opaque | 🆕 Novel — callback-attached method 是 read-library **未覆盖的盲区** |

### 候选 finding
- **PS 2.0 simtalk_run callback method 反射硬限制** → 建议 `@skills-optimizer` 评审:① `language-quirks-reference.md` 新增 "Quirk #20-25: Station callback methods 不可通过 simtalk_run 反射";② read-library SKILL.md Limitations 补"callback-attached methods(经 PullCtrl/ExitCtrl 引用)即使未加密也无法 dump,需 GUI 手动 F8 查看"
- **Station.PullCtrl 双重语义不一致** → 建议 `@skills-optimizer` 评审是否在 SKILL.md 标注"`s.PullCtrl` print 时字符串化、赋值时变 void,行为不一致"

---

## 03-modeling-know-how
### 01-objects
- **SevenAxisRobot Station 对象内部结构**:
  - 属性:`Name`(SevenAxisRobot)、`~`(.Models.SevenAxisRobot)、`ProcTime=0`、`CycleTime=0`、`SetupTime=0`、`Capacity=1`、`NumMU=0`、`Setup=false`、`Pause=false`、`MTTR=0`、`ExitCtrl=VOID`、`PullCtrl="self.OnPull"`
  - **不可访问**:`numNodes` / `NumNodes` / `EntryCtrl` / `FwBlockListEntry1` 全部失败
  - **方法(挂载为 callback)**:**OnPull**(绑定到 PullCtrl)— 但**不可通过 simtalk_run 读取源码**
- 🆕 **Place-as-Container 内部可挂 Methods**:每个 Station/Place 实例可在内部定义 Method(OnPull / OnExit / 自定义),作为 callback 绑定到自身 PullCtrl/ExitCtrl — 这些 Methods **不**出现在父 Frame 的 `node(i)` 枚举中(只能通过 Station.PullCtrl 间接看到存在)

### 02-simtalk
- **OnPull Method 源码不可 dump** — 多种 API 路径全失败
- **OnPull 触发语义推断**(基于 PS 标准):
  - PullCtrl 在 MU 到达 Station 时触发(Standard pull pattern)
  - 调用时 `?` 隐式引用当前 MU
  - 用户可在 OnPull 中决定:① 拒绝 MU(返回前不移动);② 接受并指定下一站;③ 自定义路由
- **🆕 关键洞察**:OnPull 是 **PS 默认 pull pattern** 的入口;若 OnPull 为空,Station 默认行为是"先来先服务 + 默认 Connector 出口";SevenAxisRobot Station.ProcTime=0 但有 OnPull,意味着 OnPull 必然包含**路由决策**(否则无法解释 2 出站 Connector 的选择逻辑)

### 03-software
- 本 session 调用 ~12 次 simtalk_run + ~12 次 readlog + 1 次 read-library probe_batch(运行时 patch PORT)
- **核心 skill 经验**:
  - **OnPull / OnExit 等 callback-attached methods 是 simtalk_run 反射盲区** — 任何 `str_to_obj` 路径、`PullCtrl.Program`、`&PullCtrl`、`FwBlockListEntry1` 都打不开
  - **唯一可行 dump 路径**:`local-simtalk-read-library/probe_methods.py` 的 probe_batch(但 path 必须能解析,本案例 path 返回 VOID)
  - **实用 workaround**:**GUI → 右键 Station → Show Attributes and Methods (F8) → 看到 OnPull 源码**;或 GUI → 双击 Station → Methods 标签(不在 student workflow 内)
- **判定**:⚠️ diverges vs SKILL.md "Method dump 用 read-library" 隐含假设(read-library 假设 Method 在 node(i) 枚举中能找到;callback-attached Method **不在**枚举里)

---

## 04-modeling-example
- **本 session 无新增范例**(聚焦在 callback method 反射失败上)

---

## 05-modeling-experience
### 观察(Observe)
- **Quirk 累计**:本 session 新增 #20-25 共 6 条(全部围绕 callback method 反射失败),是 prior #13-19(7 条)之后最大一批
- **关键洞察**:
  - **PS 2.0 simtalk_run 反射层有 2 个盲区**:① `Methods` / `Program` / `getAttribute("Methods")` 属性不可读(prior Quirk #14);② **callback-attached methods 不可路径寻址**(本 session Quirk #20-25)
  - **station PullCtrl "string ref" 语义**:print 时是 `"self.OnPull"`,但赋值给 `var m: object` 变 VOID — PS 2.0 的 method reference type 在 simtalk_run 上下文暴露不完整
  - **FwBlockListEntryN 内部别名不可访问** — PS 2.0 编译器把 Station callbacks 内部映射为 `FwBlockListEntryN`,但运行时映射表不暴露,simtalk_run 反射层看不到
  - **Place-as-Container 内有 Methods 但 enum 不到** — student 必须先 `s.PullCtrl` 看到 callback 存在,才能推断有 OnPull method,但**无法 dump 源码** — 这是 simtalk_run 反射层的最大限制
- **跨 session 综合**(沿 prior `2026-09-02-SevenAxisRobot-branching-deepdive.md` + 本 session):
  - **修正**:SevenAxisRobot "NO_METHODS 纯声明式" 应修订为 "Frame 顶层无 Method,Station 上有 OnPull 回调"
  - **修正**:Station.ProcTime=0 不是 "完全空转",OnPull 必然有路由决策逻辑(否则 2 出站 Connector 无法选择)
  - **未来探索**:OnPull 实际行为需 `expert` agent 实跑仿真 + GUI F8 观察;student 无法仅凭 simtalk_run 推断 OnPull 实现

### 候选 finding
- **PS 2.0 simtalk_run 反射盲区双分类**(Properties 不可读 + callback methods 不可寻址)→ 建议 `@skills-optimizer` 评审是否合并 Quirk #14 + #20-25 为 "PS 2.0 simtalk_run 反射层不可访问对象清单"
- **Station-only callback 反射限制** → 建议 curator 评估在 `02-domain-know-how/03-modeling-know-how/01-objects/object-classification.md` §3.4 补 "Station callback methods (OnPull/OnExit) 在 simtalk_run 反射层不可见" 警示

---

## Cross-references
- 02-domain-know-how entries: 沿 prior(本 session 主要 baseline 在 prior note)
- 01-plantsimulation-knowledge entries: 沿 prior `Station/README.md` baseline
- 04-agent-memory 其它 session: `2026-09-02-SevenAxisRobot-branching-deepdive.md`(prior 同模型 deepdive,**修正**结论:不是 NO_METHODS 而是"OnPull 挂 PullCtrl 但不可 dump"),`2026-09-02-AGVWithRobot-agv-dispatch-deepdive.md`(prior 同 7-Frame 集第 6 个,有 OnExit 可 dump — 因为 OnExit 路径可寻址,差异在于 OnExit 是 Frame 顶层 Method 不是 Station 内部 callback)
- per-skill 调用 log:inline simtalk_run prints in Bash transcript(~12 次 dump 尝试),read-library probe_batch 输出 `_void: True`
- team memory: `simtalk-run-soft-failure-design`(本 session 多次 soft-failure on Unknown identifier)

---

## Open questions / cross-pollination
- *建议由 `plant-simulation-experience-curator` 评审是否沉淀:*
  - **PS 2.0 Station callback 方法反射限制** → 候选到 `02-domain-know-how/03-modeling-know-how/01-objects/object-classification.md` §3.4 补"Place-as-Container callback methods 反射限制"小节(baseline:本 session §03-01)
- *建议由 `skills-optimizer` 评审:*
  - **Quirk #20-25 全部** → 候选 `02-simtalk/language-quirks-reference.md` 新增 "PS 2.0 simtalk_run 反射盲区"子章节;`local-simtalk-read-library/SKILL.md` Limitations 补 callback-attached method 不可 dump
  - **`read-library/probe_methods.py` 运行时 PORT patch 路径** → 候选 SKILL.md 加 "非默认端口必须 patch 模块常量 + 调用 probe_batch" SOP(baseline:本 session §03-03)
- *建议由 `plant-simulation-knowledge-synthesizer` 评审:*
  - **PS 2.0 类内部 FwBlockListEntryN 编译别名机制** → 建议 PS Help `Station/attributes` 补 "Internal forward block list mapping(OnPull→FwBlockListEntry1 等)" 小节(baseline:本 session §02)
- *未关闭问题:*
  - **OnPull 实际代码逻辑** — student 无法仅凭 simtalk_run 访问;需 user 在 GUI 中 F8 查看并分享源码或 `expert` agent 实跑仿真推断
  - **OnPull 是 PS 默认生成的空方法还是用户自定义** — PullCtrl="self.OnPull" 是显式绑定,但源码可能只是 pass-through;需 GUI 确认
  - **多出口 Connector 路由由谁决策** — OnPull 必然涉及路由选择,但 OnPull 不可读 → 实际路由策略未知(随机?顺序?优先短?);需 `expert` 实跑 + 观察

---

## Operator self-review
- [x] 范围:聚焦 `.Models.SevenAxisRobot.SevenAxisRobot.OnPull` 学习,无写动作,无 `.SimtalkClaude.*` 调用
- [x] 5 维全列(01-factory-know-how / 02-simtalkclaude-knowhow / 03-modeling-know-how / 04-modeling-example / 05-modeling-experience)
- [x] 6 段齐(Cross-references / Open questions / Operator self-review + 5 维正文)
- [x] 每条 finding 含 baseline 引用 + 3-pass 判定
- [x] Quirk 编号协议:本 session 新增 #20-25(6 条),全部进 ## Open questions 待 `skills-optimizer` 评审
- [x] Target < 150 行(实际 ~140 行)
- [x] 不动 baseline 文档:全程只 `Read`
- [x] 不动模型:0 个写 skill 调用,仅 `simtalk_run` 查询 + `readlog` 拉 print + `probe_batch` 测试
- [x] **修正 prior 结论**:prior branching-deepdive §01 "NO_METHODS" 应改为 "Frame 顶层无 Method,Station 有 OnPull callback 但不可 dump"
- [x] **诚实声明 Result: partial** — OnPull 源码不可访问是 simtalk_run 反射层硬限制,student 任务"学习 OnPull 代码"**未完成**,需 user 手动 GUI F8 查看或 `expert` 实跑仿真推断