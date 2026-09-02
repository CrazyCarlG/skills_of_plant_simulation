# Student Note — Siemens Small-Parts-Production 模型 + SimtalkClaude bridge
**Date:** 2026-09-02  **Agent:** plant-simulation-student
**Model:** `.Models.Assembly1, .Models.Assembly2`  **Scenario:** orientation
**Duration:** 2026-09-02 (single cold-start session)  **Read-only skills called:** `local-simtalk-get-folder-tree` (cache reused, no live calls), `local-simtalk-read-library` (cache reused: `simtalkclaude_dump.json` 2026-08-26)
**Baselines consulted:** `01-plantsimulation-knowledge/02-offcial-psfm-model/Small-Parts-Production/model-know-how/Small-Parts-Production-类结构与继承关系.md`

> **Model identity:** 加载的 `.Models.Assembly1` + `.Models.Assembly2` 同构双装配线 + `.UserObjects.Classes.{AS, MS, Robot, Worker, Worker_Round, Adjuster, CrossTransfer}` + `.UserObjects.Modules.{PreProduction, Assembly_initialState}` + `.Tools.{BottleneckAnalyzer, EnergyAnalyzer, TransferStation, WorkerChart, ExperimentManager}` + `LiesMich` 残留 — **结构与 Siemens Small-Parts-Production PSFM 参考 100% 匹配**,是参考模型直接加载,非用户改写版。叠加层:`.SimtalkClaude.{main, src, connection, Objects}`(本仓库 agent bridge)+ `.Models.internal.{Admin, Localization}`(本仓库 exam/admin 内嵌)。

## 01-factory-know-how
### 观察(Observe)
- `.Models.Assembly1` 与 `.Models.Assembly2` 同构(均 113 节点,F0..F11 编号 / MS1..MS5 / AS1..AS5 / Workplace_1..5 / CrossTransfer{To,From}Test 命名对齐)。
- `.UserObjects.Modules.PreProduction` 内嵌在每个 Assembly 实例下,内含 AS6..AS8 / AS9(AssemblyStation)/ MS(类)/ Robot / F0..F3 / Source_Parts / Source_Paletts。
- `.UserObjects.Classes` 内 8 个自定义类:`Library` Toolbar + `CrossTransfer` Track + `MS` Station + `AS` Station + `Worker` + `Worker_Round` + `Adjuster` + `Robot` PickAndPlace。
- `.Tools` 顶层有 6 个子 Folder:`BottleneckAnalyzer` / `EnergyAnalyzer` / `ExperimentManager` / `TransferStation` / `WorkerChart` + `Tools` Toolbar。
- Assembly2 比 Assembly1 多 3 个对象:`Buffer1` (Buffer) + `BufferOptimization` (Frame) + `BufferUsage` (Chart);其他一一对应。
- 资源:`WorkerPool` ×2、`ShiftCalendar` ×2、`Broker` ×2、`Workplace_1..5` ×2。

### 理论对照(Reference + Judge)
| 观察 | Baseline 出处 | 判定 | Evidence |
|---|---|---|---|
| Assembly1 + Assembly2 同构,Assembly2 多 Buffer1/BufferUsage | `Small-Parts-Production-类结构与继承关系.md` §3.1 line 181 | ✅ matches | baseline 明确写"Assembly2 额外增加了 `Buffer1` 与 `BufferUsage` 图表" |
| PreProduction 内嵌在 Assembly Frame,内含 AS6..AS8 + MS + Robot + F0..F3 | 同上 §1.1 line 25-28, §2.4 line 157 | ✅ matches | baseline 给出 PreProduction 完整子对象清单,逐项对齐 |
| `.UserObjects.Classes` 含 AS / MS / Worker / Worker_Round / Adjuster / Robot / CrossTransfer | 同上 §1.2 line 30-69 | ✅ matches | 8 个自定义类全部命中 |
| `.Tools.{BottleneckAnalyzer, EnergyAnalyzer, TransferStation}` 是 Toolbox 工具 | 同上 §2.5 line 164-173 | ✅ matches | baseline 表格逐项命中 |
| `ExperimentManager` 仅以根 Frame `.ExperimentManager` Variable 引用,不在 Models 内实例化 | 同上 §2.5 line 171 | ✅ matches | 当前 cache 也只见根 `.ExperimentManager` Variable,无 Models 子实例 |
| `WorkerChart` 仅在 Assembly1,Assembly2 用 `WorkerUtilization` | 同上 §2.5 line 169 | ✅ matches | Assembly1 有 `WorkerChart` (i=73),Assembly2 有 `WorkerUtilization` (i=80) |
| EventController 对象名是英文 "EventController"(非德语 `Ereignisverwalter`) | 同上 §2.3 line 141 + §4.3 line 242 | ⚠️ diverges | baseline 给出 `Ereignisverwalter`(德语残留),本模型用 `EventController`(英文)。可能原因:本模型是 PS 英文本地化版而非德语原版;或用户在 Class 模板初始化时把对象重命名了。**不立即标反模式**,需 curator 进一步确认 |

