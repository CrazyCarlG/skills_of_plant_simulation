# 载荷模板 / Payload Templates

下列模板可以直接复制后填充变量。**所有模板都需要替换 `<action_id>`**——用 uuid4/hex 等唯一字符串即可。

当前协议消息：`ping`（连通性检查）、`simtalk_syntax`（仅语法检查）、`simtalk_run`（执行表达式）、`readlog`（拉取服务端应用日志）；后三者回包统一为 `action_result`。`type` 取值受白名单约束（详见 `references/lifelines.md` §3）。字段定义见 `message-schema.md`。

消息以 `||END||` 作为帧分隔符：请求末尾追加 `||END||`，回复以 `||END||` 结尾。统一发送命令（`<json>` 换成下面的具体载荷）：

```bash
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host <host> --port <port> \
  --data '<json>||END||' \
  --resp-mode delimiter --resp-delimiter '||END||' \
  [--timeout <秒>]
```

> **所有"必须 / 禁止 / 会挂死"的铁律集中在 `references/lifelines.md`**，包括：
> - WSL2 容器连接目标（`host.docker.internal:50007`，详见 `lifelines.md` §1）
> - 回复分帧必须用 `--resp-mode delimiter --resp-delimiter '||END||'`（详见 `lifelines.md` §2）
> - `type` 字段白名单（未知 type 静默挂死——Quirk #13，详见 `lifelines.md` §3）
> - 模态陷阱（详见 `lifelines.md` §4）
> - 当前 readlog 状态（v15+ 已回归 v12，详见 `lifelines.md` §5）
> - 成功判据（Quirk #6 / #7，详见 `lifelines.md` §6）
>
> 若服务端按行分帧，则改用 `--send-delimiter $'\n' --resp-mode line --resp-delimiter $'\n'`（见 `socket_client.md`）——**当前生产服务端不支持此模式**。

## 模板 0：连通性检查（ping）

```bash
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host host.docker.internal --port 50007 --timeout 5 \
  --data '{"type":"ping","timestamp":"20260824170056"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
```

回包 `{"type":"ping","result":"success"}`（服务端在 `type` 字段回显请求类型）表示链路正常；网络不通则收不到回复。

## 模板 A：语法检查

```bash
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host host.docker.internal --port 50007 --timeout 10 \
  --data '{"type":"simtalk_syntax","action_id":"<id>","simtalk_code":"<simtalk code>"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
```

可选字段 `target_path` 把解析限定到某个对象上（例如 `.Models.Model.m`）。

如果 SimTalk 跨多行，用 Python 拼 JSON 最稳妥（避免 shell 转义）：

```bash
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host host.docker.internal --port 50007 --timeout 10 \
  --data "$(python3 -c 'import json; print(json.dumps({"type":"simtalk_syntax","action_id":"abc123","simtalk_code":"print(\"hi\")\nreturn 1"}))')||END||" \
  --resp-mode delimiter --resp-delimiter '||END||'
```

> 注意：JSON 内的换行必须写成 `\n`，不能直接放真换行。

## 模板 A2：参数声明（v10 实测）

```bash
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host host.docker.internal --port 50007 --timeout 10 \
  --data '{"type":"simtalk_syntax","action_id":"<id>","simtalk_code":"param str:string := \"hello\"; print str"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
```

`param` 关键字在 `simtalk_syntax` **接受**（v10 T1-T6 推翻 v9 的"完全不接受"结论）。可写形式：

| 形式 | sx | rn | 备注 |
|---|---|---|---|
| `param i:integer,str:string; body` | ✅ | ✅ | 单行 `;` 分隔签名与 body |
| `param str:string := "x"; body` | ✅ | ✅ | **默认值参数**——最安全 |
| `param byref str:string; body` | ✅ | ✅ | byref 修饰符合法 |
| `param byref str:string; str := "x"; body` | ✅ | ✅ | byref 形参可重新赋值 |
| `param str:string\nbody` | ✅ | ✅ | 多行形式也接受 |
| `param byref str:string := "x"` | ❌ | n/a | byref 不允许默认值（语言规则） |
| `param byval str:string` | ❌ | n/a | byval 是默认值，显式写不合法 |

