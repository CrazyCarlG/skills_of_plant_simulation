# 端到端工作流 / End-to-End Workflow

本页给出一份完整的"写 SimTalk → 送到服务端 → 拿到真实结果"的剧本。把它当成 checklist：当用户提出"我要让这段 SimTalk 在 Plant Simulation 里跑一遍"时，按这套流程走。

## 0. 准备阶段 / Prep

1. **确认服务端信息**——向用户索取：
   - 服务器 `host:port`（默认 9000，请确认）
   - 响应分帧模式：默认 `line` + 分隔符 `||END||`；如果服务端用别的，请覆盖 `--resp-mode` / `--resp-delimiter`
   - 是否需要持久守护进程（多轮对话建议一直开着）

2. **确认守护进程状态**：
   ```bash
   python3 skills/local-simtalk-execution/scripts/connector.py status
   ```
   若未运行，启动：
   ```bash
   python3 skills/local-simtalk-execution/scripts/connector.py start \
     --host <host> --port <port> --daemon
   ```

3. **首次握手**——发一个 `ping` 确认链路：
   ```bash
   python3 scripts/connector.py send '{"type":"ping","action_id":"init"}'
   ```
   期望拿到 `result == "success"` 且 `data == "pong"`。

## 1. 提交 SimTalk / Submit

按目标选消息类型（完整字段见 `01-message-schema.md`）：

| 目标 | type | 备注 |
|---|---|---|
| 只查语法，不真跑 | `simtalk_syntax` | 推荐作为首选；便宜、可重复 |
| 真跑一段代码 | `simtalk_run` | 会改变模型状态 |
| 调一个具体方法 | `execute_method` | 比 `simtalk_run` 更结构化 |
| 读属性 | `query_object` | 不副作用 |
| 拉日志 | `pull_log` | 出错时排查用 |

> 每条消息都生成独立 `action_id`（如 `uuid4().hex`），方便与服务端日志对齐。

## 2. 解析回包 / Parse Reply

成功 → 读 `data` 字段。失败日志示例：

```
2026-08-06 14:25:46: print('hello from SimTalk') hasError ： Syntax error near line 1 at '''. (in row :1)
```

抽取关键信息：
- `Syntax error near line N at '<token>'`：行号 + 触发 token
- `(in row :N)`：备用行号（不同版本格式）
- `Unknown identifier '<name>'`：变量/方法名拼写错误
- `Type mismatch`：类型不匹配

> 提取出错的步骤：**仅修改 `simtalk` / `expression` 字段**，不要修改 `action_id`、不要重新组装整个 envelope 之外的字段。

## 3. 迭代与重试 / Iterate

每次失败后：

1. 用 `simtalk-programming` 风格的修复策略改代码（最小修改，保留意图）。
2. 重新发 `simtalk_syntax` 验证编译通过。
3. 通过后再发 `simtalk_run` / `execute_method` 实际执行。
4. 用 `query_object` / `pull_log` 复核副作用或日志。

**避免**：
- 一边改代码一边改其它字段（路径、参数），否则定位问题会变难。
- 同一份 payload 失败后立即反复重试——先看日志再决定。

## 4. 错误重试策略 / Error Retry Policy

| 失败类型 | 是否重试 | 怎么做 |
|---|---|---|
| `result == "timeout"` | 视情况 | 先提高 `--timeout`；若是服务端真卡住则停止重试，让用户介入 |
| `result == "failed"` 编译错 | **不**重试同一 payload | 改代码 |
| `result == "failed"` 运行时异常 | 视情况：可能是状态问题，可尝试 `pull_log` 排查后重发 |
| 连接错（退出码 2） | 1 次 | 让守护进程自动重连后再发 |
| 守护进程挂掉 | 重新 `start --daemon` 后再发 |

## 5. 长任务 / Long-running Operations

Plant Simulation 模型运行（仿真）通常很慢。一次 `simtalk_run` 可能跑几分钟甚至更长。

建议：

- 第一轮用 `simtalk_syntax` 验证脚本合法。
- 第二轮用 `simtalk_run` 触发仿真，`--timeout` 设大（300s+）。
- 中途想看进度？用 `pull_log` 拉最新日志。
- 避免并发：守护进程串行化请求，长任务期间其他 `send` 会被阻塞。

## 6. 收尾 / Cleanup

会话末尾：

```bash
python3 scripts/connector.py stop
```

如果用户希望保持连接（例如第二天继续），保留守护进程，仅 `stop` 当次 `send` 不再发生。

## 7. 完整示例 / Worked Example

**用户请求**："帮我跑这段 SimTalk 看看 throughput 是多少"

```simtalk
print("hello from SimTalk")
root.Throughput := .statThroughput
```

**Claude 流程**：

1. `status` → 未运行 → `start --daemon`。
2. `send '{"type":"ping","action_id":"a1"}'` → 收到 `success`。
3. 构造：
   ```json
   {"type":"simtalk_syntax","action_id":"s1","simtalk":"print(\"hello from SimTalk\")\nroot.Throughput := .statThroughput"}
   ```
   发出去 → 失败，日志显示 `Unknown identifier 'root'`。
4. 改用 `.Models.Model`：
   ```json
   {"type":"simtalk_syntax","action_id":"s2","simtalk":"..."}
   ```
   → `success`。
5. 改用 `simtalk_run`：
   ```json
   {"type":"simtalk_run","action_id":"r1","expression":"...","return_value":false}
   ```
   → `success`，`log` 末尾出现 `"hello from SimTalk"`。
6. `query_object` 读 throughput：
   ```json
   {"type":"query_object","action_id":"q1","object_path":".Models.Model","attributes":["statThroughput"]}
   ```
   → `data.statThroughput = 12.34`。

把每一步结果整理给用户。