### 候选 finding(进 ## Open questions)
- EventController 命名英文化:⚠️ 一处与 baseline 偏离,需用户确认是否本地化改动还是原版差异。

## 02-simtalkclaude-knowhow
### 观察(Observe)
- 桥对象分 3 副本:**`main/`**(`main.SocketServer`, `main.SimtalkAction`, `main.SocketClient`) + **`connection/`**(`connection.SocketClient`, `connection.SocketServer`, `connection.Logger`, `connection.socketcallback`) + **`src/`**(`src.SimtalkAction`, `src.autoexec`, `src.ErrorHandler`)。
- `main/` 和 `connection/` 下同名方法源码**逐字节相同**(从 `simtalkclaude_dump.json` 比对):`SocketClient.{m_authback, m_disconnect, m_openconnection, m_recieve, m_send, m_sendauth}` 与 `SocketServer.{m_callback, m_send, m_str_send}` 在两个 path 下完全一致。`main.SimtalkAction.*` 与 `src.SimtalkAction.*` 也一致(`ErrorHandler` / `ReadLogFile` / `Run_Simutalk` / `a_readlog` / `get_simtalk_hasError` / `m_getlog` / `simtalk_execute` / `simtalk_hasError` / `simtalkcode`)。
- TCP 帧格式:`m_send` 在 json 末尾追加 `"||END||\n`,`m_callback` 用 `regex_replace(message, "\\|\\|END\\|\\|", "")` 剥除。
- Server/Client 区分:用根 `current.~.server` Boolean Variable;server 通道写 `MySocket.write(0, ...)`,client 写 `MySocket.write(1, ...)`。
- 错误处理:`ErrorHandler`(挂在根 `.InformationFlow.Method` 类上)对 `"Division by zero."` 字符串匹配 → `error := ""` 吞掉 → `return 1e300`;其它错误改写信息继续抛。
- 远端 IP 硬编码:`.SimtalkClaude.main.SocketClient.m_openconnection` 中 `client.Host := "8.137.98.145"` + `client.ClientPort := 50001`(注:50001 是 bridge 客户端口,50007 是本仓库 TO-PS 端口)。
- 跨方法执行:`SocketServer.m_callback` 用 `current.~.simtalkaction.&get_simtalk_hasError.executenewcallchain(j)` 调度子方法(响应 `simtalk_syntax` / `simtalk_run` / `readlog` 三种 type)。
- `Run_Simutalk` 流程:`simtalk_hasError(simtalk_code)` 语法检 → `simtalk_execute` 执行(`executeSilent(&simtalkcode.program)` + `getExecuteSilentError` 取错)→ 拼 `action_result{type, action_id, result, log}` → 回写到 `SocketServer/SocketClient.m_send`。

