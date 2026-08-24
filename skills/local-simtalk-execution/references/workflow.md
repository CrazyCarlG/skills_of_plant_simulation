# 端到端工作流 / End-to-End Workflow

本页给出一份完整的"写 SimTalk → 送到服务端 → 拿到真实结果"的剧本。把它当成 checklist：当用户提出"我要让这段 SimTalk 在 Plant Simulation 里跑一遍"时，按这套流程走。

> 本技能没有守护进程：每一步都是 `socket_client.py` 的一次独立调用。当前协议有 `ping`（连通性检查）、`simtalk_syntax`（仅语法检查）、`simtalk_run`（执行表达式）三种请求；后两者回包统一为 `action_result`，`ping` 回包为 `{"type":"ping","result":"success"}`（服务端在 `type` 字段回显请求类型）。
>
> **默认目标**（WSL2 容器 ↔ Plant Simulation 主机）：`host.docker.internal:50007`。`127.0.0.1` / `localhost` 在容器内会指向容器自身、连不上服务端（v1 T0 验证）。其它环境按实际部署改 host，端口固定 `50007`。
>
> ⚠️ **必须**用 `--resp-mode delimiter --resp-delimiter '||END||'` 读取回包——服务端不会主动关闭连接，`eof` 模式一定超时（v2 T4 验证）。

## 0. 准备阶段 / Prep

1. **确认服务端信息**——向用户索取：
   - 服务器 `host:port`（默认 `host.docker.internal:50007`，请确认）
   - 回复分帧模式：当前服务端**不会**主动关闭连接，必须用 `--resp-mode delimiter --resp-delimiter '||END||'`；其它模式（`eof` / `line` / `fixed`）实测下都不可靠
   - 发送侧在 `--data` 末尾追加 `||END||`；若将来服务端按行分帧再改 `--send-delimiter`

2. **首次握手**——先发一个最便宜的 `ping` 确认链路，再发 `simtalk_syntax` 验证语法链路：
   ```bash
   python3 skills/local-simtalk-execution/scripts/socket_client.py \
     --host host.docker.internal --port 50007 --timeout 5 \
     --data '{"type":"ping","timestamp":"20260824170056"}||END||' \
     --resp-mode delimiter --resp-delimiter '||END||'
   ```
   期望 `ping` 拿到 `{"type":"ping","result":"success"}`；随后用 `simtalk_syntax` 验证 `result` 不含 `"hasError"` 子串。

## 1. 提交 SimTalk / Submit

按目标选消息类型（完整字段见 `message-schema.md`）：

| 目标 | type | 备注 |
|---|---|---|
| 确认链路连通 | `ping` | 最轻量，仅测网络 |
| 只查语法，不真跑 | `simtalk_syntax` | 推荐作为首选；便宜、可重复 |
| 真跑一段代码 | `simtalk_run` | 会改变模型状态；可能触发模态对话框 |

> 每条消息都生成独立 `action_id`（如 `uuid4().hex`），方便与服务端日志对齐。

发送示例（`simtalk_syntax`）：

```bash
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host host.docker.internal --port 50007 --timeout 10 \
  --data '{"type":"simtalk_syntax","action_id":"s1","simtalk_code":"print(1)"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
```

## 2. 解析回包 / Parse Reply

按请求 `type` 分支判断成功（Quirk #6）：

- `simtalk_syntax`：`"hasError" not in result`（`result` 是诊断文本，例如 `"has no Error"`）
- `simtalk_run`：**双重检查**（Quirk #7）：
  ```text
  result == "success"  AND  not log.startswith("code execute failed")
  ```
  只看 `result == "success"` 会漏掉运行时异常（除零、未知标识符等也返回 `"success"`，错误细节走 `log`）。

**`data` 字段**：当前 `simtalk_run` 的 `data` **永远为空**（v6/v8/v9 多次验证）——服务端 `Run_Simutalk` 是 `-> void`，不会把表达式的值回填进来。**永远不要读 `data` 字段**。

**`retsult` 字段**：服务端缓存的历史诊断，与本次请求无关（v2-v10 多次复现）。**永远忽略 `retsult`**。

