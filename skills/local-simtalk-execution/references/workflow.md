# 端到端工作流 / End-to-End Workflow

本页给出一份完整的"写 SimTalk → 送到服务端 → 拿到真实结果"的剧本。把它当成 checklist：当用户提出"我要让这段 SimTalk 在 Plant Simulation 里跑一遍"时，按这套流程走。

> 本技能没有守护进程：每一步都是 `socket_client.py` 的一次独立调用。当前协议有 `ping`（连通性检查）、`simtalk_syntax`（仅语法检查）、`simtalk_run`（执行表达式）三种请求；后两者回包统一为 `action_result`，`ping` 回包为 `{"type":"result","result":"success"}`。

## 0. 准备阶段 / Prep

1. **确认服务端信息**——向用户索取：
   - 服务器 `host:port`（默认 `127.0.0.1:9000`，请确认）
   - 回复分帧模式：以 `||END||` 分隔符结束回复时用 `--resp-mode delimiter --resp-delimiter '||END||'`；若服务端每次回复后关闭连接则用默认 `eof`；定长用 `--resp-mode fixed --resp-fixed <N>`
   - 发送侧在 `--data` 末尾追加 `||END||`；若服务端按行分帧则改用 `--send-delimiter $'\n'` 追加换行

2. **首次握手**——先发一个最便宜的 `ping` 确认链路，再发 `simtalk_syntax` 验证语法链路：
   ```bash
   python3 skills/local-simtalk-execution/scripts/socket_client.py \
     --host <host> --port <port> \
     --data '{"type":"ping","timestamp":"20260824170056"}||END||' \
     --resp-mode delimiter --resp-delimiter '||END||'
   ```
   期望 `ping` 拿到 `{"type":"result","result":"success"}`；随后用 `simtalk_syntax` 验证 `result == "success"`。

## 1. 提交 SimTalk / Submit

按目标选消息类型（完整字段见 `message-schema.md`）：

| 目标 | type | 备注 |
|---|---|---|
| 确认链路连通 | `ping` | 最轻量，仅测网络 |
| 只查语法，不真跑 | `simtalk_syntax` | 推荐作为首选；便宜、可重复 |
| 真跑一段代码 | `simtalk_run` | 会改变模型状态 |

> 每条消息都生成独立 `action_id`（如 `uuid4().hex`），方便与服务端日志对齐。

发送示例（`simtalk_syntax`）：

```bash
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host <host> --port <port> \
  --data '{"type":"simtalk_syntax","action_id":"s1","simtalk":"print(1)"}||END||'
```

## 2. 解析回包 / Parse Reply

成功 → 读 `data` 字段（`simtalk_run` 且 `return_value: true` 时才有）。失败日志示例：

```
2026-08-06 14:25:46: print('hello from SimTalk') hasError ： Syntax error near line 1 at '''. (in row :1)
```

抽取关键信息：
- `Syntax error near line N at '<token>'`：行号 + 触发 token
- `(in row :N)`：备用行号（不同版本格式）
- `Unknown identifier '<name>'`：变量/方法名拼写错误
- `Type mismatch`：类型不匹配

> 提取出错的步骤：**仅修改 `simtalk` / `expression` 字段**，不要改 `action_id`，也不要改 `target_path` / `context_path` 等其它字段。

## 3. 迭代与重试 / Iterate

每次失败后：

1. 用最小修改的方式改代码（保留意图）。
2. 重新发 `simtalk_syntax` 验证编译通过。
3. 通过后再发 `simtalk_run` 实际执行。
4. 用回包 `data` / `log` 复核执行结果。

**避免**：
- 一边改代码一边改其它字段（`target_path` / `context_path`），否则定位问题会变难。
- 同一份 payload 失败后立即反复重试——先看日志再决定。

## 4. 错误重试策略 / Error Retry Policy

| 失败类型 | 是否重试 | 怎么做 |
|---|---|---|
| `result == "timeout"` | 视情况 | 先提高 `--timeout`；若是服务端真卡住则停止重试，让用户介入 |
| `result == "failed"` 编译错 | **不**重试同一 payload | 改代码 |
| `result == "failed"` 运行时异常 | 视情况：可能是状态问题，先看回包 `log` 排查后重发 |
| 连接错（退出码 2） | 1 次 | 检查服务端后重发 |
| 连接中途断开（退出码 3） | 1 次 | 确认分帧方式后重发 |

## 5. 收尾 / Cleanup

无需清理——每次调用结束连接即关闭，不残留后台进程。

## 6. 完整示例 / Worked Example

**用户请求**："帮我跑这段 SimTalk 看看 throughput 是多少"

```simtalk
print("hello from SimTalk")
root.Throughput := .statThroughput
```

**Claude 流程**：

1. 先做语法检查：
   ```bash
   python3 skills/local-simtalk-execution/scripts/socket_client.py \
     --host 127.0.0.1 --port 9000 \
     --data '{"type":"simtalk_syntax","action_id":"s1","simtalk":"print(\"hello from SimTalk\")\nroot.Throughput := .statThroughput"}||END||'
   ```
   → 失败，日志显示 `Unknown identifier 'root'`。

2. 修正后再做语法检查：
   ```bash
   python3 skills/local-simtalk-execution/scripts/socket_client.py \
     --host 127.0.0.1 --port 9000 \
     --data '{"type":"simtalk_syntax","action_id":"s2","simtalk":"print(\"hello from SimTalk\")\n.Throughput := .statThroughput"}||END||'
   ```
   → `success`。

3. 用 `simtalk_run` 实际执行并取回 throughput：
   ```bash
   python3 skills/local-simtalk-execution/scripts/socket_client.py \
     --host 127.0.0.1 --port 9000 \
     --data '{"type":"simtalk_run","action_id":"r1","expression":"print(\"hello from SimTalk\")\n.statThroughput","return_value":true}||END||'
   ```
   → `success`，回包 `data` 为 throughput 数值。

把每一步结果整理给用户。
