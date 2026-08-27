# Factory51 + SimtalkClaude 集成经验 — 2026-08-27

> 本文档沉淀把 **SimtalkClaude**（TCP 远程驱动桥）导入 Siemens 官方 **Factory51** 模型后
> 学到的核心模式。目标读者是后续在 Plant Simulation 里做"模型 ↔ 外部 agent"
> 双向打通工作的工程师，以及下一轮需要再核对这份事实的 agent。

---

## 〇、本次调研的基础事实

- **Factory51**：`02-offcial-psfm-model/Factory51/Factory51.psfm`（Folder Model，PSFM 文本格式），
  版本 `26.6.2.3599` / `ModelFormat: 1` / 1592 个对象。完整结构详见
  `01-plantsimulation-knowledge/02-offcial-psfm-model/Factory51/model-know-how/Factory51-模型结构.md`。
- **SimtalkClaude**：v1 在 `02-simulation-file-experience/simtalkclaude-best-practices.md` 已有完整经验；
  v2（`.SimtalkClaude2`）有 22 个 ROOT method + 20 个继承 method，备份在
  `skills/local-simtalk-add-note-to-method/code_log/SimtalkClaude2_*_program_original.txt`。
- **导入方式**：`.SimtalkClaude2` 作为独立的 Class Library（Folder Model 里的一个 Folder）
  挂在 Factory51 根 Frame 之外，与业务 Frame（P1/P2/Warehouse/WMS）**不发生对象引用**。

---

## 一、Factory51 自身值得抄的"教科书"做法

> 详见 `Factory51-模型结构.md` 与 `Factory51-类结构与继承关系.md`，本节只摘与
> "如何让模型可被 agent 驱动"相关的设计选择。

### 1.1 Class Library / Models 二分法

```
Factory51.psfm/
├── UserObjects/          ← Class Library（类定义，isClass）
│   ├── Production/       ← Frame 类，内含 ~120 个子对象
│   ├── Painting/         ← Frame 类
│   ├── PolishingCell/    ← Frame 类
│   ├── PostProcess/      ← Frame 类 + 派生 PostProcess1/2/3
│   ├── Drying/           ← Frame 类 + 派生 Drying1/2
│   ├── Warehouse/        ← Frame 类
│   ├── MUs/              ← Box/Pallet/AGV/Forklift/Truck 等 MU 类
│   └── ...
├── ApplicationObjects/   ← 外部库类（HBW3D、CranesAndMore）
├── MaterialFlow/         ← 标准库基础类（Source/Conveyor/Station …）
├── Resources/            ← 标准库基础类（WorkerPool/Workplace/AGVPool …）
├── InformationFlow/      ← 标准库基础类（Method/Variable/DataTable …）
├── MUs/                  ← 标准库基础 MU（Container/Part/Transporter）
├── UserInterface/        ← 标准库 UI 类
└── Models/
    └── Factory51/        ← 模型实例（isInstance）
        ├── P1, P2        ← Production 类实例
        ├── Warehouse     ← Warehouse 类实例
        └── ...           ← Source/StoreEntry/MultiPortalCrane/Track …
```

