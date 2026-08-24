# connector.py 使用说明 / connector.py Reference

`scripts/connector.py` 是一个长连接 TCP 客户端守护进程：它维持一条到 Plant Simulation 服务端的 TCP 连接，本地通过 Unix socket 暴露 `send` 接口。多进程同时调用 `send` 时由守护进程串行化，因此同一时间只有一个请求在飞。

## 子命令一览 / Subcommands

```text
connector.py start  --host <host> --port <port> [--daemon] [其它选项]   启动守护进程
connector.py send   <payload>           [--timeout <秒>]                  发送一帧并阻塞等待回包
connector.py stop   [--name <profile>]                                    停止守护进程
connector.py status [--name <profile>]                                    查看运行状态
```

> `--name <profile>` 允许多个连接共存（默认 `default`），socket 与 pid 文件分别落在 `~/.cache/simtalk-connector/<profile>/`。

## `start` 选项

| 选项 | 默认值 | 含义 |
|---|---|---|
| `--host` | (必填) | Plant Simulation 服务端主机 |
| `--port` | (必填) | 服务端 TCP 端口 |
| `--daemon` | `False` | 双 fork 到后台，否则前台运行 |
| `--reconnect-delay` | `2.0` | 连接断开后重连间隔（秒） |
| `--timeout` | `10.0` | 默认请求超时（秒），`send` 可覆盖 |
| `--resp-mode` | `line` | 响应分帧模式：`line` / `idle` / `fixed` |
| `--resp-delimiter` | `\|\|END\|\|` | `line` 模式的分隔字符串 |
| `--resp-idle` | `1.0` | `idle` 模式判定"安静"所需的秒数 |
| `--resp-length` | `None` | `fixed` 模式的字节数 |
| `--newline` | `True` | 发送时是否自动追加 `\n` |

## `send` 用法

```bash
python3 scripts/connector.py send '<JSON 载荷>' --timeout 30
# 或通过 stdin
echo '<JSON 载荷>' | python3 scripts/connector.py send --timeout 30
```

返回三种状态码（写到 stdout/stderr）：

| 退出码 | 输出 | 含义 |
|---|---|---|
| `0` | 原始响应字节（末尾补 `\n`）写到 stdout | 成功 |
| `1` (TIMEOUT) | `TIMEOUT: <msg>` 写到 stderr | 超时未收到回包 |
| `2` (ERR) | `ERR: <msg>` 写到 stderr | 连接错误 / 服务端中断 / 守护进程不可达 |

> **重要**：成功时 stdout 是**原始字节**，不是 JSON 化的退出码。Claude 解析时应假设它是 UTF-8 JSON，但若服务端偶尔返回非 JSON（例如二进制日志），需要相应 fallback。

## 响应分帧 / Response Framing

Plant Simulation 服务端的输出不是定长，connector 提供三种读取策略，必须在 `start` 时与服务器约定一致：

1. **`line`**（默认）——读到 `--resp-delimiter`（默认 `||END||`）为止；分隔字符串本身会被丢弃。
2. **`idle`** ——服务器静默 `--resp-idle` 秒后认为一帧结束，适合连续日志流。
3. **`fixed`** ——严格读 `--resp-length` 字节，适合二进制/定长协议。

> 三选一**不**要混用；先用 `ping` 包确认默认设置能拿到完整回包，再决定是否调整。

## 本地 IPC 协议 / Local IPC（客户端 ↔ 守护进程）

Claude → 守护进程（`send` 子命令内部使用）：

1. 4 字节大端长度 + JSON meta 字节串（meta 当前仅含 `timeout`）
2. 4 字节大端长度 + 业务载荷字节串

守护进程 → Claude 回包：

1. 1 字节状态码（`0` ok / `1` timeout / `2` error）
2. 4 字节大端长度 + 响应字节串

> 一般 Claude **不需要**直接处理本地 IPC；`send` 子命令已经把它封装好。了解它是为了在调试守护进程 bug 时参考。

## 文件落点 / Runtime Files

```text
~/.cache/simtalk-connector/<profile>/
  ├── connector.sock        # Unix socket，send/status/stop 通过它访问守护进程
  ├── connector.pid         # 当前 PID
  └── connector.log         # 守护进程日志（启动时写一行 "listening on ..."）
```

`status` 通过探测 socket 是否存在 + PID 文件判定运行状态；`stop` 先 SIGTERM、再等 2 秒、SIGKILL 兜底。

## 典型生命周期 / Lifecycle

```bash
# 1) 启动（后台）
python3 scripts/connector.py start --host 127.0.0.1 --port 9000 --daemon

# 2) 心跳确认
python3 scripts/connector.py send '{"type":"ping","action_id":"x"}'

# 3) 业务调用
python3 scripts/connector.py send '{"type":"simtalk_syntax","action_id":"y","simtalk":"print(1)"}'

# 4) 关闭
python3 scripts/connector.py stop
```

如果一个工作会话需要执行多次 SimTalk 调用，**不要每次都 start/stop**——保留守护进程直到会话结束。

## 调试技巧 / Debugging

- 看守护进程日志：`tail -f ~/.cache/simtalk-connector/default/connector.log`
- 看 PID 与 socket：`ls -la ~/.cache/simtalk-connector/default/`
- 手动验证服务端：`python3 -c "import socket;s=socket.socket();s.connect(('127.0.0.1',9000));..."`（仅用于检查网络可达性）
- 状态码反复出现 `2`/`connection closed`：服务端主动断开，检查 Plant Simulation 是否还在运行、端口是否被防火墙拦截。