**注意**：`simtalk_run` 对未传参的 `param`（无论是否 byref）**静默接受**——服务端把 `simtalk_code` 当方法体执行，没有真正的调用者，param 被当成局部 var 看待。`result:"success"` 不代表"实参被正确绑定"，只是"代码没崩"。

## 模板 B：执行表达式

载荷：

```json
{
  "type": "simtalk_run",
  "action_id": "<id>",
  "simtalk_code": "print('hello from SimTalk')"
}
```

- `simtalk_code`（必填）：单条 SimTalk 表达式或语句。与 `simtalk_syntax` 共用字段名，**不要**写 `expression`。
- `context_path`（可选）：`.current` 之外的执行上下文，例如 `path.to.Machine`。
- `return_value`（可选，**实测无效**）：v6/v7/v8/v9 多次加 `return_value:true` 验证，`data` 字段在所有用例下（integer / string / 加不加 `return_value` 标记）都**不出现**。服务端 `Run_Simutalk` 是 `-> void`，不会把内层 `return X` 的值序列化进 socket 回传。

发送命令：

```bash
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host host.docker.internal --port 50007 --timeout 60 \
  --data '{"type":"simtalk_run","action_id":"<id>","simtalk_code":"print(1+1)"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
```

> ⚠️ **`return X` 必须配 `-> T` 返回类型声明**（v8 推翻了 v6/v7 的旧认知）：
> - v6/v7 文档说"`Run_Simutalk` 是 `-> void` 方法体，所以 `return X` 直接被拒"——**错的**。真实原因是 `simtalk_code` **本身没声明返回类型**（v6 T5 报 `"The method has no return value"`），不是外层方法 void。
> - 带 `-> T` 声明（如 `-> integer\nreturn 1+1`）后 `return X` **合法 + 可执行**（v8 T2/T3/T4 + v9 R4 全部 `result:"success"`）。
> - **但**：`data` 字段始终不出现——服务端执行了 `return X`、给出 `result:"success"`，但**没把值序列化进 socket 回传**。
>
> **取值的唯一可行路径**：
> 1. 用 `print(X)` 把 X 写到 Plant Simulation GUI 的 **Console**（Window ribbon → Console 按钮），人去 GUI 看
> 2. 或者把 X 写到某个**已存在**的全局 attribute（如 `.MyResult := 1+1`），再用一次 `simtalk_run` 读 attribute——但 attribute 的当前值同样**无法通过 socket 拿回**（socket 只能拿 `result:success/failed`）
> 3. 如果将来服务端在 `result:"success"` 的同时把 `return X` 的值序列化进 `data` 字段，`return_value:true` + `data` 字段才有意义

> ⚠️ **成功判据（双重检查，详见 `lifelines.md` §6）**：`simtalk_run` 对运行时异常（除零、未知标识符等）仍然返回 `result:"success"`，错误细节改走 `log`（Quirk #7）。只看 `result == "success"` 会漏掉运行时异常。
> ```text
> result == "success"  AND  not log.startswith("code execute failed")
> ```
> 两个条件必须同时满足。
>
> ⚠️ **模态陷阱（详见 `lifelines.md` §4）**：`prompt` / `promptList1` / `promptListN` / `infoBox` 在 `simtalk_run` 里**禁止使用**——它们会弹出 GUI 对话框直到用户点击 OK，服务端阻塞，socket 永远拿不到回包（表现跟 v3-v5 的"卡死 60s"完全一致）。

## 模板 C：拉取 GUI Console 输出（readlog，⚠️ v15+ 已回归）

