---
last_updated: 2026-08-28
contributors: [@z004bjuu, @plant-simulation-expert]
scope: SimtalkClaude v1/v2 的 TCP 帧格式、动作分派、鉴权、回复协议与可复用模式
---

# SimtalkClaude 协议与关键模式

## 三、协议设计要点

### 3.1 帧格式：`json + "||END||"`

```simtalk
-- 发送侧（m_send）
var msgStr: string := jsondata.asString(false) + "||END||"
MySocket.write(channelNo, msgStr)

-- 接收侧（m_callback）
message := regex_replace(message, "\|\|END\|\|", "")
j.parse(message)
```

> **为什么用 `||END||` 而不是换行？**
> SimTalk JSON (`jsondata.asString(false)`) 会保留字符串内的换行符，用 `||END||` 作分隔符可以无歧义切分多个包，不会因为消息体里有 `\n` 而提前断开。

### 3.2 动作分派：`switch j["type"]`

服务端 `SocketServer.m_callback`：

```simtalk
switch type
case "ping"           → m_send(ping_reply)
case "simtalk_syntax" → SimtalkAction.&get_simtalk_hasError.executenewcallchain(j)
case "simtalk_run"    → SimtalkAction.&Run_Simutalk.executenewcallchain(j)
case "readlog"        → SimtalkAction.&ReadLogFile.executenewcallchain(j)
end
```

> `executenewcallchain(j)` 是 Plant Simulation 的“用 JSON 对象做参数调用方法”机制——直接传一个 JSON 进去，对端按 attribute 名取字段，比写一堆 `if j.contains(...)` 干净。

### 3.3 鉴权（v2 新增，v1 无此环节）

```json
client → server:  {"type":"auth", "token":"...", "ts": <unix_seconds>, "sig":"..."}
server → client:  {"type":"auth", "status":"ok", "session_id":"..."}
```

- `ts` 用 Unix epoch 秒（不是毫秒），从 `sysDate - str_to_dateTime("01.01.1970 00:00:00")` 换算
- 收到 `status:"ok"` 才把 `session_id` 写进本地 `Variable`，否则断 socket
- `sig` 字段是预留的 HMAC 签名口子，v2 暂未真正实现 HMAC（Variable 初始值是空串）

### 3.4 回复包统一字段

所有 action 回复都长这样：

```json
{
  "type":      "<echo 原 type>",
  "action_id": "<echo 原 action_id>",
  "result":    "success" | "failed",
  "log":       "<执行日志 / 错误信息>"
}
```

> 把 `action_id` 原样回传是 agent 端做“异步请求-响应对齐”的关键。`action_result` 是被复用的 JSON 容器变量，每个 handler 都要在出口清空。

## 四、关键模式（v1/v2 共用）

### 4.1 用一个 Method 当 SimTalk 代码的 scratch buffer

```simtalk
-- .SimtalkClaude.main.SimtalkAction.simtalkcode 是一个 Method 对象
&simtalkcode.program := code
var errMsg: string; var errLine: integer
var hasError := &simtalkcode.hasSyntaxError(errMsg, errLine)
executeSilent(&simtalkcode.program)
var errMsg := getExecuteSilentError
```

> `hasSyntaxError` / `executeSilent` 只接受已存在的 Method 对象作为代码宿主。把代码写到 `simtalkcode.Program` 后，语法错误和运行时错误都能结构化回传。

### 4.2 `&Method.executenewcallchain(json)` 路由到具体 handler

```simtalk
current.~.simtalkaction.&Run_Simutalk.executenewcallchain(j)
```

- `current.~` 表示父对象上的 SimtalkActionFrame
- `&` 把方法名（内容形式）变成方法对象
- `executenewcallchain` 按 JSON 字段填充参数

### 4.3 客户端/服务端同构：`Server` boolean 开关

```simtalk
if current.~.server
  current.~.SocketServer.m_send(action_result)
else
  current.~.SocketClient.m_send(action_result)
end
```

> 同一份 `SimtalkAction` 既能跑在服务端模式，也能跑在客户端模式。`Server` 是 Frame 上的 boolean Variable。

### 4.4 自动重置：每个 read 之后清理

```simtalk
clearConsole
clearLogFile
openConsole
```

> 这是 Plant Simulation 远程控制场景下的卫生措施：每条 agent 指令结束后重置 Console/log，确保下一次指令从完整因果链开始。

### 4.5 ErrorHandler：吞掉已知良性错误

```simtalk
if error = "Division by zero."
  error := ""
  return 1e300
end
error := "error in " + method_path + ": " + error
return 0
```

> 将“除零”这类已知无害的异常替换成 `1e300`，避免中断长跑仿真；其它异常改写前缀后继续抛，由上层决定是否中止。

## 九、复现这份 dump 的命令

### 9.1 复现 v1 dump

```bash
python3 skills/local-simtalk-get-folder-tree/scripts/bfs_full.py --no-infobox . 5 \
  skills/local-simtalk-read-library/data/tree.json
```

过滤 SimtalkClaude 的方法路径时，使用 `tree.json` 递归查找以 `.SimtalkClaude.` 开头的 `Method`，写入 `simtalkclaude_methods.txt`。探针应使用单方法 + sleep 模式，而不是未经保护的 `BATCH=8`。

### 9.2 复现 v2 dump（Factory51 集成）

v2 dump 来源是 `skills/local-simtalk-add-note-to-method/code_log/SimtalkClaude2_*_program_original.txt`（22 个 method 备份）。

```bash
ls skills/local-simtalk-add-note-to-method/code_log/SimtalkClaude2_*.txt
# 共 22 个文件，每个对应一个 v2 method 的 program 原文
```
