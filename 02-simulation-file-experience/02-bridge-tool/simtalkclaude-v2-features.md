---
last_updated: 2026-08-28
contributors: [@z004bjuu, @plant-simulation-expert]
scope: SimtalkClaude v2 相对 v1 的鉴权、分帧、连接、输入校验、容器清理和实例结构
---

# SimtalkClaude v2 新增功能

> v1 与 v2 的方法清单速查见 [`simtalkclaude-v1-v2-delta.md`](./simtalkclaude-v1-v2-delta.md)。

## 6.1 鉴权握手（v2 唯一关键安全升级）

v1 完全无鉴权——任何能连上 `50001` 的客户端都可以运行任意 SimTalk。Factory51 这类高价值模型上线时应使用 v2。

v2 客户端 `connection/SocketClient.m_sendauth`：

```simtalk
var epoch: dateTime := str_to_dateTime("01.01.1970 00:00:00")
var now: dateTime := sysDate
var diffSeconds: real := now - epoch
var tsMillis: integer := round(diffSeconds * 1000)
var tsSeconds: integer := round(diffSeconds)
auth["token"] := token
auth["ts"] := tsSeconds
auth["sig"] := sig
m_send(auth)
```

v2 客户端 `connection/SocketClient.m_authback`：

```simtalk
param j: json
var status := j["status"]
if status = "ok"
  session_id := j["session_id"]
  return
else
  MySocket.On := false
end
```

v2 服务端 `connection/socketcallback` 路由：

```simtalk
switch type
case "auth"
  m_authback(j)
case "action"
  current.~.simtalkaction.get_simtalk_hasError(j)
case "response"
  debug
end
```

- 鉴权失败时立即断开 socket，不要给失败重试留机会。
- `sig` 字段是为后续 HMAC 签名留的口子；当前代码没有真正实现 HMAC。

## 6.2 双协议分帧：`m_str_send`（旧）+ `m_send`（新）

v2 保留 v1 的 `m_send(jsondata)` 路径，并增加 `m_str_send(msgStr)` 发送“原始字符串 + `||END||`”的路径：

```simtalk
param msgStr: string
msgStr := msgStr + "||END||"
var success: boolean := MySocket.write(0, msgStr)
```

新工程应只保留 `m_send(jsondata)`；同时存在两种帧格式会增加 parser 复杂度。v2 内部目前没有调用方发送字符串，因此 `m_str_send` 是 dead code。

## 6.3 连接状态机：`m_openconnection` 原子化 connect + auth

v2 将手动连接和发送 auth 包合并为一个 method：

```simtalk
if MySocket.On = false
  auth_success := false
  session_id := ""
  MySocket.TCP := true
  var client: object := MySocket
  client.ServerSocket := false
  client.TCP := true
  client.Host := "8.137.98.145"
  client.ClientPort := 50001
  print "Connecting Server"
  MySocket.On := true
  print "Authorizing"
  m_sendauth
end
```

- 先重置 `auth_success` 和 `session_id`，再 connect、再 auth，显式化三态流程。
- 不应把 `ServerIP` 硬编码在 Method 源码中；应放入 `ServerIP` Variable，便于运行时修改。

## 6.4 防御性 `action_id` 校验

v2 的 `ReadLogFile` 在入口校验必填字段：

```simtalk
param action: json
if not action.contains("action_id") then
  throwRuntimeError("invalid json, mission action_id")
end
action_result["type"] := action["type"]
action_result["action_id"] := action["action_id"]
action_result["log"] := a_readlog
```

所有 handler 入口都应先校验必填字段，缺失时直接抛错，不静默继续。

## 6.5 handler 出口的 JSON 容器清理

v2 在 `get_simtalk_hasError` 末尾清理复用容器：

```simtalk
action_result["type"] := ""
action_result["action_id"] := ""
action_result["result"] := ""
action_result["log"] := ""
```

`action_result` 是被复用的 JSON Variable，不是每个 handler 都新建一个容器。新工程必须在 handler 出口清理，避免旧字段污染下一次回复。

## 6.6 Connection 层与 main 层的实例化关系

```
.SimtalkClaude2.Objects                ← 引用层（Method 类模板，0 个方法定义）
.connection                            ← 连接层 Frame 实例
├── SocketClient
├── SocketServer
└── socketcallback
.main                                  ← 运行时实例
├── Server (boolean Variable)
├── SocketServer / SocketClient
├── session_id / token / sig
└── SimtalkAction
    ├── Run_Simutalk
    ├── get_simtalk_hasError
    ├── ReadLogFile
    ├── simtalkcode
    ├── ErrorHandler
    └── ...
.src                                    ← Class Library 模板
├── autoexec
├── ErrorHandler
└── SimtalkAction
```

三层同名 method（`.connection.X`、`.main.X`、`.src.X`）中，`main` 方法的 `Origin` 指向 `.connection.X` 或 `.src.X`。Factory51 只修改 root 定义，保证多个 agent 共享同一行为。