| 层 | 职责 | 复用方式 |
|---|---|---|
| **UserObjects/** | 业务类定义 | 跨模型/跨实例复用 |
| **ApplicationObjects/** | 第三方库类 | 跨模型复用 |
| **MaterialFlow/Resources/InformationFlow/MUs/UserInterface/** | 标准库基础类 | 跨模型复用 |
| **Models/** | 当前模型的具体实例 | 当前模型独占 |

> **值得抄**：把"类定义"和"实例"**分目录存放**——这样导入 SimtalkClaude 这类"非业务
> 工具"时，**工具的 Class Library 只挂在根 Frame 之外，不污染 `UserObjects/`**，
> 业务类的语义保持干净。
> （如果 SimtalkClaude 也塞进 `UserObjects/`，业务 Frame 继承 `Production` 时会
> 顺带继承到 `.UserObjects.SimtalkClaude.*`，污染业务命名空间。Factory51 的做法
> 是把 SimtalkClaude 作为**顶层 Folder**，与 `UserObjects` 平级 —— 这是干净的隔离。）

### 1.2 "一条线定义、两条线实例化"（Production → P1/P2）

```
Production（UserObjects/Production，自定义 Frame 类，isClass）
  ├── P1（Models/Factory51/P1，isInstance）
  └── P2（Models/Factory51/P2，isInstance，结构与 P1 完全一致）
```

- Production 类内含全部 11 个工序子 Frame + ~90 个对象（Line/Converter/Station/Workplace/WorkerPool …）。
- P1/P2 通过 `Origin` 指向 Production 的 UUID `3e014d4c`，继承全部结构。
- P2 与 P1 同构，**没有任何 override** —— 完全相同的副本。

> **对 agent 的意义**：当外部指令"把 P2 的所有 Workplace 都加上 pause=true"时，
> agent 可以直接 `for p in [P1, P2] { ... }` 用同一段逻辑遍历，
> 而不必针对 P1/P2 各写一份代码。这就是 Class Library 的真正价值。

### 1.3 Frame 类做"工序单元"——Painting/PolishingCell/PostProcess/Drying 同构

| 工序类 | 内含 | 派生类 | 实例 |
|---|---|---|---|
| Painting | Line+Station+Workplace+LockoutZone+PaintColor(Variable) | ClearPaint/Painting1/Painting2 | P1/ClearPaint, Painting1/2 |
| PolishingCell | Polishing+Buffer+DisplayBuffer+Display+Workplace | Polishing1/2/3 | P1/Polishing1..3 |
| PostProcess | Line1..3+Step1..3+Workplace1..2+Display | PostProcess1/2/3 | P1/PostProcess1..3 |
| Drying | Line（Conveyor）| Drying1/2 | P1/Drying1/2 |

> **对 agent 的意义**：每一种工序类都是"Frame 模板 + 内嵌对象清单"。
> agent 若想做"参数扫描"（比如改每个 PolishingCell 的加工时间），
> 直接遍历所有 `PolishingCell 派生类的实例`即可，路径枚举可以基于 Origin 关系自动生成。
> 详见 `local-simtalk-get-class-inheritance/scripts/probe_inheritance.py`。

### 1.4 Control 全部走 Method（OnEntrance / OnExit / ExitCtrl / InitCtrl）

| 对象 | 控制类型 | 挂载方法 |
|---|---|---|
| `Source` / `TruckArrivals` | EntranceCtrl | `self.OnEntrance` |
| `StoreEntry` | ExitCtrl | `StorageArea.storing`（跨对象委托）|
| `StoreExit` | ExitCtrl | `self.OnExit` |
| `Production/Line` | ExitCtrl | `self.OnExit`（PlatesInProduction += 1 + Polishing 空满分流）|
| `TruckArrivals` | InitCtrl | `self.~.Path.create(self.~)` |

> **值得抄**：把"行为"封装在 Method 里、对象属性上只挂**方法引用字符串**——这让
> agent 可以用 `local-simtalk-modify-object-atrribute` 在不改代码的前提下切换控制逻辑
> （比如把 `StoreEntry.ExitCtrl` 从 `"StorageArea.storing"` 临时改成 `"self.MyProbe"`，
> 让 agent 拿到每一次出库事件，再恢复）。

---

## 二、SimtalkClaude v2 真正的新增模式（相比 v1）

> v1 基线经验全部在 `02-simulation-file-experience/simtalkclaude-best-practices.md`。
> 本节**只列 v2 多出来的东西**——v1 的所有特性（`||END||` 帧、scratch buffer、
> `executenewcallchain`、`Server` boolean、copy-read-delete、ErrorHandler 等）v2 全部继承。

### 2.1 鉴权握手：`m_sendauth` + `m_authback`

> 这是 v2 **相比 v1 最关键的安全升级**。v1 完全无鉴权 —— 任何能连上 `50001` 的客户端
> 都可以跑任意 SimTalk。Factory51 这种"价值千万人民币的工厂模型"上线时必须有鉴权。

**v2 客户端 `connection/SocketClient.m_sendauth`**（从 `code_log/SimtalkClaude2_connection_SocketClient_m_sendauth_program_original.txt` 提取）：

```simtalk
-- 获取当前 Unix 时间戳（毫秒级精度）
-- Unix epoch: 1970-01-01 00:00:00
var epoch: dateTime := str_to_dateTime("01.01.1970 00:00:00")
var now: dateTime := sysDate
var diffSeconds: real := now - epoch
var tsMillis: integer := round(diffSeconds * 1000)
var tsSeconds: integer := round(diffSeconds)

auth["token"] := token
auth["ts"]    := tsSeconds
auth["sig"]   := sig
m_send(auth)
```

**v2 客户端 `connection/SocketClient.m_authback`**（收到服务端 auth reply 后）：

```simtalk
param j:json
--{"type":"auth","status": "ok", "session_id": state.session_id}
var status := j["status"]
if status = "ok"
    session_id := j["session_id"]
    return
else
    MySocket.On := false    -- 鉴权失败 → 直接断 socket
end
```

**v2 服务端 `connection/socketcallback` 路由**：

```simtalk
switch type
case "auth"
    m_authback(j)            -- 收到 auth 请求 → 处理鉴权 + 回包
case "action"
    current.~.simtalkaction.get_simtalk_hasError(j)
case "response"
    debug                    -- 客户端模式的 response 回包
end
```

> **值得抄**：
> - **鉴权失败的硬切**：服务端收 `"status": "ok"` 才把 `session_id` 写入本地 Variable，
>   否则**立刻 `MySocket.On := false` 断 socket**。不要给失败重试留机会。
> - **`sig` 字段是为后续 HMAC 签名留的口子**——目前代码里 `sig` 是占位（直接赋值），
>   实际上应当 `sig = HMAC_SHA256(token + ts, secret)`。v2 给出了字段位置但没填实现。
> - **服务端把"auth"作为独立 case**——意味着后续任何 action 都需要在 handler 入口
>   校验 `j["session_id"] == current.session_id`，否则拒执行。v2 暂时没在
>   `Run_Simutalk` / `get_simtalk_hasError` 里加这层校验，**留作 TODO**。

### 2.2 双协议分帧：`m_str_send`（旧）+ `m_send`（新）

> v2 保留了 v1 的 `m_send(jsondata)` 路径，但**多了一个 `m_str_send(msgStr)`**
> —— 用来发"原始字符串 + ||END||"，绕过 JSON 编码。

**`connection/SocketServer.m_str_send`**（**仅 v2 存在**）：

```simtalk
param msgStr:string
msgStr := msgStr + "||END||"
var success: boolean := MySocket.write(0, msgStr)
```

**`connection/SocketServer.m_send`**（v1 沿用）：

```simtalk
param jsondata:json
var msgStr: string := jsondata.asString(false) + "||END||"
var success: boolean := MySocket.write(0, msgStr)
```

> **值得抄 / 不建议抄**：
> - ✅ **理由**：v2 早期版本的协议不是 JSON 格式而是裸字符串（比如 `"PING||END||"`），
>   `m_str_send` 给"老客户端兼容"留了入口。**但实际生产环境应该删掉 `m_str_send`**——
>   多种帧格式意味着 parser 复杂度翻倍，且 JSON 才有结构化字段。
> - ❌ **不建议抄**：v2 同时存在 `m_send` 和 `m_str_send` 两个分支出口，
>   让人搞不清当前到底走哪条。**新工程只保留 `m_send(jsondata)` 一种即可**。

### 2.3 连接状态机：`m_openconnection` 原子化 connect+auth

> v1 的连接流程需要 client 端**先手动连 socket、再单独发 auth 包**——两步操作，
> 中间网络抖动就会卡在"已连但未鉴权"的悬挂态。v2 把这两步收进一个 method。

**v2 `connection/SocketClient.m_openconnection`**：

```simtalk
if MySocket.On = false
    -- 激活 Socket 连接
    auth_success := false
    session_id := ""
    MySocket.TCP := true

    var client: object := MySocket
    -- 1. 作为客户端：取消 ServerSocket
    client.ServerSocket := false
    client.TCP := true
    client.Host := "8.137.98.145"   -- 替换为目标服务器 IP
    client.ClientPort := 50001        -- 本地未被占用的端口（1025–32025）
    print "Connecting Server"
    MySocket.On := true
    print "Authrizing"
    m_sendauth                        -- 紧接着发 auth 包
end
```

> **值得抄**：
> - **三态机显式化**：`auth_success := false` / `session_id := ""` 先重置本地状态，
>   再连接，再 auth。`m_authback` 收到 `"ok"` 才把 `auth_success` 翻 true
>   （外部 caller 轮询这个 flag 决定能不能继续发 `simtalk_run`）。
> - **空 host / 注释化硬编码 IP**：`-- 替换为目标服务器 IP` —— v2 把 IP 写在
>   Method 源码里而不是 Variable 上。**这是反模式**——应该用 `current.~.ServerIP` 之类的
>   Variable，让 agent 能 `local-simtalk-modify-object-atrribute` 改而无需编辑源码。

### 2.4 防御性 action_id 校验（v2 新增）

**v2 `main/SimtalkAction.ReadLogFile`**：

```simtalk
param action:json
//构造回复"action_id"
if not action.contains("action_id") then
    throwRuntimeError("invalid json,mission action_id")
end
action_result["type"]       := action["type"]
action_result["action_id"]  := action["action_id"]
action_result["log"]        := a_readlog
...
```

> **值得抄**：所有 entry handler 第一件事是**校验必填字段**，缺失直接 `throwRuntimeError`，
> 不静默继续。v1 的 handler 没有这层校验，意味着客户端漏发 `action_id` 会导致
> `action_result["action_id"] := action["action_id"]` 拿到 `VOID`，后续
> agent 端做"请求-响应对齐"时直接错过这条 reply。

### 2.5 handler 出口的 json 容器清理（v2 新增）

**v2 `main/SimtalkAction.get_simtalk_hasError` 末尾**：

```simtalk
// 出口清理：把 action_result 容器里的字段清空，避免下次 handler 误读旧字段
action_result["type"]      := ""
action_result["action_id"] := ""
action_result["result"]   := ""
action_result["log"]      := ""
```

> **值得抄**：`action_result` 是一个**被复用的 json Variable**（不是每次 handler
> 都 new 一个）—— `Run_Simutalk` / `get_simtalk_hasError` / `ReadLogFile` 共用同一个
> 容器。如果出口不清理，下次 handler 进来时残留的旧字段会污染 reply JSON。
> v1 没有这步清理，是隐藏的 bug。**新工程必须照抄这一步**。

### 2.6 Connection 层与 main 层的实例化关系（v2 比 v1 更复杂）

```
.SimtalkClaude2.Objects                ← 引用层（Method 类模板，0 个方法定义，纯文档）
├── Method                             ← Method class 引用实例
.connection                            ← 连接层 Frame 实例
├── SocketClient                        ← 客户端类实例（业务 socket 句柄所在）
├── SocketServer                        ← 服务端类实例
└── socketcallback                       ← 路由分发
.main                                  ← 运行时实例
├── Server (boolean Variable)
├── SocketServer (引用 .connection.SocketServer)
├── SocketClient (引用 .connection.SocketClient)
├── session_id / token / sig (Variables)
└── SimtalkAction                       ← 业务分发 Frame
    ├── Run_Simutalk
    ├── get_simtalk_hasError
    ├── ReadLogFile
    ├── simtalkcode   ← scratch buffer（被 simtalk_run 反复覆盖）
    ├── ErrorHandler
    └── ...
.src                                    ← Class Library 模板
├── autoexec
├── ErrorHandler
├── SimtalkAction (上面那些 method 的"类定义"副本)
└── ...
```

> **值得抄 / 故意取舍**：
> - **三层同名 method**（`.connection.X` / `.main.X` / `.src.X`），
>   `main` 里的 method `Origin` 指向 `.connection.X`（或 `.src.X`），
>   实现"实例 = 继承 root"的标准 Plant Simulation 用法。
> - **debug 时改 `.connection.X`**（root 定义）会影响所有继承路径；
>   改 `.main.X` 只影响单个实例。Factory51 的 simtalkclaude2 选择"只改 root、
>   不改实例"，保证多 agent 同时连接同一个模型时行为一致。

---

## 三、Factory51 业务侧 vs SimtalkClaude 工具侧的耦合点

> 这是最容易出 bug 的地方——SimtalkClaude 不是 Factory51 自带的东西，
> 它的存在**不应影响 Factory51 业务的仿真结果**。

### 3.1 命名空间隔离

| 路径 | 归属 | 影响范围 |
|---|---|---|
| `.Models.Factory51.P1` 等 | Factory51 业务 | 仿真业务逻辑 |
| `.UserObjects.Production` 等 | Factory51 业务 | 业务类定义 |
| `.SimtalkClaude` / `.SimtalkClaude2` | 工具桥 | 仅 TCP 通信，**不影响仿真** |
| `.ApplicationObjects.HBW3D` 等 | 第三方库 | 业务类定义 |

> **隔离测试方法**：
> 1. 把 `.SimtalkClaude2` Frame 整体删掉，Factory51 模型仍能完整运行（卡车、生产线、立体库）。
> 2. 把 `.Models.Factory51` 整体替换成空 Frame，`.SimtalkClaude2` 仍能 ping/鉴权成功。
> 3. 这两个事实说明**两边 100% 隔离**。

### 3.2 simtalk_run 可触达范围（理论上）

> 任何 `simtalk_run` 跑出的 SimTalk 都通过 `executeSilent(&simtalkcode.program)`
> 在 Plant Simulation 主进程里跑，能**修改任何对象**。这意味着——
> 一个拿到鉴权的 agent **有权限破坏 Factory51 的业务状态**（改 P1.NumAGVs = 0
> 让产线停摆、删 Source 让卡车不再生成等）。

| 风险 | 缓解 |
|---|---|
| agent 误改业务对象 | 鉴权 + 在服务端加 `j["action"]` 白名单 |
| agent 看错路径改错对象 | `current.~.x.~.y` 必须先用 `local-simtalk-get-folder-tree` 验证 |
| 仿真中跑 simtalk_run 影响 EventController | 服务端在 EventController paused 时拒绝 simtalk_run |

> **建议在 v3 里加**：
> ```simtalk
> -- Run_Simutalk 入口
> if current.~.Models.Factory51.EventController.~.isRunning
>     throwRuntimeError("simtalk_run refused: simulation is running")
> end
> ```

---

## 四、可继续挖掘的方向（留给后续 session）

1. **`m_str_send` 真实用途**：v2 注释说"作为老协议兼容入口"，但代码里**没有任何调用方
   发字符串**——也就是说 `m_str_send` 是 dead code。**建议在 v3 里删掉**。
2. **`Logger/logdata` DataTable 写入**：v2 的 `connection/socketcallback` 处理 `"response"`
   时只有一行 `debug`，**没有任何写入 Logger 的代码**。和 v1 一样，这里是日志黑洞。
3. **`socketcallback` 的 case 缺少 `"readlog"`**：v1 的 `m_callback` case 有 `readlog`，
   v2 的 `socketcallback` 只有 `auth` / `action` / `response`——意味着 v2 的客户端模式
   **无法收到 readlog 回复**。**这是 v2 的真 bug**。
4. **`sig` 字段留空**：`m_sendauth` 的 `auth["sig"] := sig` 是从 Variable 读，Variable
   初始值是什么？**待确认**——若是空串，服务端鉴权永远失败。
5. **Factory51 的 `EventController.~.isRunning`**：v3 应当做服务端闸口，仿真中拒绝 simtalk_run。

---

## 五、本次实测 / 离线分析的工作流记录

| 步骤 | 操作 | 结果 |
|---|---|---|
| 1 | 检查 TCP 端口 50001/50007 是否监听 | **无监听** —— Plant Simulation 未运行 |
| 2 | 检查 Plant Simulation 进程 | **未运行** |
| 3 | `find` 搜 Factory51 内的 `SimtalkClaude` | **未在 `.psfm` 目录 bundle 内发现** —— 用户当前未把模型持久化到这份 bundle，或 bundle 是早于导入 simtalkclaude 的版本 |
| 4 | `find` 搜 `SimtalkClaude`/`SimtalkClaude2` 在仓库 | **命中**：v1 在 `02-simulation-file-experience/simtalkclaude-best-practices.md`，v2 在 `skills/local-simtalk-add-note-to-method/code_log/SimtalkClaude2_*` |
| 5 | 对比 v1 vs v2 method 清单 | v2 多 3 个 method：`m_sendauth`、`m_authback`、`m_str_send`、`socketcallback`（共 4 个） |
| 6 | 读 v2 各新增 method 源码 | 整理出 §2 的 6 条新模式 |

> **结论**：本次分析**没有跑任何 `simtalk_run`**——所有发现来自磁盘上的 `code_log/` 备份
> 与已有 `.md` 文档。**用户如需基于 live 模型二次确认，需先把 Plant Simulation 启动并加载
> Factory51**，再跑 `local-simtalk-get-folder-tree` + `local-simtalk-read-library` 重新 dump。
> 本文档的 §四 "可继续挖掘的方向"是给那个 session 留的。