> ⚠️ **v15+ readlog 已回归 v12 反馈循环模式**——v13 修复的"独立缓冲 + GUI Console 捕获"在当前服务端构建（2606.0002）下失效：buffer 会把上一条 readlog 的响应嵌套回自己，造成体积指数膨胀；同时捕获不到 `print(...)` 输出。详见 `references/lifelines.md` §5。
>
> **当前使用规则（v15+）**：
> - ⚠️ 不要把 readlog 写进自动化/轮询循环
> - ⚠️ 不要期望从 readlog 拿到 GUI Console 的 `print(...)` 实际值
> - ✅ 调试时偶尔调一次 readlog 确认服务端是否响应即可
> - 取 `print(...)` 实际值请去 Plant Simulation GUI Console（Window ribbon → Console）肉眼读

```bash
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host host.docker.internal --port 50007 --timeout 10 \
  --data '{"type":"readlog","action_id":"<id>"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
```

请求字段：
- `type`: `"readlog"`（必填，受 `lifelines.md` §3 白名单约束）
- `action_id`: 32 字符 hex 推荐（必填）

响应字段（v15+ 已不可信）：
- `result`: 字面量 `"success"` / `"failed"` / `"timeout"`
- `log`: ⚠️ 当前会嵌套上一次 readlog 的响应 + 仅含 `Log file opened! Application Version: ...` 起始标记，**不包含** simtalk_run 的 print 输出
- 其它字段（`data` / `retsult`）一律忽略

**v13 时的标准流程**（v15+ 已不再可靠，仅作历史参考）：
```bash
# 第 1 步：触发 print
python3 socket_client.py ... --data '{"type":"simtalk_run","action_id":"a","simtalk_code":"print UNIQUE_MARKER_QQ\nreturn 1+1"}||END||' ...

# 第 2 步：拉 readlog（buffer 包含 UNIQUE_MARKER_QQ 行）——v15+ 不再成立
python3 socket_client.py ... --data '{"type":"readlog","action_id":"b"}||END||' ...
```

**轮询场景**：v15+ **不要**在循环里调用 readlog（buffer 体积会指数膨胀，触发 `socket_client.py` 的 65536 字节截断）。

## 实用 Bash 助手 / Helper Snippets

用 Python 生成单行 JSON 再交给 `--data`（自动生成唯一 `action_id`）：

```bash
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host host.docker.internal --port 50007 --timeout 30 \
  --data "$(python3 - <<'PY'
import json, uuid
payload = {
    "type": "simtalk_syntax",
    "action_id": uuid.uuid4().hex,
    "simtalk_code": "print('hello from SimTalk')",
}
print(json.dumps(payload))
PY
)||END||" \
  --resp-mode delimiter --resp-delimiter '||END||'
```

> `$(...)` 命令替换会把 Python 输出的单行 JSON 作为 `--data` 参数传入，避免手工转义。

---

## 字段命名备忘 / Field Naming Cheatsheet

- `type`：snake_case 字符串，当前为 `ping` / `simtalk_syntax` / `simtalk_run` / `readlog`
- `action_id`：32 字符 hex 推荐（`uuid.uuid4().hex`）
- `timestamp`（`ping` 可选）：时间戳，例如 `20260824170056`
- `simtalk_code`（`simtalk_syntax` / `simtalk_run` 共用）：使用真实换行需转义为 `\n`；**不要**写 `simtalk` 或 `expression`（服务端只认 `simtalk_code`）
- `target_path`（`simtalk_syntax` 可选）：限定到某个对象上做解析，例如 `.Models.Model.m`
- `context_path`（`simtalk_run` 可选）：`.current` 之外的执行上下文，例如 `path.to.Machine`

## 常见反模式 / Common Anti-patterns

> 与 `references/lifelines.md` §8 同步——本节保留示例细节，铁律性总结以 `lifelines.md` 为准。

1. **❌** 在 shell 里直接写未转义的真换行——JSON 会被拆成多段。
   **✅** 全部使用 `\n` 转义或 Python 拼 JSON。
