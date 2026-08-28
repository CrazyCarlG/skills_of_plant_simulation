---
last_updated: 2026-08-28
contributors: [@z004bjuu, @plant-simulation-expert]
scope: SimtalkClaude v1/v2 的定位、支持动作、目录分层与后续探索方向
---

# SimtalkClaude 概览

## 一、SimtalkClaude 是什么

一个让**外部 agent 通过 TCP JSON 协议远程驱动 Plant Simulation 模型**的桥梁组件。

对外表现为：连接 `host.docker.internal:50007`（v1 默认）或 `8.137.98.145:50001`（v2），发 `{type, ...}` 动作，收 `{type, result, log, action_id}` 回复。

| 动作 | v1 | v2 |
|---|---|---|
| `ping` | ✅ | ✅ |
| `simtalk_syntax` | ✅ | ✅ |
| `simtalk_run` | ✅ | ✅ |
| `readlog` | ✅ | ❌ **v2 bug**：服务端 `socketcallback` 没有 `readlog` case，客户端模式收不到 readlog 回复 |
| `auth` | ❌ | ✅（v2 新增） |

> **当前本仓库实际用 v1**（默认连 `host.docker.internal:50007`）。v2 用于接入 Siemens Factory51 等高价值模型。

## 二、目录分层的“教科书”做法

```
.SimtalkClaude/
├── connection/   ← 网络传输层（Socket 收发、Logger）
│   ├── SocketClient.*   ← 客户端 socket 封装
│   ├── SocketServer.*   ← 服务端 socket 事件入口
│   └── Logger/          ← 日志 DataTable
├── main/         ← 运行时实例（带 Server / SocketServer / SocketClient / SimtalkAction）
├── src/          ← 库模板（class library，main 实例的来源）
│   ├── autoexec          ← 模型打开即执行
│   ├── ErrorHandler      ← 挂在 Method 对象上的全局错误处理
│   └── SimtalkAction.*   ← 动作分发表
└── Objects/      ← 各内置类的引用实例（Method / Socket / DataList / Button …）
```

| 层 | 职责 | 修改频率 |
|---|---|---|
| `connection/` | 字节收发、心跳、鉴权回包 | 几乎不改 |
| `main/` | 业务实例 + 当前模式（Server flag） | 偶尔改 |
| `src/` | 类库、模板代码 | 经常迭代 |
| `Objects/` | 类引用、文档示例 | 几乎不改 |

> **值得抄**：把“transport / instance / library / reference”四层分开，移植/复用时只换 `connection/`，业务代码不动。

## 十、可继续挖掘的方向

- **`m_str_send` 的实现细节**：v2 当前是 dead code，建议在 v3 删掉。
- **`Logger/logdata`**：v2 的 `Logger.Frame` 下只有一个空的 `DataTable`，预期是记录每次请求/响应，但没有看到任何写入代码。
- **`socketcallback` 缺 `readlog` case**：v1 有，v2 没有，是当前 v2 bug。
- **`sig` 字段留空**：需确认 `m_sendauth` 读取的 `sig` 初始值；若为空，鉴权可能无法成立。
- **`Objects.Method`**：可能是给 Method 对象文档示例用的引用实例。
