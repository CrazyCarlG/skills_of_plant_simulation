# socket_client.py 使用说明 / socket_client.py Reference

`scripts/socket_client.py` 是一个**一次性** TCP 客户端：每次调用都新建一条到 Plant Simulation 服务端的 TCP 连接，发送一份载荷，读完一次回复后立刻关闭。它**不**维护长连接、不做守护进程、也不自动重连——每发一条消息都是一次独立的 send → recv → close。

## 命令行 / Command Line

```text
socket_client.py --port <端口> --data <载荷> [--host <主机>] [其它选项]
```

| 选项 | 默认值 | 含义 |
|---|---|---|
| `--host` | `127.0.0.1` | Plant Simulation 服务端主机 |
| `--port` | (必填) | 服务端 TCP 端口 |
| `--data` | (必填) | 要发送的文本载荷（JSON 字符串） |
| `--timeout` | `10.0` | socket 超时（秒），连接与读取阶段共用 |
| `--encoding` | `utf-8` | 文本编码 |
| `--binary` | `False` | 把 `--data` 当作 Python 转义字节字面量解析 |
| `--send-delimiter` | (空) | 追加到发送载荷末尾的分隔符（如 `\n`） |
| `--resp-mode` | `eof` | 回复结束判定：`eof` / `line` / `fixed` / `delimiter` |
| `--resp-delimiter` | (空) | `line` / `delimiter` 模式的分隔字符串 |
| `--resp-fixed` | `0` | `fixed` 模式的精确回复字节数 |

## 退出码 / Exit Codes

| 退出码 | 输出 | 含义 |
|---|---|---|
| `0` | 回复内容写到 stdout | 成功 |
| `1` | `TIMEOUT: <msg>` 写到 stderr | 在 `--timeout` 内未收到（足够的）回复 |
| `2` | `ERR: cannot connect to ...` 或参数错误 | 无法建立连接 / 用法错误 |
| `3` | `ERR: connection closed before reply -> <e>` | 收到回复前连接被提前关闭或 socket 错误 |

> **重要**：成功时 stdout 是**原始回复字节**。Claude 解析时应假设它是 UTF-8 JSON；若服务端偶发返回非 JSON（例如二进制日志），需要相应 fallback。退出码才是判定成功/失败的可靠依据，不是 stdout 内容。

## 回复分帧 / Response Framing

Plant Simulation 服务端的输出长度不定，`--resp-mode` 决定"一条完整回复到哪里为止"，必须与服务端约定一致：

1. **`eof`**（默认）——读到服务端关闭连接（FIN）为止。适合每次回复后服务端主动断开的场景。
2. **`line`** ——读到 `--resp-delimiter` 为止（分隔符本身被丢弃）。适合服务端保持连接、以换行等分隔符结束一条回复的场景。
3. **`delimiter`** ——与 `line` 行为相同，读到 `--resp-delimiter` 为止，语义上更强调"自定义分隔符"。
4. **`fixed`** ——严格读 `--resp-fixed` 字节。适合二进制 / 定长协议。

> 用 `line` / `delimiter` 时**必须**给 `--resp-delimiter`，用 `fixed` 时**必须**给 `--resp-fixed > 0`，否则脚本会直接报参数错误退出（退出码 2）。

## 发送分隔符 / Sending Delimiter

脚本**不会**自动在载荷末尾追加换行。若服务端按行分帧、要求每条请求以 `\n` 结束，请用 `--send-delimiter` 显式追加：

```bash
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --port 9000 \
  --data '{"type":"simtalk_syntax","action_id":"x","simtalk":"->boolean"}' \
  --send-delimiter $'\n' \
  --resp-mode line --resp-delimiter $'\n'
```

## 典型用法 / Usage

```bash
# 服务端每次回复后关闭连接（默认 eof）
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host 127.0.0.1 --port 9000 \
  --data '{"type":"simtalk_syntax","action_id":"x","simtalk":"->boolean"}'

# 执行表达式（自定义分隔符 ||END||）
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host 127.0.0.1 --port 9000 \
  --data '{"type":"simtalk_run","action_id":"y","expression":"print(1)"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
```

由于每次都是新连接，一个工作会话里的多次调用之间没有共享状态——每次都要重新传 `--host` / `--port` / 分帧参数。

## 调试技巧 / Debugging

- 先看脚本自身用法：`python3 skills/local-simtalk-execution/scripts/socket_client.py --help`
- 手动验证服务端可达性：`python3 -c "import socket;s=socket.socket();s.settimeout(3);s.connect(('127.0.0.1',9000))"`
- 反复出现 `2`/`cannot connect`：服务端未监听或端口被防火墙拦截，检查 Plant Simulation 是否还在运行。
- 反复出现 `1`/`TIMEOUT`：分帧方式不匹配或服务端卡住，先用 `eof` 或 `line` 配正确分隔符确认能拿到完整回包。