2. **❌** 同一 `action_id` 复用多次——服务端无法区分请求。
   **✅** 每次发送都生成新 id。
3. **❌** 默认 10 秒 `--timeout` 用于运行仿真。
   **✅** 长任务显式 `--timeout 600` 之类。
4. **❌** 失败后立刻把同一 payload 再发一遍。
   **✅** 看 `log` 字段、定位行号、改代码再发。
5. **❌** 请求末尾漏掉 `||END||`，或读回包时未指定 `--resp-delimiter '||END||'`。
   **✅** 请求末尾追加 `||END||`，并用 `--resp-mode delimiter --resp-delimiter '||END||'` 读取回包（详见 `lifelines.md` §2）。
6. **❌** 在 `simtalk_run` 的 `simtalk_code` 里写 `prompt(...)` / `infoBox(...)` / `promptList1(...)` / `promptListN(...)` —— 服务端卡在模态对话框等用户点 OK，socket 永远没回包，看起来跟 v3-v5 的"卡死 60s"一样。
   **✅** 用 `print(X)` 把数据写到 Plant Simulation GUI 的 Console（Window ribbon → Console 按钮），再去 GUI 查看；或者改用 `simtalk_syntax` 只校验语法而**不执行**，避免 GUI 阻塞（详见 `lifelines.md` §4）。
7. **❌** 在 `simtalk_run` 里**只写 `return X` 而不声明 `-> T` 返回类型**——服务端编译失败（`result:"failed"` + `log:"The method has no return value"`），v6 T5 证实。
   **🟡** 写 `-> T\nreturn X`（如 `-> integer\nreturn 1+1`）**是合法 + 可执行的**——v8 T2/T3/T4 全部 `result:"success"`。**但**：`data` 字段在所有用例下（integer / string / 加不加 `return_value` 标记）都不出现——服务端没把内层 `-> T` 方法的返回值序列化进 socket 回传。
   **✅** 见模板 B 后的"取值"说明；当前唯一可行的取值方式仍是 `print(X)` → Plant Simulation GUI Console。
8. **❌** 在 `simtalk_run` 里写**当前模型尚未声明的全局 attribute**——例如 `MyAttr := 12345`（`MyAttr` 还没建）——Plant Simulation 会弹出"是否创建 MyAttr？"模态对话框等用户点 OK（v9 R5 验证）。表现与 `prompt(...)` 卡死完全一样。
   **✅** 写到局部 `var`（如 `var x: integer := 12345`）；或先在 GUI 里手工建好 attribute，再在 `simtalk_run` 里写；或干脆只读不写（详见 `lifelines.md` §4）。
   注意：`simtalk_syntax` 不需要 namespace 上下文，所以写不存在的 attr 也能语法通过——陷阱只在执行时触发。
9. **❌** `type` 字段不在 `ping` / `simtalk_syntax` / `simtalk_run` / `readlog` 白名单内（如 `{"type":"foo"}`）——服务端**静默挂死到 timeout**，不会回任何错误（Quirk #13，v16 验证）。这是从 v16 异常测试中提取的**新硬规则**。
   **✅** 客户端必须先对 `type` 做白名单校验（详见 `lifelines.md` §3）。
10. **❌** 期望从 `readlog` 拿到 Plant Simulation GUI Console 的 `print(...)` 输出（v15+）——v15+ 已回归 v12 反馈循环模式，readlog 不再捕获 print 输出。`simtalk_run` 的 `data` 字段依然永远为空（Quirk #6 不变）。
    **✅** 去 Plant Simulation GUI Console 肉眼读；或接受"无法通过 socket 取 print 实际值"这个现实（详见 `lifelines.md` §5）。
11. **❌** 把 `readlog` 写进自动化 / 监控 / 测试循环里（v15+）——v15+ 回归后 buffer 体积会指数膨胀，几次就会被 65536 字节截断。
    **✅** 仅在调试时单次调用 readlog；不要进循环（详见 `lifelines.md` §5）。