失败日志示例：
```
2026-08-06 14:25:46: print('hello from SimTalk') hasError ： Syntax error near line 1 at '''. (in row :1)
```

抽取关键信息：
- `Syntax error near line N at '<token>'`：行号 + 触发 token
- `(in row :N)`：备用行号（不同版本格式）
- `Unknown identifier '<name>'`：变量/方法名拼写错误
- `Type mismatch`：类型不匹配
- `code execute failed. error msg:...`：运行时异常（仅 `simtalk_run`）

> 提取出错的步骤：**仅修改 `simtalk_code` 字段**（`simtalk_syntax` / `simtalk_run` 共用），不要改 `action_id`，也不要改 `target_path` / `context_path` 等其它字段。

## 3. 迭代与重试 / Iterate

每次失败后：

1. 用最小修改的方式改代码（保留意图）。
2. 重新发 `simtalk_syntax` 验证编译通过。
3. 通过后再发 `simtalk_run` 实际执行。
4. 用回包 `log` 复核执行结果（不要等 `data`，它不会出现）。

**避免**：
- 一边改代码一边改其它字段（`target_path` / `context_path`），否则定位问题会变难。
- 同一份 payload 失败后立即反复重试——先看日志再决定。
- 把 `prompt(...)` / `infoBox(...)` / 写未声明的全局 attr 塞进 `simtalk_run`——这些会卡 GUI，**永远没回包**（Quirk #8 + `code-templates.md` 常见反模式 #6/#8）。

## 4. 错误重试策略 / Error Retry Policy

| 失败类型 | 是否重试 | 怎么做 |
|---|---|---|
| `result == "timeout"` | 视情况 | 先提高 `--timeout`；若是模态陷阱（`prompt` / 写未声明 attr）则 socket **永远不会回包**——停止重试，让用户去 GUI 取消对话框 |
| `result == "failed"` 编译错 | **不**重试同一 payload | 改代码 |
| `result == "success"` 但 `log.startswith("code execute failed")` | **不**重试同一 payload | 运行时异常，看 `log` 改代码 |
| 连接错（退出码 2） | 1 次 | 检查服务端后重发；WSL2 内用 `host.docker.internal` 而不是 `127.0.0.1` |
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
     --host host.docker.internal --port 50007 --timeout 10 \
     --data '{"type":"simtalk_syntax","action_id":"s1","simtalk_code":"print(\"hello from SimTalk\")\nroot.Throughput := .statThroughput"}||END||' \
     --resp-mode delimiter --resp-delimiter '||END||'
   ```
   → 失败，日志显示 `Unknown identifier 'root'`（`result` 含 `"hasError"`）。

2. 修正后再做语法检查：
   ```bash
   python3 skills/local-simtalk-execution/scripts/socket_client.py \
     --host host.docker.internal --port 50007 --timeout 10 \
     --data '{"type":"simtalk_syntax","action_id":"s2","simtalk_code":"print(\"hello from SimTalk\")\n.Throughput := .statThroughput"}||END||' \
     --resp-mode delimiter --resp-delimiter '||END||'
   ```
   → `result == "has no Error"`（不含 `"hasError"`）→ 语法 OK。

3. 用 `simtalk_run` 实际执行（注意：当前服务端**不会**回填 `data`，运行时异常也是 `result:"success"`）：
   ```bash
   python3 skills/local-simtalk-execution/scripts/socket_client.py \
     --host host.docker.internal --port 50007 --timeout 60 \
     --data '{"type":"simtalk_run","action_id":"r1","simtalk_code":"print(\"hello from SimTalk\")\nprint(.statThroughput)"}||END||' \
     --resp-mode delimiter --resp-delimiter '||END||'
   ```
   → `result == "success" AND log == "execute success"` → 执行成功。要拿 throughput 实际值，**去 Plant Simulation GUI 的 Console**（Window ribbon → Console）看 `print(.statThroughput)` 的输出，socket 端只能确认执行成功。

把每一步结果整理给用户。
