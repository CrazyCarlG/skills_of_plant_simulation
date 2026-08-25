# 端到端工作流 / End-to-End Workflow

本页给出一份完整的"写 SimTalk → 送到服务端 → 拿到真实结果"的剧本。把它当成 checklist：当用户提出"我要让这段 SimTalk 在 Plant Simulation 里跑一遍"时，按这套流程走。

> 本技能没有守护进程：每一步都是 `socket_client.py` 的一次独立调用。当前协议有 `ping`（连通性检查）、`simtalk_syntax`（仅语法检查）、`simtalk_run`（执行表达式）、`readlog`（拉取 GUI Console 输出 + 服务端日志起始标记）四种请求；后三者回包统一为 `action_result`，`ping` 回包为 `{"type":"ping","result":"success"}`（服务端在 `type` 字段回显请求类型）。
>
> ⚠️ **v15+ readlog 已回归**——v13 修复的"独立缓冲 + GUI Console 捕获"在当前服务端构建（2606.0002）下失效，`readlog` 回到 v12 的反馈循环模式，**不再可信**。详见 `references/lifelines.md` §5。
>
> **`simtalk_run` 的 `data` 字段始终为空**（Quirk #6 不变）——服务端 `Run_Simutalk` 是 `-> void`，不会把值序列化进 socket。详见 `references/lifelines.md` §6。
>
> **本工作流涉及的所有铁律**（连接目标、分帧方式、`type` 白名单、模态陷阱、成功判据等）集中在 `references/lifelines.md`，本文件不再重复展开。

## 0. 准备阶段 / Prep

1. **确认服务端信息**——所有连接相关铁律见 `references/lifelines.md` §1-2：
   - 服务器 `host:port`（WSL2 容器默认 `host.docker.internal:50007`，详见 `lifelines.md` §1）
   - 回复分帧必须用 `--resp-mode delimiter --resp-delimiter '||END||'`（详见 `lifelines.md` §2）
   - 发送侧在 `--data` 末尾追加 `||END||`

2. **首次握手**——先发一个最便宜的 `ping` 确认链路，再发 `simtalk_syntax` 验证语法链路：
   ```bash
   python3 skills/local-simtalk-execution/scripts/socket_client.py \
     --host host.docker.internal --port 50007 --timeout 5 \
     --data '{"type":"ping","timestamp":"20260824170056"}||END||' \
     --resp-mode delimiter --resp-delimiter '||END||'
   ```
   期望 `ping` 拿到 `{"type":"ping","result":"success"}`（`type` 回显请求类型）；随后用 `simtalk_syntax` 验证 `result` 不含 `"hasError"` 子串（详见 `lifelines.md` §6）。

## 1. 提交 SimTalk / Submit

按目标选消息类型（完整字段见 `message-schema.md`，`type` 字段取值受 `lifelines.md` §3 白名单约束）：

| 目标 | type | 备注 |
|---|---|---|
| 确认链路连通 | `ping` | 最轻量，仅测网络 |
| 只查语法，不真跑 | `simtalk_syntax` | 推荐作为首选；便宜、可重复 |
| 真跑一段代码 | `simtalk_run` | 会改变模型状态；可能触发模态对话框（详见 `lifelines.md` §4） |
| 拉取 GUI Console 输出 | `readlog` | ⚠️ v15+ 已回归 v12 反馈循环模式，不可信（详见 `lifelines.md` §5） |

> 每条消息都生成独立 `action_id`（如 `uuid4().hex`），方便与服务端日志对齐。

发送示例（`simtalk_syntax`）：

```bash
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host host.docker.internal --port 50007 --timeout 10 \
  --data '{"type":"simtalk_syntax","action_id":"s1","simtalk_code":"print(1)"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
```

## 2. 解析回包 / Parse Reply

按请求 `type` 分支判断成功（完整判据见 `references/lifelines.md` §6）：

- `simtalk_syntax`：`"hasError" not in result`（`result` 是诊断文本，例如 `"has no Error"`）
- `simtalk_run`：**双重检查**（Quirk #7）：
  ```text
  result == "success"  AND  not log.startswith("code execute failed")
  ```
  只看 `result == "success"` 会漏掉运行时异常（除零、未知标识符等也返回 `"success"`，错误细节走 `log`）。

**`data` 字段**：当前 `simtalk_run` 的 `data` **永远为空**（v6/v8/v9 多次验证）——服务端 `Run_Simutalk` 是 `-> void`，不会把表达式的值回填进来。**永远不要读 `data` 字段**（详见 `lifelines.md` §6）。

**`retsult` 字段**：服务端缓存的历史诊断，与本次请求无关（v2-v10 多次复现）。**永远忽略 `retsult`**（详见 `lifelines.md` §6）。

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
- 把 `prompt(...)` / `infoBox(...)` / 写未声明的全局 attr 塞进 `simtalk_run`——这些会卡 GUI，**永远没回包**（Quirk #8 + `lifelines.md` §4 + `code-templates.md` 常见反模式 #6/#8）。
- 把 `readlog` 当"完整历史"用——v15+ 已回归 v12 反馈循环模式（详见 `lifelines.md` §5），不可信。
- 在 `simtalk_run` 的 `data` 字段里期望拿到 print 实际值——`data` 永远为空（Quirk #6 不变），要拿 print 值请去 Plant Simulation GUI Console 肉眼读（v15+ readlog 不可信）。

## 4. 错误重试策略 / Error Retry Policy

