# 消息协议 / Message Schema

本文件定义 Claude 通过 `socket_client.py` 与 Plant Simulation TCP 服务端交互的所有 JSON 消息。
所有载荷都以 UTF-8 编码，并以 `||END||` 作为帧分隔符：请求末尾追加 `||END||`，回复以 `||END||` 结尾（读取时用 `--resp-mode delimiter --resp-delimiter '||END||'`）。**服务端不会主动关闭连接**——`--resp-mode eof`（默认）一定超时，**必须**显式指定 delimiter 模式（v2 T4 验证）。

> **客户端连接目标**（WSL2 容器场景）：`host.docker.internal:50007`。`127.0.0.1:50007` / `localhost:50007` 会落到容器自身、连接被拒（v1 T0）。其它环境按实际部署改 host，端口固定 `50007`。

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
| `action_result` | server → client | 对 `simtalk_syntax` / `simtalk_run` 的统一回包 |
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