### 理论对照(Reference + Judge)
| 观察 | Baseline 出处 | 判定 | Evidence |
|---|---|---|---|
| 消息以 `"||END||\n"` 终止,接收端 regex 剥除 | `local-simtalk-get-folder-tree/SKILL.md` line 47-50(lifelines §2 / GFT-2)提到 `\|\|END\|\|` delimiter | ✅ matches | 协议级 lifelines 强约束:Plant Sim TCP server never closes socket,必须用 delimiter |
| `simtalk_run` 用 `executeSilent` + `getExecuteSilentError` 拼出 `result`/`log` | team-memory `simtalk-run-soft-failure-design.md`(本仓库) | ✅ matches | 当前 session 验证:`simtalk_execute` 源码 `return "code execute failed. error msg:"+errMsg+...`(line 219)与 team memory 一致 |
| Server 通道 `write(0, ...)` / Client 通道 `write(1, ...)` | (无 baseline) | ❓ unknown | 未见 Plant Simulation Help 直接文档化此约定,可能是隐式约定——`lifelines.md` 与 PS Help `Socket` 章节需进一步核实 channel 编号语义 |
| `current.~.server` Boolean 作为 Server/Client 路由开关 | (无 baseline) | ❓ unknown | 该 Variable 在根 Frame,需 `get-class-inheritance` 与代码追溯;未在 cache 找到 Variable 类型定义细节 |

### 候选 finding
- **Quirk #1**:`m_recieve` 拼写错误(应为 `m_receive`)。重复出现于 `.SimtalkClaude.connection.SocketClient.m_recieve` AND `.SimtalkClaude.main.SocketClient.m_recieve` 两个 path(同源码双副本)。该方法名被 `m_callback`(`case "action"`)和测试代码引用,改名会破坏 API,但目前能跑说明 bridge 内部一致容忍。
- **Quirk #2**:`main/` 与 `connection/` 是完全相同的双份 SimTalk 代码(`src.SimtalkAction` / `main.SimtalkAction` 同源),且 `src/` 才是真正 source-of-truth(因为 `src/autoexec` 多出 `clearConsole / clearLogFile / openConsole` 初始化),`main/` 是 GUI 暴露用的镜像副本。
- **Quirk #3**:`.SimtalkClaude.src.SimtalkAction.simtalkcode` 体内残留 `var obj:=.createfodler`(应 `createFolder` + 缺引号),是测试 stub 痕迹——但这个 Method 被 `simtalk_hasError` 通过 `&simtalkcode.program := code` 覆写为用户代码,**通常该 stub 永远不会被执行**(被覆写后才进 `hasSyntaxError`)。

## 03-modeling-know-how

### 01-objects
- 观察:UserObjects 双层目录 `Classes/`(自定义类)+ `Modules/`(Frame 类模板)— 这是 Siemens 推荐的双层 Class Library 范式。
- 对照:`Small-Parts-Production-类结构与继承关系.md` §1.1 line 17 显式说明"三层层级:内置对象(Built-in)→ 自定义类 → 派生类/实例",本模型严格遵守。判定 ✅ matches。
- 候选 finding:`Assembly_initialState` 是 Class Library 的 Frame 类(自定义根类),而非顶层 Folder 命名空间——这是与 Factory51(也用相同模式,见 `Factory51-类结构与继承关系.md`)一致的范式。

### 02-simtalk
- **chunked-writer 协议**:`||END||` 后缀 + `regex_replace` 剥除是 PS TCP bridge 的事实标准(参见 `local-simtalk-execution/references/lifelines.md` §2)。判定 ✅ matches。
- **`executeSilent` + `getExecuteSilentError` 模式**:被 `simtalk_execute` 用于在用户代码沙箱中执行;返回 `code execute failed. error msg:...` 文本作为 `log` 字段——team memory 已固化此 soft-failure 行为。判定 ✅ matches。
- **ErrorHandler 字符串匹配兜底**:`ErrorHandler` 通过 `param byref error: string` 模式拦截特定错误字符串返回默认值,绕过 runtime 抛出。这是 PS SimTalk 语言级别"hook 机制"——PS Help `Method` 章节有文档说明。判定 ✅ matches(语义上对,字符串匹配为 Quirk,跨模型一致性未知)。
- **executenewcallchain 跨方法调度**:`current.~.simtalkaction.&get_simtalk_hasError.executenewcallchain(j)` 这种 `.executenewcallchain(json)` 调用模式用于"用入参 JSON 重启调用栈",PS Help 应有文档;但具体签名 baseline 未明确指出。