| 失败类型 | 是否重试 | 怎么做 |
|---|---|---|
| `result == "timeout"` | 视情况 | 先提高 `--timeout`；若是模态陷阱（`prompt` / 写未声明 attr）则 socket **永远不会回包**——停止重试，让用户去 GUI 取消对话框（详见 `lifelines.md` §4） |
| `result == "failed"` 编译错 | **不**重试同一 payload | 改代码 |
| `result == "success"` 但 `log.startswith("code execute failed")` | **不**重试同一 payload | 运行时异常（Quirk #7 软失败），看 `log` 改代码 |
| 连接错（退出码 2） | 1 次 | 检查服务端后重发；WSL2 内用 `host.docker.internal` 而不是 `127.0.0.1`（详见 `lifelines.md` §1） |
| 连接中途断开（退出码 3） | 1 次 | 确认分帧方式后重发（详见 `lifelines.md` §2） |
| 想拿 GUI Console 的 `print(...)` 输出 | ⚠️ `readlog` v15+ 不可信 | 去 Plant Simulation GUI Console 肉眼读；或用 `scripts/simtalk_send.py`（若可用）——见 `lifelines.md` §5 |
| 把 `readlog` 当"完整历史"用 | ⚠️ 不推荐 | v15+ readlog 已回归 v12 反馈循环模式，体积会指数膨胀（详见 `lifelines.md` §5） |

## 5. 收尾 / Cleanup

无需清理——每次调用结束连接即关闭，不残留后台进程。

## 6. 操作通报约定 / Operation Notification Convention

> **v18 用户约定**：每次调用本技能时，**先用 `infoBox(text, false)` 在 Plant Simulation GUI 上向用户通报当前操作；调用结束后用 `infoBox("", false)` 关闭消息框。**
>
> 目的：让 GUI 用户能直观看到 Claude 当前正在做什么、何时调用结束。

### 6.1 通报打开 / Open Notification

在 §0 Prep 完成后、§1 Submit 之前，发一条 `simtalk_run` 调用非模态 `infoBox`：

```bash
python3 skills/local-simtalk-execution/scripts/simtalk_send.py \
  --timeout 30 \
  run 'infoBox("V<N> <短描述>", false)'
```

> ⚠️ **infoBox 文案要短**——GUI 消息框宽度有限，长文案会被截断显示不全。一句话即可（如 `"V19 测试中"`），不要罗列所有函数名。

> ⚠️ **必须用 `Modal:false`（非模态）**——模态版本（`true` 或省略）会让服务端永远阻塞等用户点 OK，socket 拿不到回包（详见 `lifelines.md` §4 模态陷阱）。

期望回包：
```json
{ "type": "", "action_id": "<uuid>", "result": "success", "log": "execute success" }
```

`result == "success"` ⇒ GUI 上已弹出非模态消息框。

### 6.2 通报关闭 / Close Notification

**在所有调用结束、§5 收尾之前**，发一条 `simtalk_run` 调用 `infoBox("", false)`：

```bash
python3 skills/local-simtalk-execution/scripts/simtalk_send.py \
  --timeout 30 \
  run 'infoBox("", false)'
```

期望回包：`result == "success"`。

> 该调用是**幂等**的——即使消息框已经关闭，再发空串也是 no-op，不会报错。建议在结束时**主动关闭一次**，不必担心"是否还在 GUI 上"。

### 6.3 防御性二次关闭 / Defensive Double-Close

若对是否残留消息框存疑，可在正式关闭后**再发一次** `infoBox("", false)`：

```bash
# 第一次关闭（必须）
python3 ... run 'infoBox("", false)'
# 防御性第二次关闭（可选，确认幂等）
python3 ... run 'infoBox("", false)'
# 收尾 ping（可选，确认服务端仍健在）
python3 ... ping
```

### 6.4 与现有步骤的集成 / Integration with Existing Steps

| 阶段 | 动作 |
|---|---|
| §0 Prep 之后 | 打开 infoBox（6.1） |
| §1-§5 各步 | 正常执行技能调用 |
| §5 Cleanup 之前 | 关闭 infoBox（6.2） |
| （可选） | 防御性二次关闭 + 收尾 ping（6.3） |

### 6.5 已知限制 / Known Limitations

| 限制 | 表现 | 替代 |
|---|---|---|
| 看不到 GUI | RDP 断开 / 最小化 / 无显示器时，msgBox 仍存在但用户不可见 | 服务端 socket 端只能验证"执行无异常"；建议在脚本最后加一次收尾 ping |
| 用户实际看到的是另一台机器 | WSL2 → Windows 主机的 GUI 渲染，主机用户能看到 msgBox | 通报对象是 GUI 用户而非对话用户——若需对话用户同步，改用文字回复 |
| 模态版本陷阱 | 误用 `infoBox(text, true)` 或省略 Modal 参数 | 必须显式写 `Modal:false`——本约定默认就是 `false` |
| 文案太长被截断 | GUI 消息框宽度有限，长文案会显示不全 | **一句话即可**（如 `"V19 测试中"`），不要罗列所有函数名——v19 用户反馈 |

### 6.6 与 v18 测试日志的关系 / Link to v18 Test Log

本约定由 v18 测试会话（`log/test-session-20260825-v18.md` §3）首次验证：
- `infoBox("V18 测试中", false)` → `result:"success"` / 退出码 0
- `infoBox("", false)` → `result:"success"` / 退出码 0
- 防御性二次关闭 → 仍 `result:"success"`（幂等）

任何后续版本如发现 `infoBox(non-empty, false)` 在 `simtalk_run` 上下文里回归为阻塞，请同步更新本节 + `lifelines.md` §4。

## 7. 完整示例 / Worked Example

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
