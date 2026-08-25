# 消息协议 / Message Schema

本文件定义 Claude 通过 `socket_client.py` 与 Plant Simulation TCP 服务端交互的所有 JSON 消息。

> **硬规则（连接目标 / 分帧方式 / `type` 白名单 / 模态陷阱 / 当前 readlog 状态）全部集中维护在 `references/lifelines.md`，本文件不再重复展开。**

所有载荷都以 UTF-8 编码，并以 `||END||` 作为帧分隔符。**服务端不会主动关闭连接**——必须显式指定 delimiter 模式读取回包（详见 `lifelines.md` §2）。

> Note: 服务器/客户端方向仅是约定视角——实际传输在客户端 socket ↔ 服务端 socket 之间。

## 通用字段 / Common Fields

| 字段 | 必填 | 说明 |
|---|---|---|
| `type` | 是 | 消息类型（见下表） |
| `action_id` | 是 | 客户端生成的 UUID/字符串，用于把请求与响应配对 |
| `timestamp` | 否 | ISO-8601 时间戳，客户端可选填 |

| 消息类型 | 方向 | 用途 |
|---|---|---|
| `ping` | client → server | 连通性检查（可选时间戳），确认链路可用 |
| `simtalk_syntax` | client → server | 仅做编译/语法检查，不真正执行 |
| `simtalk_run` | client → server | 在 `.current` 上执行一段 SimTalk 表达式并返回结果 |
| `readlog` | client → server | 拉取服务端应用日志（socket I/O / Log file opened 等）——注意：**不是 Plant Simulation GUI Console 的 `print()` 输出** |
| `action_result` | server → client | 对 `simtalk_syntax` / `simtalk_run` / `readlog` 的统一回包 |
| `ping` | server → client | 对 `ping` 的回包；当前服务端在 `type` 字段回显请求类型 |

---

## `ping` — 连通性检查

