---
name: local-simtalk-execution
description: 在本机通过 TCP 连接执行 Plant Simulation 的 SimTalk 代码——语法检查、方法调用、对象查询、模型运行等。当用户希望把 SimTalk 代码片段或方法体送入一台本地/局域网运行的 Plant Simulation 进程获得真实执行结果（编译器报错、返回值、对象属性、运行日志）时使用。触发场景包括：语法校验（"check this SimTalk syntax"）、运行方法（"execute this method on .M"）、查询对象（"what is the current value of this attribute"）、回放错误日志（"show me the compile errors"）。若用户只是请求编写、阅读或审查 SimTalk 代码而无需真实执行，应改用 simtalk-programming。
---

# local-simtalk-execution

让 Claude 直接驱动一台正在运行的 Plant Simulation 进程：把 SimTalk 代码或方法调用打成 JSON 消息，通过 `scripts/connector.py` 维护的长连接送到本机/局域网 TCP 服务端，再把真实执行结果（编译错误、返回值、对象属性、运行日志）带回对话。

> 该技能专注于"执行"侧；编写/重构 SimTalk 代码请使用 `simtalk-programming`。两者组合：先编程，再让本技能验证。

## 工作前提 / Prerequisites

- 一台本机或局域网可达的 Plant Simulation 进程，已暴露一个 TCP 端口用于接收 JSON 消息（默认约定见下）。
- 用户在首次使用时会提供：服务器 `host:port`、所需的 `action_id` 来源（是否由服务端生成或客户端生成）、是否需要保持长连接。
- `scripts/connector.py` 已在仓库内可执行（`python3 skills/local-simtalk-execution/scripts/connector.py status` 应可运行）。

## 任务流程 / Workflow

1. **确认连接**——根据用户的服务器信息，按需启动 connector 守护进程：
   ```bash
   python3 skills/local-simtalk-execution/scripts/connector.py start \
     --host <host> --port <port> --daemon
   ```
   若用户已保持连接，跳过此步。

2. **构造消息**——根据用户目标挑选 schema（见 `references/message-schema.md`）：
   - 仅做语法/编译检查：`type: "simtalk_syntax"`
   - 真正执行一个方法或代码段：`type: "simtalk_run"` 或 `"execute_method"`
   - 查询对象属性：`type: "query_object"`
   - 拉取最近日志：`type: "pull_log"`

   完整的载荷模板见 `references/code-templates.md`。

3. **发送并等待回复**——通过 `send` 子命令阻塞发送；默认 10s 超时，长操作请用 `--timeout` 提高：
   ```bash
   python3 skills/local-simtalk-execution/scripts/connector.py send \
     '{"type":"simtalk_syntax","action_id":"<id>","simtalk":"<code>"}' \
     --timeout 30
   ```
   守护进程返回的状态码决定后续：0=成功、1=超时、2=错误。

4. **解读结果**——`action_result` 消息含 `result` (`success`/`failed`/`timeout`) 与 `log` 字段：
   - `success`：直接读取返回的 `data` / `value` 字段。
   - `failed`：从 `log` 中抽取错误行（含行号），回到 `simtalk-programming` 流程修改代码，再发新一轮请求。
   - `timeout`：先评估操作是否真的需要更长 `--timeout`，再决定是否重试。

5. **迭代**——重复步骤 2-4 直到 `result == "success"` 或用户主动终止。

6. **清理（可选）**——会话结束时可停止守护进程：
   ```bash
   python3 skills/local-simtalk-execution/scripts/connector.py stop
   ```

## 关键文件 / Key Files

- `scripts/connector.py`：TCP 长连接客户端守护进程（start/send/stop/status 四子命令），自动重连、阻塞一问一答。
- `references/connector.md`：connector 子命令、参数、响应分帧协议（`line`/`idle`/`fixed` 三种）详解。
- `references/message-schema.md`：服务端/客户端所有 JSON 消息类型（`simtalk_syntax`、`action_result`、`simtalk_run`、`query_object` …）字段定义。
- `references/workflow.md`：完整端到端工作流，包括错误重试与守护进程故障排查。
- `references/code-templates.md`：常见载荷模板，可直接复制后填充。

## 故障排查 / Troubleshooting

| 现象 | 可能原因 | 处理 |
|---|---|---|
| `cannot reach connector at ...` | 守护进程未启动 | 先 `start --daemon` |
| `TIMEOUT: no reply within timeout` | Plant Simulation 端卡住或操作过慢 | 提高 `--timeout`；检查服务端进程是否在跑 |
| `ERR: connection closed before reply` | 服务端断开 | 让守护进程自动重连，或手动 `stop && start` |
| 服务器消息以 `||END||` 结尾却拿不到完整回复 | 分帧模式不匹配 | 启动时显式 `--resp-mode line --resp-delimiter '||END||'` |

## 知识库路径 / Knowledge Paths

本技能**不需要**直接读取知识库——它只负责把消息送出去并解析回包。如需查看 SimTalk 语法/对象方法的权威说明，应切换到 `simtalk-programming` 或 `ps-object-reference`。