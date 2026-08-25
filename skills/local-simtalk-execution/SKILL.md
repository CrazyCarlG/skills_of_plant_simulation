---
name: local-simtalk-execution
description: 在本机通过 TCP 连接执行 Plant Simulation 的 SimTalk 代码——语法检查、方法调用、对象查询、模型运行等。当用户希望把 SimTalk 代码片段或方法体送入一台本地/局域网运行的 Plant Simulation 进程获得真实执行结果（编译器报错、返回值、对象属性、运行日志）时使用。触发场景包括：语法校验（"check this SimTalk syntax"）、运行方法（"execute this method on .M"）、查询对象（"what is the current value of this attribute"）、回放错误日志（"show me the compile errors"）。若用户只是请求编写、阅读或审查 SimTalk 代码而无需真实执行，本技能不适用。
---

# local-simtalk-execution

让 Claude 直接驱动一台正在运行的 Plant Simulation 进程：把 SimTalk 代码或方法调用打成 JSON 消息，通过 `scripts/socket_client.py` 一次性发送到本机/局域网 TCP 服务端，再把真实执行结果（编译错误、返回值、对象属性、运行日志）带回对话。

> 本技能专注于"执行"侧：每次调用都是一次独立的 TCP 连接（send → 收回复 → 关闭），不维护长连接、不做守护进程。

## 工作前提 / Prerequisites

- 一台本机或局域网可达的 Plant Simulation 进程，已暴露一个 TCP 端口用于接收 JSON 消息。
- 用户在首次使用时会提供：服务器 `host:port`、回复结束判定方式（服务端关闭连接 / 换行 / 自定义分隔符 / 定长）。
- `scripts/socket_client.py` 已可执行（`python3 skills/local-simtalk-execution/scripts/socket_client.py --help` 应能打印用法）。

## 任务流程 / Workflow

1. **确认连接信息**——向用户索取 `host:port` 与回复分帧方式；默认假设服务端每次回复后关闭连接（`eof` 模式）。

2. **构造消息**——根据用户目标挑选 schema（见 `references/message-schema.md`）：
   - 仅确认链路连通：`type: "ping"`
   - 仅做语法/编译检查：`type: "simtalk_syntax"`
   - 真正执行一段代码或读取状态：`type: "simtalk_run"`
   - 拉取 GUI Console 的 `print(...)` 输出（v13+）：`type: "readlog"`——socket 端**第一次**能拿到 `print(...)` 的实际值；readlog 使用独立缓冲，**可以**在轮询循环里调用，每次只返回"上次 readlog 之后"的增量

   完整的载荷模板见 `references/code-templates.md`。

3. **发送并等待回复**——用 `socket_client.py` 一次性发送；默认 10s 超时，长操作请用 `--timeout` 提高：
   ```bash
   python3 skills/local-simtalk-execution/scripts/socket_client.py \
     --host <host> --port <port> \
     --data '{"type":"simtalk_syntax","action_id":"<id>","simtalk_code":"<code>"}||END||' \
     --timeout 30
   ```
   退出码决定后续：0=成功、1=超时、2=无法连接、3=连接中途断开。

4. **解读结果**——`action_result` 消息含 `result` (`success`/`failed`/`timeout`) 与 `log` 字段：
   - `success`：直接读取返回的 `data` / `value` 字段。
   - `failed`：从 `log` 中抽取错误行（含行号），修改代码后再发新一轮请求。
   - `timeout`：先评估操作是否真的需要更长 `--timeout`，再决定是否重试。

5. **迭代**——重复步骤 2-4 直到 `result == "success"` 或用户主动终止。

## 关键文件 / Key Files

- `scripts/socket_client.py`：一次性 TCP 客户端，发送 `--data` 并按 `--resp-mode` 读取回复（`eof`/`line`/`fixed`/`delimiter`）。
- `references/socket_client.md`：socket_client.py 参数、回复分帧模式、退出码详解。
- `references/message-schema.md`：服务端/客户端所有 JSON 消息类型（`ping`、`simtalk_syntax`、`simtalk_run`、`readlog`、`action_result`）字段定义；`ping` 回包在 `type` 字段回显请求类型。
- `references/workflow.md`：完整端到端工作流，包括错误重试与故障排查。
- `references/code-templates.md`：常见载荷模板，可直接复制后填充。

## 故障排查 / Troubleshooting

| 现象 | 可能原因 | 处理 |
|---|---|---|
| `ERR: cannot connect to <host>:<port>` | 服务端未启动或端口不对 | 检查 Plant Simulation 进程与 `--host`/`--port` |
| `TIMEOUT: no reply within ...s` | 服务端卡住或操作过慢 | 提高 `--timeout`；检查服务端进程是否在跑 |
| `ERR: connection closed before reply` | 服务端提前断开 | 检查服务端日志；确认分帧方式与回复结束条件一致 |
| 拿不到完整回复 | 分帧模式不匹配 | 显式指定 `--resp-mode` 与 `--resp-delimiter` / `--resp-fixed` |
| `readlog` 看不到 `print(...)` 输出 | 旧 bug（Quirk #11）已修复；v13 起 readlog 直接拉回 GUI Console 输出 | 不适用（v13+ readlog 包含 GUI Console 输出）；如仍看不到，确认服务端是新版本 |
| `readlog` 体积爆炸 / 服务端 hang | 旧 bug（Quirk #12）已修复；v13 起 readlog 用独立缓冲+重置 | 不适用（v13+ 可以放心在循环里调用） |
| `readlog` 里只能看到部分历史 | v13+ 的预期行为——每次 readlog 返回"上次 readlog 之后"的增量，buffer 在回包后清空 | 不要把 readlog 当"完整历史"用；要拿全部历史就在同一轮里只调一次 |

## 知识库路径 / Knowledge Paths

本技能**不需要**直接读取知识库——它只负责把消息送出去并解析回包。SimTalk 语法/对象方法的权威说明请查阅 `01-plantsimulation-knowledge` 知识库。
