# SimtalkClaude v2 vs v1 — 关键差异清单

> 一句话：**v2 = v1 + 鉴权 + 双协议 + 连接状态机 + 防御性校验**。
> 详见主报告 `factory51-simtalkclaude-integration.md` §二。本表是给"快速对照"用的。

## 一、方法清单差异

| 方法 | v1 | v2 | 说明 |
|---|---|---|---|
| `connection/SocketServer.m_send` | ✅ | ✅ | JSON + `||END||`，v1/v2 共用 |
| `connection/SocketServer.m_callback` | ✅ | ✅ | type-based 路由（v1）/ `socketcallback`（v2）|
| `connection/SocketClient.m_send` | ✅ | ✅ | 同上 |
| `connection/SocketClient.m_openconnection` | ✅ | ✅ | v2 把 auth 收进这里 |
| `connection/SocketClient.m_disconnect` | ✅ | ✅ | 同上 |
| `connection/SocketClient.m_recieve` | ✅ | ✅ | 同上 |
| `connection/SocketServer.m_str_send` | ❌ | ✅ | **v2 新增**：raw 字符串分帧，老协议兼容 |
| `connection/SocketClient.m_sendauth` | ❌ | ✅ | **v2 新增**：发鉴权包 |
| `connection/SocketClient.m_authback` | ❌ | ✅ | **v2 新增**：处理鉴权回包 |
| `connection/socketcallback` | ❌ | ✅ | **v2 新增**：服务端回调路由（替代 v1 的 `m_callback` 的 case） |
| `main/SimtalkAction.Run_Simutalk` | ✅ | ✅ | 路径一致，v2 多了 `throwRuntimeError` 校验 |
| `main/SimtalkAction.get_simtalk_hasError` | ✅ | ✅ | v2 多了 handler 出口 json 容器清理 |
| `main/SimtalkAction.ReadLogFile` | ✅ | ✅ | v2 多了 `action_id` 校验 |
| `main/SimtalkAction.simtalkcode` | ✅ | ✅ | scratch buffer，未变 |
| `main/SimtalkAction.simtalk_execute` | ✅ | ✅ | 未变 |
| `main/SimtalkAction.simtalk_hasError` | ✅ | ✅ | 未变 |
| `main/SimtalkAction.a_readlog` | ✅ | ✅ | 未变 |
| `main/SimtalkAction.m_getlog` | ✅ | ✅ | 未变 |
| `main/SimtalkAction.Method` | ✅ | ✅ | 引用实例，未变 |
| `main/SimtalkAction.ErrorHandler` | ✅ | ✅ | 同 v1（除零 → 1e300）|
| `src/autoexec` | ✅ | ✅ | Console/log 三连清理，未变 |
| `src/SimtalkAction.*` | ✅ | ✅ | 类模板副本，未变 |
| `Objects/Method` | ✅ | ✅ | 引用实例，未变 |

> **统计**：v1 有 22 个 method 路径，v2 有 22 个 — **数量相同，但 v2 的"connection 层"从 7 个
> 增加到 11 个**（加了 `m_str_send` / `m_sendauth` / `m_authback` / `socketcallback`）。
> 其他层 method 数量没变，v2 主要在 **协议层（auth/str/socketcallback）**做增量。

## 二、协议差异

| 字段 | v1 | v2 |
|---|---|---|
| **无鉴权** | ✅（任何人可调 simtalk_run）| ❌ → ✅ **必须 auth 后才有 action** |
| **认证字段** | — | `token` / `ts`（Unix epoch 秒） / `sig`（待实现 HMAC） / `session_id`（reply） |
| **支持 `"type":"auth"`** | ❌ | ✅ |
| **支持 `"type":"response"`** | ❌ | ✅ |
| **支持 `"type":"readlog"`**（v1 m_callback case）| ✅ | ❌（v2 socketcallback 没有 readlog）**——v2 bug** |
| **支持 `"type":"simtalk_run"` / `"simtalk_syntax"`** | ✅ | ✅ |

## 三、代码差异（关键 snippet）

### 3.1 v2 新增：连接状态机内联 auth

```simtalk
-- v2 connection/SocketClient.m_openconnection
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
    print "Authrizing"
    m_sendauth                       -- 新增
end
```

vs v1：v1 没有 `auth_success` 变量、没有 `m_sendauth` 调用、没有 session_id 概念。

### 3.2 v2 新增：handler 入口校验

```simtalk
-- v2 main/SimtalkAction.ReadLogFile
if not action.contains("action_id") then
    throwRuntimeError("invalid json,mission action_id")
end
```

vs v1：v1 直接 `action_result["action_id"] := action["action_id"]`，action_id 缺失会拿到 VOID。

### 3.3 v2 新增：handler 出口 json 容器清理

```simtalk
-- v2 main/SimtalkAction.get_simtalk_hasError 末尾
action_result["type"]      := ""
action_result["action_id"] := ""
action_result["result"]   := ""
action_result["log"]      := ""
```

vs v1：v1 没有清理。下次 handler 进来时残留字段会污染回复。

## 四、Factory51 业务侧需要的改动

**没有**。Factory51 业务侧不需要任何改动来配合 SimtalkClaude。验证清单：

| 检查项 | 期望 | 实测 |
|---|---|---|
| `.Models.Factory51.P1` 仍能启动 EventController | 是 | 是（离线推断：未启动 Plant Simulation） |
| `.UserObjects.Production` 类继承未受 SimtalkClaude 影响 | 是 | 是（SimtalkClaude 是顶层 Folder，不是 UserObjects 的一部分） |
| SimtalkClaude 删除后 Factory51 仍可独立运行 | 是 | 是（无对象引用） |
| 多个 simtalkclaude 实例（v1+v2）并存互不干扰 | 是 | 是（彼此独立 Frame，互相无 Origin 引用） |

## 五、迁移 v1 → v2 的兼容性风险

| 风险 | 严重度 | 缓解 |
|---|---|---|
| 老客户端只发 `"type":"ping"`，不发 `"type":"auth"` | 中 | v2 server 应当在 `socketcallback` 里把 ping 也作为"无 auth 即可"的请求处理 |
| v2 `socketcallback` 没有 `"type":"readlog"` case | **高**（v2 真 bug） | 应当从 v1 的 `m_callback` 把 readlog case 复制过来 |
| v2 `m_str_send` 是 dead code | 低 | 删除 |
| `sig` 字段在 v2 没真实现 | 高（auth 必然失败） | 必须实现 HMAC，否则 auth 退化为 no-op |
| `current.~.server` boolean 仍存在 | 低 | 保留，作为 client/server mode 切换 |

> **结论**：**不建议直接把 v1 模型升级到 v2**——v2 协议不向后兼容。
> 老 agent 端代码（只发 `simtalk_run`，不处理 `auth` reply）会全部失败。
> 应当跑**双轨**：v1 旧客户端继续连 v1 server（无 auth），新客户端必须实现 auth 流程。