请求（client → server）：
```json
{
  "type": "ping",
  "timestamp": "20260824170056"
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `timestamp` | 否 | 客户端时间戳（可选） |

回包为 `{"type":"ping","result":"success"}`（服务端在 `type` 字段回显请求类型，而非使用独立的 `result` 信封）；网络不通则收不到回复。

---

## `simtalk_syntax` — 仅检查语法

请求（client → server）：
```json
{
  "type": "simtalk_syntax",
  "action_id": "644c86747baa465b8e67b7457a4529f4",
  "simtalk_code": "-> boolean"
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `simtalk_code` | 是 | SimTalk 源码片段（单行或完整方法体）。字段名是 `simtalk_code`，**不是** `simtalk`——服务端只认这个名字 |
| `target_path` | 否 | 限定到某个对象上做解析（例如 `.Models.Model.m`） |

## `action_result` — 统一回包

响应（server → client）：
```json
{
  "type": "action_result",
  "action_id": "644c86747baa465b8e67b7457a4529f4",
  "result": "failed",
  "log": "2026-08-06 13:15:59: Log file opened! Application Version: 2606.0002, UTC: 2026-08-06 05:15:59\n2026-08-06 14:25:46: print('hello from SimTalk') hasError ： Syntax error near line 1 at '''. (in row :1)"
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `result` | 是 | **⚠️ 两条路径语义不一致，必须按请求 `type` 分支处理**：<br>• `simtalk_syntax` 路径（v7+）：承载**诊断文本**，判定方式为「**不含 `"hasError"` 子串 = 成功**；含 = 失败」。典型成功值：`"has no Error"`；典型失败值：`" hasError ： Syntax error near line N at '<token>'. (in row :N)"`<br>• `simtalk_run` 路径：仍是字面量 `"success"` / `"failed"` / `"timeout"`，**但运行时异常（如除零、未知标识符）也会返回 `"success"`**，错误细节改走 `log`——必须配合 `log` 前缀双重检查（详见 Quirk #7） |
| `log` | 否 | `simtalk_run` 路径通常可信（v9 验证）；`simtalk_syntax` 路径下 **不稳定**（v10 复测：成功用例下也常返回陈年缓存错误文本，失败用例反而返回 `"execute success"`）——**`simtalk_syntax` 路径下请用 `result` 字段判断，不要用 `log`** |
| `data` | 否 | **当前 `simtalk_run` 的 `data` 字段实测始终为空**（v6 T4-T6 + v8 T2-T4 + v9 R4a-d 穷举 4 种 `return X` 形式 + `return_value:true` 标记，全部不出现）——服务端 `Run_Simutalk` 是 `-> void`，不会把表达式的值回填进来。**`data` 字段永远不要读** |
| `error` | 否 | 当 `result != "success"` 时，机器可读的错误摘要 |
| `retsult` | 否 | ⚠️ **服务端缓存的历史诊断，与本次请求无关**。从 v2 到 v10 多次复现：同一 `retsult` 值在不同 `simtalk_code` 下原样出现，与 `result` 字段自相矛盾（v6 T4 `result:"success"` 时 `retsult` 仍是陈年的 `"Syntax error near line 1 at 'is'"`）。**永远不要**据此判断成功/失败，请用 `result` + `log` |
| `duration_ms` | 否 | 服务器端处理耗时（可选） |

> Claude 解读规则：
> - **按 `type` 分支**（Quirk #6）：`simtalk_syntax` 看 `result` 是否含 `"hasError"`；`simtalk_run` 走下面的双重检查
> - **`simtalk_run` 成功判据**（Quirk #7）：`result == "success" AND not log.startswith("code execute failed")`——只看 `result` 会漏掉运行时异常
> - **`simtalk_run` 失败排查**：在 `log` 中搜索 `Syntax error near line N` / `hasError` / `(in row :N)` / `code execute failed. error msg:` 等关键字定位问题
> - **永远不要读 `data` 字段**——`simtalk_run` 实测下 `data` 始终为空（v8+v9 穷举验证）；也不要读 `retsult`——那是历史缓存
> - `result == "timeout"` → 不修改代码，先考虑提高 `--timeout`（模态陷阱也会导致 timeout——见 Quirk #6 anti-pattern + #8）

## `simtalk_run` — 执行表达式

请求：
```json
{
  "type": "simtalk_run",
  "action_id": "f1c0...",
  "simtalk_code": "print('hello from SimTalk')"
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `simtalk_code` | 是 | 单条 SimTalk 表达式或语句。与 `simtalk_syntax` 共用字段名 `simtalk_code`，**不要**写 `expression` |
| `context_path` | 否 | `.current` 之外的执行上下文，例如 `path.to.Machine` |
| `return_value` | 否 | 请求服务端把表达式结果写回 `data` 字段。**实测无效**（v6 T5 + v8 T2-T4 + v9 R4a-d）：`return_value:true` 与不带这个标记的回包完全一致；`-> T\nreturn X` 能让代码合法且可执行，但 `data` 字段始终为空——服务端 `Run_Simutalk` 是 `-> void`，不会把内层方法返回值序列化到 socket 回传。如服务端将来升级支持返回值，本字段才有意义 |

回包仍是 `action_result`；**`data` 字段当前始终不出现**——服务端 `Run_Simutalk` 是 `-> void`，不会把 `return X` 的值序列化进 socket 回传（见上方 `data` 字段说明）。

> ⚠️ **模态陷阱**：`simtalk_run` 的执行上下文是 Plant Simulation 的 GUI 进程。如果你的 `simtalk_code` 含有 `prompt` / `promptList1` / `promptListN` / `infoBox` 这些**模态 I/O 函数**（见 `01-plantsimulation-knowledge/.../input-output.md`），GUI 会弹出对话框直到用户点击 OK——服务端因此阻塞，socket 永远拿不到回包，表现跟 v3-v5 的"卡死 60s"一模一样。
>
> 规避：
> - **不要**在 `simtalk_run` 里写 `prompt(...)` / `infoBox(...)` / `promptList1(...)` / `promptListN(...)`
> - 输出值请用 `print(X)` 写到 Plant Simulation 的 **Console**（Window ribbon tab → Console 按钮），去 GUI 面板查看
> - socket 端只能确认"执行成功/失败"，**永远拿不到** `print` 的实际值

---

## `readlog` — 拉取服务端日志（含 GUI Console 输出）

> ⚠️ **v15+ 当前服务端构建下 readlog 已回归 v12 状态**：
> - **不再**捕获 Plant Simulation GUI Console 的 `print(...)` 输出
> - **存在**反馈循环 bug——buffer 体积指数膨胀到 65536 字节被截断
> - **不要**把 readlog 写进自动化/监控循环；仅供一次性调试使用
> - 取 `print(...)` 实际值请去 Plant Simulation GUI Console（Window ribbon → Console 按钮）肉眼读
> - 详见 `lifelines.md` §5 和 v15 测试日志 §6
>
> 历史背景——v13 短暂修复：readlog 当时能返回 GUI Console 输出 + 使用独立缓冲 + 每次调用重置，详见 `log/test-session-20260825-v13.md`。

请求：
```json
{
  "type": "readlog",
  "action_id": "644c86747baa465b8e67b7457a4529f4"
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `action_id` | 是 | 客户端生成的 UUID/字符串，用于把请求与响应配对 |

回包（`action_result`）：
```json
{
  "type": "action_result",
  "action_id": "644c86747baa465b8e67b7457a4529f4",
  "result": "success",
  "log": "2026-08-25 10:21:08: Log file opened! Application Version: 2606.0002, UTC: 2026-08-25 02:21:08\n2026-08-25 10:21:34: BUF_TEST_X\n2026-08-25 10:21:34: BUF_TEST_Y\n"
}
```

每条日志行的格式：`YYYY-MM-DD HH:MM:SS: <text>`。

> **v13 短暂修复时 readlog 能返回的东西**（仅历史记录，**v15+ 已回归**）：
>
> | 来源 | v13 是否出现 | v15+ 状态 | 备注 |
> |---|---|---|---|
> | Plant Simulation GUI Console 的 `print(...)` 输出 | ✅ **是** | ❌ **否**（已回归） | `print "X"` → `2026-08-25 10:21:34: X` |
> | `print` 表达式的实际值（如 `print 42+41`） | ✅ **是** | 表达式求值后写入 Console，readlog 同样拉到 |
> | `Log file opened! Application Version: ...` | ✅ 是 | 每次 readlog 缓冲重置时打一条标记 |
> | 服务端 socket I/O 通讯 trace（`Copilot -->> Local: ...` / `Local -->> Copilot: ...`） | ❌ **否** | v13 已修复——readlog 不再记录服务端自己的 I/O trace |
> | `Sent successfully` 收发确认 | ❌ **否** | 同上 |
> | `simtalk_syntax` / `simtalk_run` 的 `log` 诊断文本 | ❌ **否**（在 action_result 的 `log` 字段里；readlog 不重复） | 通过 `simtalk_syntax` / `simtalk_run` 的回包直接读 |
>
> **简单说**：v13 起 `readlog` = GUI Console 拉取通道 + 服务端日志起始标记（`Log file opened`）。**Socket 端第一次能拿到 `print(...)` 的实际值**——`simtalk_run` 的 `data` 字段依然永远为空（Quirk #6 不变），但 readlog 可以拿到 print 写进 Console 的内容。
>
> **重要新行为——缓冲重置（v13 R4 验证）**：
>
> 服务端 readlog 内部维护一个独立日志缓冲。每次 readlog 调用：
> 1. 打开/重置缓冲，写一条 `Log file opened! Application Version: ...` 标记
> 2. 把"上次 readlog 之后"的新 Console 输出追加进缓冲
> 3. 把缓冲内容作为 `log` 字段返回
> 4. 清空缓冲
>
> 实测序列（v13 R4）：
> ```
> print "X"        # 服务端缓冲记下 X
> print "Y"        # 服务端缓冲记下 Y
> readlog #1       # log: "...Log file opened...\n... X\n... Y"
> print "Z"        # 服务端缓冲记下 Z
> readlog #2       # log: "...Log file opened...\n... Z"   ← X / Y 不再出现
> ```
>
> **使用建议**：
> - **轮询场景**：每次 readlog 拿到的是"自上次 readlog 之后"的增量，**不会重复**，**不会膨胀**——可以放心在监控/测试循环里调用
> - **拿 print 值的标准流程**：`simtalk_run "print <expr>"` → `readlog`，从 `log` 里抽 `<expr>` 所在的那一行（用唯一标记字符串定位行号最稳）
> - **跨 readlog 的状态**：readlog 缓冲不跨调用保留，所以**不要**期望"连续两次 readlog 能拿到完整历史"

---

## 已知服务端行为差异 / Known Server Quirks

> 以下行为已在 2026-08-24 测试会话中由服务端日志确认，记录在这里避免后续踩坑。

1. **`ping` 回包 `type` 字段回显请求类型**
   - 文档曾记为 `{"type":"result","result":"success"}`，但当前服务端实际回的是 `{"type":"ping","result":"success"}`。
   - 任何按 `type == "result"` 做分流的消费者都会被这条不一致坑到；统一按"请求里写的 `type` 就是回包里的 `type`"来处理更稳。

2. **字段名严格区分**
   - `simtalk_syntax` / `simtalk_run` 一律用 `simtalk_code`（**不是** `simtalk`、**不是** `expression`）。
   - 服务端在 `SimtalkAction.get_simtalk_hasError` 第 4 行严格按 `simtalk_code` 取值；写错字段名会得到服务端错误日志 `An item with the identifier 'simtalk_code' was not found`，但**不会有任何回包**。

3. **服务端对异常分支不写回包**
   - 字段缺失 / JSON 解析失败时，服务端只在 stderr 写日志、不向 socket 发送 `||END||` 结束的回包——客户端会一直等到 `--timeout` 才退出（退出码 1）。
   - 排查这种"看似挂死"时，先看服务端日志；如果日志里出现 `simtalk_code was not found` 或 `Error in JSON data: Syntax error`，就是字段或 JSON 字面量错了，而不是网络问题。

4. **`||END||` 帧分隔符对请求侧是可选的**
   - 服务端按"读到可解析的 JSON 就处理"工作，请求末尾加不加 `||END||` 都进同一条处理路径（已在 t2d 测试中验证：未带 `||END||` 仍得到相同的 `simtalk_code` 字段缺失错）。
   - 但**回复**侧必须按 `--resp-mode delimiter --resp-delimiter '||END||'` 读取，否则 `socket_client.py` 会一直阻塞到超时。

5. **`retsult` 字段是历史缓存，与本次请求无关**（v2–v10 多次复现）
   - 从 v2（`simtalk_syntax` 首次拿到回包）到 v10（`simtalk_syntax` 多参/默认值/`byref` 等各种成功用例下仍返回陈年的 `"Syntax error near line 1 at 'is'"`）多次复现
   - 服务端似乎在某个全局变量/缓存里残留了"上一次有错误的请求"的诊断，每次回包都顺手塞进 `retsult`
   - **消费规则**：永远以 `result` 为状态判断依据、`log` 为本次诊断、`retsult` **直接忽略**

6. **`simtalk_syntax` 与 `simtalk_run` 的 `result` 字段语义不一致**（v7 引入）
   - `simtalk_syntax`（v7+）：`result` 是**诊断文本**——`"has no Error"` = 成功；`" hasError ： ..."` = 失败
   - `simtalk_run`：`result` 是字面量——`"success"` / `"failed"` / `"timeout"`
   - **消费规则**：必须按请求 `type` 分支处理——不能写 `if result == "success"` 一刀切
   - 修复方向：服务端应统一为 v6 之前的"result = success/failed 字面量 + log = 诊断文本"，方便消费方

7. **`simtalk_run` 对运行时异常仍返回 `result:"success"`**（v9 R11 / v10 R1 验证）
   - 编译错误（语法错、类型不匹配）→ `result:"failed"` + `log` 含 `" hasError ： ..."`
   - **运行时异常（除零、未知标识符等）→ `result:"success"` + `log` 含 `"code execute failed. error msg:..."`**——这是用户主动设计（v9 用户澄清"是用户在干预"），意图是让消费方从 `log` 读错误细节。
   - **消费规则**：`simtalk_run` 成功判据必须**双重检查**：
     ```text
     result == "success"  AND  not log.startswith("code execute failed")
     ```
   - 不要建议服务端"修复"这条——是设计意图。

8. **`simtalk_run` 写不存在的全局 attribute 会触发模态对话框**（v9 R5 验证）
   - `MyAttr := 12345`（`MyAttr` 是当前模型里**还没建**的全局 attribute）会让 Plant Simulation GUI 弹出"是否创建 MyAttr？"模态对话框
   - 服务端阻塞等用户点 OK，socket 永远没回包——表现与 `prompt(...)` 卡死完全一样
   - **规避**：写到局部 `var`（安全）；或先在 GUI 里手工建好 attribute，再在 `simtalk_run` 里写；或干脆只读不写
   - `simtalk_syntax` 不需要 namespace 上下文，所以写不存在的 attr 也能语法通过——陷阱只在执行时触发

9. **`simtalk_syntax` 的 `log` 字段可能返回陈年缓存**（v10 部分推翻 v9）
   - v9 推翻 v8 "`log` 陈年缓存"结论后，v10 又观察到相反现象：T1-T6 等**成功用例**的 `log` 字段是 `" hasError ： Syntax error near line 1 at ''. (in row :1)"`（陈年错误文本），而 T7/T8 **失败用例**的 `log` 反而是 `"execute success"`
   - **消费规则**：`simtalk_syntax` 路径**只用 `result` 字段判断**，`log` 仅作辅助

10. **`param` / `byref` 在 `simtalk_run` 中被静默接受**（v10 验证）
    - 多参签名 `param i:integer,str:string; body`、默认值参数 `param str:string := "x"; body`、`byref` 修饰符都语法合法 + run 成功
    - 服务端对**无调用者**的情况静默放过（未绑定的形参当成局部 var 看待）
    - **不要**依赖此行为做"真引用语义"——只是服务器宽松，不是形参被正确求值

11. **`readlog` 返回服务端应用日志，**不是** Plant Simulation GUI Console 的 `print()` 输出**（v13 短暂修复，**v15+ 当前服务端构建下已回归**）
    - v12 旧 bug：readlog 只返回服务端 socket wrapper 自己的应用日志，**不**返回 GUI Console 输出
    - **v13 短暂修复**：服务端把 GUI Console 的 `print(...)` 输出也写进 readlog 缓冲；v13 R3 中 `print "V13_CLEAN_TEST_ALPHA"` 后 readlog 立刻出现 `2026-08-25 10:20:54: V13_CLEAN_TEST_ALPHA`
    - ⚠️ **v15 回归（2606.0002 构建）**：readlog 回到 v12 的反馈循环模式——`print(...)` 输出**捕获不到**，buffer 体积指数膨胀到 65536 字节被截断。**当前 readlog 不可信**，取 `print(...)` 实际值请去 Plant Simulation GUI Console 肉眼读。详见 v15 测试日志 §6

12. **`readlog` 存在反馈循环 / 递归膨胀 bug**（v13 短暂修复，**v15+ 当前服务端构建下已回归**）
    - v12 旧 bug：服务端把 readlog 自己的响应写进日志，下次 readlog 再把它塞进 `log` 字段，回包体积指数级膨胀
    - **v13 短暂修复**：readlog 使用独立缓冲 + 每次调用重置，v13 R5 连续 4 次 readlog 体积稳定 ≈200 字节
    - ⚠️ **v15 回归**：反馈循环 + 体积爆炸重新出现——v15-rl-01 实测被截断到 65536 字节
    - **当前使用建议**：readlog 仅供一次性调试；**不要**写进自动化循环。详细见 `references/lifelines.md` §5

13. **`type` 字段取值不在白名单内会让 socket 静默挂死**（v16 验证）
    - 白名单：`ping` / `simtalk_syntax` / `simtalk_run` / `readlog`
    - 发送 `{"type":"unknown_xxx",...}` 时服务端**不写回包**，socket 必须靠 `--timeout` 兜底
    - **消费规则**：客户端必须对 `type` 做白名单校验，不要直接发送外部传入的 `type`

---

## 异常抛出行为总览 / Exception Throwing Matrix（v16）

> 服务端在三类异常下的回包形态**不统一**——客户端必须按异常类别分别解析。

| 异常类别 | 触发示例 | 回包信封 | `result` | `log` 前缀 | 挂死？ |
|---|---|---|---|---|---|
| **JSON 解析错** | `this is not json` / `{"x"` / 空载荷 | **裸字符串**（非 action_result） | —— | `Error in JSON data: Syntax error...` / `Unexpected end of string` | ❌ |
| **Schema 字段缺失** | `{}` / `{"action_id":"x"}` / `null` | 裸字符串 | —— | `An item with the identifier 'X' was not found.` | ❌ |
| **Schema 字段类型错** | `{"type":123,...}` | 裸字符串 | —— | `Illegal data type: 'string' or compatible type expected.` | ❌ |
| **未知 `type` 值** | `{"type":"unknown_xxx",...}` | **不回包** | —— | —— | ✅ **挂死到 timeout**（Quirk #13） |
| **SimTalk 编译错** | `var x:integer := 1/0`（常量折叠） | action_result | `failed` | ` hasError ： ...` | ❌ |
| **SimTalk 运行时异常**（用户主动设计的"软失败"） | `print nonExistentSymbol` / `simtalk_run` 无 `simtalk_code` | action_result | `success` | `code execute failed. error msg:...` 或 `There is no calling method in which the thrown runtime error can be raised.` | ❌ |

**客户端应对策略**：

1. **JSON 解析错 / Schema 字段错 / 类型错**：服务端返回**裸字符串**（不是 JSON），客户端要做非 JSON fallback——例如先尝试 `json.loads`，失败则直接显示原始文本。
2. **未知 type 值**：客户端必须**在发送前**做白名单校验，不要让请求离开客户端。
3. **SimTalk 编译错**：服务端正常返回 `action_result` + `result:"failed"`，按 §"通用成功判据" 的 simtalk_syntax 路径处理。
4. **SimTalk 运行时异常**：服务端**软失败**——`result:"success"` + `log` 含 `"code execute failed"`。客户端必须用 §6 双判据检查。这是用户主动设计（v9 R11 验证），**不要建议服务端"修复"**。
5. **服务端进程稳定性**：v16 验证——16 次坏 JSON 风暴后服务端进程健在（ping 和合法 simtalk_run 均正常）。**唯一会让服务端无法响应新请求**的场景是 Quirk #13（未知 type）。

> 完整测试矩阵见 `log/test-session-20260825-v16.md` §7。