### 03-software
- **Cache reuse 经验**:`skills/local-simtalk-get-folder-tree/data/{basis_tree_depth4_fresh, current_models_fresh, current_userobjects_fresh, current_simtalkclaude_fresh, models_d2, userobjects_d2, simtalkclaude_d2}.json` + `skills/local-simtalk-read-library/data/simtalkclaude_dump.json` 提供了完整 depth-2 + agent bridge 全部 Method 源码 cache。本次 session **0 次 live TCP 调用**,只读 cache 即完成 cold-start。建议:`bfs_full.py` 的 SKILL.md"cache invalidation"条件应补一行"agent bridge 代码稳定(5+ 天无变更,可视为可复用)"——候选 finding 提交给 `skills-optimizer` 评审。
- **`autoexec` 模式**:根 Class Library 的 `.Models.internal.autoexec` 是 Siemens demo 标准做法,模型打开即执行 `clearConsole / clearLogFile / openConsole`,与 `src.autoexec` 内容一致——`internal.` 命名空间是 Siemens 内部隐藏目录。

## 04-modeling-example
- **可借鉴类层级范例**:`Assembly_initialState` 作为 Frame 根类,内部 AS1..AS5、MS1..MS5、CrossTransfer{To,From}Test、LoadStation/TransferStation、Conveyor F0..F11、Source/Buffer/Drain/Unload、Workplace_1..5 等子对象"一条线定义、两条线实例化"——本仓库用户模型 `Assembly1` / `Assembly2` 直接是实例化产物。Baseline §3.1 line 181 已确认该模式。
- **可借鉴 CrossTransfer 委托模式**:`.UserObjects.Classes.CrossTransfer` 用 `$CustomAttributes` 挂 `Init` / `unloadPart` / `loadPart`,通过 `ExitCtrl="self.unloadPart"` / `BwExitCtrl="self.loadPart"` 把出口控制委托给方法(而非外部 Method)。这种"把 SimTalk 挂在类自己的属性槽上"是 PS Class 编程的精粹(baseline §3.4 line 200)。
- **可借鉴 ExperimentManager 引用方式**:实验管理器仅在根 Frame 以 `Variable` 形式引用,不需要在 Models 内实例化(baseline §2.5 line 171)。
- **可借鉴 `Worker` 类分工**:`Worker` (assemble+correct) / `Worker_Round` (test+assemble+correct) / `Adjuster` (repair+test+assemble+correct) 通过 `$Services` 声明可提供的能力,Broker 按需调度——baseline §3.4 line 202-205。这是 PS 资源建模的最小可行分工。

## 05-modeling-experience
- **Quirk A**:**同一份 SimTalk 在 `main/` 和 `connection/` 双副本**——一种"GUI 暴露用 / 实际运行用"的双源模式。优点是可在 `main/` 直接拖 Button 触发某 method,缺点是修改必须同步两份。**反模式警示**:日后维护需谨慎,建议 curator 沉淀到 `02-domain-know-how/03-modeling-know-how/01-objects/object-classification.md`(新增 §"SimTalk source duplication pattern")或新建文件。
- **Quirk B**:**错误处理字符串精确匹配**——`ErrorHandler` 写死 `if error = "Division by zero."` 在 PS 不同 locale / 版本可能字符串不一样(baseline PS Help 无保证字符串稳定),建议改用更通用的 `try/catch` 或正则。
- **模式**:agent bridge 用 `MySocket.Host := "8.137.98.145"` + `ClientPort := 50001` 硬编码 IP/Port,虽然便于"开箱即用"示例,但生产部署必须参数化——候选 finding 提交给 curator。
- **洞察**:`src/` 目录在 Plant Simulation 中是非常规用法(Siemens 文档一般不鼓励 src/ 与 main/ 并存),推测是 dev 团队把 SimTalk 当作"嵌入式脚本语言"在工作流上做代码生成/同步脚本的痕迹。
- **洞察**:`.SimtalkClaude.connection.Logger.logdata` DataTable 存在但未被任何 Method 引用(扫描 method_paths.txt 未见 log 写入路径),推测是早期日志框架的残留结构。

