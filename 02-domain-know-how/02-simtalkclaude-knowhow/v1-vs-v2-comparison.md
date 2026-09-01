---
last_updated: 2026-09-01
contributors: [@plant-simulation-expert]
scope: SimtalkClaude v1 vs v2 协议对比、方法清单差异与迁移风险
---

# SimtalkClaude v1 vs v2 对比

## 一、一句话结论

**v2 = v1 + 鉴权 + 双协议 + 连接状态机 + 防御性校验**。

v2 主要在**协议层(auth/str/socketcallback)**做增量,v1 与 v2 的 method 数量相同(各 22 个),但 v2 的 connection 层从 7 个增加到 11 个。

## 二、方法清单差异

| 方法 | v1 | v2 | 说明 |
|---|---|---|---|
| `connection/SocketServer.m_send` | ✅ | ✅ | JSON + `||END||`,v1/v2 共用 |
| `connection/SocketServer.m_callback` | ✅ | ✅ | type-based 路由(v1)/ `socketcallback`(v2) |
| `connection/SocketClient.m_send` | ✅ | ✅ | 同上 |
| `connection/SocketClient.m_openconnection` | ✅ | ✅ | v2 把 auth 收进这里 |
| `connection/SocketClient.m_disconnect` | ✅ | ✅ | 同上 |
| `connection/SocketClient.m_recieve` | ✅ | ✅ | 同上 |
| `connection/SocketServer.m_str_send` | ❌ | ✅ | **v2 新增**:raw 字符串分帧,**dead code** |
| `connection/SocketClient.m_sendauth` | ❌ | ✅ | **v2 新增**:发鉴权包 |
| `connection/SocketClient.m_authback` | ❌ | ✅ | **v2 新增**:处理鉴权回包 |
| `connection/socketcallback` | ❌ | ✅ | **v2 新增**:服务端回调路由 |
| `main/SimtalkAction.Run_Simutalk` | ✅ | ✅ | 路径一致,v2 多了 `throwRuntimeError` 校验 |
| `main/SimtalkAction.get_simtalk_hasError` | ✅ | ✅ | v2 多了 handler 出口 json 容器清理 |
| `main/SimtalkAction.ReadLogFile` | ✅ | ✅ | v2 多了 `action_id` 校验 |
| `main/SimtalkAction.simtalkcode` | ✅ | ✅ | scratch buffer,未变 |
| `main/SimtalkAction.ErrorHandler` | ✅ | ✅ | 同 v1(除零 → 1e300) |
| `src/autoexec` | ✅ | ✅ | Console/log 三连清理,未变 |
| `Objects/Method` | ✅ | ✅ | 引用实例,未变 |

## 三、协议差异

| 字段 | v1 | v2 |
|---|---|---|
| **无鉴权** | ✅(任何人可调 simtalk_run) | ❌ → ✅ **必须 auth 后才有 action** |
| **认证字段** | — | `token` / `ts`(Unix epoch 秒)/ `sig`(待实现 HMAC)/ `session_id`(reply) |
| **支持 `"type":"auth"`** | ❌ | ✅ |
| **支持 `"type":"response"`** | ❌ | ✅ |
| **支持 `"type":"readlog"`**(v1 m_callback case) | ✅ | ❌ **v2 bug**:socketcallback 没有 readlog |
| **支持 `"type":"simtalk_run"` / `"simtalk_syntax"`** | ✅ | ✅ |

## 四、v2 新增功能详解

### 4.1 鉴权握手(唯一关键安全升级)

v1 完全无鉴权——任何能连上 `50001` 的客户端都可以运行任意 SimTalk。Factory51 这类高价值模型上线时应使用 v2。

v2 客户端连接状态机:

```simtalk
-- m_openconnection
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
  m_sendauth                       -- v2 新增
end
```

> **不应把 `ServerIP` 硬编码在 Method 源码中**;应放入 `ServerIP` Variable,便于运行时修改。

### 4.2 双协议分帧:`m_str_send`(旧)+ `m_send`(新)

v2 保留 v1 的 `m_send(jsondata)` 路径,并增加 `m_str_send(msgStr)` 发送"原始字符串 + `||END||`"的路径。

**新工程应只保留 `m_send(jsondata)`**;同时存在两种帧格式会增加 parser 复杂度。v2 内部目前没有调用方发送字符串,因此 `m_str_send` 是 dead code。

### 4.3 handler 入口校验 + 出口清理

v2 的 `ReadLogFile` 在入口校验必填字段:

```simtalk
param action: json
if not action.contains("" "action_id") then
  throwRuntimeError("invalid json, mission action_id")
end
```

所有 handler 入口都应先校验必填字段,缺失时直接抛错,不静默继续。

v2 在 `get_simtalk_hasError` 末尾清理复用容器:

```simtalk
action_result["type"]      := ""
action_result["action_id"] := ""
action_result["result"]    := ""
action_result["log"]       := ""
```

`action_result` 是被复用的 JSON Variable,不是每个 handler 都新建一个容器。新工程必须在 handler 出口清理。

### 4.4 三层同名 method 的实例化关系

```
.SimtalkClaude2.Objects                ← 引用层(0 个方法定义)
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

三层同名 method(`.connection.X`、`.main.X`、`.src.X`)中,`main` 方法的 `Origin` 指向 `.connection.X` 或 `.src.X`。Factory51 只修改 root 定义,保证多个 agent 共享同一行为。

## 五、迁移 v1 → v2 的兼容性风险

| 风险 | 严重度 | 缓解 |
|---|---|---|
| 老客户端只发 `"type":"ping"`,不发 `"type":"auth"` | 中 | v2 server 应当在 `socketcallback` 里把 ping 也作为"无 auth 即可"的请求处理 |
| v2 `socketcallback` 没有 `"type":"readlog"` case | **高**(v2 真 bug) | 应当从 v1 的 `m_callback` 把 readlog case 复制过来 |
| v2 `m_str_send` 是 dead code | 低 | 删除 |
| `sig` 字段在 v2 没真实现 | 高(auth 必然失败) | 必须实现 HMAC,否则 auth 退化为 no-op |
| `current.~.server` boolean 仍存在 | 低 | 保留,作为 client/server mode 切换 |

> **结论**:**不建议直接把 v1 模型升级到 v2**——v2 协议不向后兼容。
> 老 agent 端代码(只发 `simtalk_run`,不处理 `auth` reply)会全部失败。
> 应当跑**双轨**:v1 旧客户端继续连 v1 server(无 auth),新客户端必须实现 auth 流程。

## 六、当前仓库的实际版本使用

- **当前默认:v1**(`host.docker.internal:50007`)
- v2 用于接入 Siemens Factory51 等高价值模型
- 端口可由用户在 Plant Simulation 端 `.SimtalkClaude2` Frame 的 `mySocket.create("<port>")` 变量中**手动 rebind**(实际生产已观察到 50007 → 50009 切换)

## 经验 Log

> 本节是 **append-only** 时间线——新发现直接追加在末尾。

<!-- 暂无 entry——首个 entry 由下次踩坑时 append -->