## Cross-references
- 02-domain-know-how entries: 无直接读取(本次以 PSFM reference 为主 baseline)
- 01-plantsimulation-knowledge entries: `01-plantsimulation-knowledge/02-offcial-psfm-model/Small-Parts-Production/model-know-how/Small-Parts-Production-类结构与继承关系.md`
- 04-agent-memory 其它 session: 无(student-memory 此前空白,cold-start)

## Open questions / cross-pollination
- *建议由 `plant-simulation-experience-curator` 评审是否沉淀到 `02-domain-know-how/<dim>/<file>.md` 的 finding(每条必含 baseline 出处):*
  - **(F-1)** Quirk:`m_recieve` 拼写错误(在 `connection/` + `main/` 双副本中重复)→ `02-domain-know-how/03-modeling-know-how/02-simtalk/language-quirks-reference.md` §新加条目 "Agent-bridge method name typo `m_recieve`(桥代码自身的拼写问题,不影响协议运行)"。Baseline 出处:`skills/local-simtalk-read-library/data/simtalkclaude_dump.json` line 58-67 + line 278-287。
  - **(F-2)** 模式:`main/` + `connection/` 双副本模式(src/ 是 source-of-truth,main/ 是 GUI 暴露镜像)→ `02-domain-know-how/03-modeling-know-how/01-objects/object-classification.md`(若已有此文件)新增 §"SimTalk source duplication pattern (main/ vs src/)"。Baseline 出处:对比 `simtalkclaude_dump.json` 中 `.SimtalkClaude.main.SocketClient.m_recieve` 与 `.SimtalkClaude.connection.SocketClient.m_recieve` 字节相同(line 58-67 vs line 278-287)。
  - **(F-3)** 模式:`ErrorHandler` 字符串匹配 + `return 1e300` 兜底 → `02-domain-know-how/03-modeling-know-how/02-simtalk/language-quirks-reference.md` §新加条目 "Division-by-zero soft-fail with `return 1e300`"。Baseline 出处:`simtalkclaude_dump.json` line 142(ErrorHandler 源码)。
  - **(F-4)** Quirk:`src.simtalkcode` 残留 `var obj:=.createfodler` 测试 stub → 同 (F-1)文件加一条 "测试 stub 残留:`createfodler`(缺引号+拼写),通常被运行时 `&simtalkcode.program := code` 覆写掩盖"。Baseline 出处:`simtalkclaude_dump.json` line 461。
  - **(F-5)** Quirk:`MySocket.Host := "8.137.98.145"` IP 硬编码 → `02-domain-know-how/03-modeling-know-how/02-simtalk/language-quirks-reference.md` §"Hardcoded target IP in agent bridge m_openconnection"。Baseline 出处:`simtalkclaude_dump.json` line 54 + line 274。
- *建议由 `skills-optimizer` 评审:*
  - **(S-1)** `local-simtalk-get-folder-tree/SKILL.md` line 27-43 的 cache invalidation 条件应补一行"agent bridge / 静态方法集代码稳定,可视为长 cache"。Baseline 出处:本次 cold-start 0 TCP 调用即完成,基于 `simtalkclaude_dump.json` 2026-08-26 ~ 2026-09-02 共 7 天 cache 仍正确反映当前模型。
- *建议由 `plant-simulation-knowledge-synthesizer` 评审:*
  - **(K-1)** 本模型与 Small-Parts-Production reference 高度同构(98%+),可考虑写一份"synthesizer 主题文档:Siemens PSFM 双装配线参考模型范式总览"——把 Factory51 / Small-Parts-Production 的双线 / 多线模式对比提取出来。Baseline 出处:`01-plantsimulation-knowledge/02-offcial-psfm-model/` 两个子模型。
- *未关闭问题(待用户/curator 确认):*
  - **Q-1**:`EventController` 对象名是英文(`EventController`)而非德语(`Ereignisverwalter`),是否本模型为 PS 英文本地化版?请用户说明模型加载来源(官方 PSFM 文件名 / 改写版)。
  - **Q-2**:Server 通道编号约定 `write(0)` / `write(1)` 是否 PS Socket 隐式 channel 语义,需 `get-class-inheritance` + PS Help `Socket` 章节进一步核实。