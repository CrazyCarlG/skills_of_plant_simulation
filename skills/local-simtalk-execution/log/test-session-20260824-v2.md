# local-simtalk-execution Test Session v2 — 2026-08-24

本次针对 docs 修订后的回归：字段名从 `simtalk` / `expression` 统一改成 `simtalk_code`，并按真实服务器行为修正 ping 回包 `type` 字段。

## 1. 环境 / Environment

- **Skill under test**: `skills/local-simtalk-execution/`
- **Server**: Plant Simulation (host), listening on TCP port 50007
- **Client host**: WSL2 container（与 v1 相同）。从容器内用 `host.docker.internal:50007` 连接
- **Skill changes since v1**:
  - 所有 `simtalk_syntax` / `simtalk_run` 请求字段统一为 `simtalk_code`
  - `references/message-schema.md` 新增「Known Server Quirks」段
  - `SKILL.md` / `code-templates.md` / `workflow.md` / `socket_client.md` / `example/example.md` 全部同步

## 2. 用例与结果 / Test Cases & Results

### T1 — `ping` 连通性 ✅ PASS

```bash
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host host.docker.internal --port 50007 --timeout 5 \
  --data '{"type":"ping","timestamp":"v2-001"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
```

stdout（exit=0）：
```
{ "type": "ping", "result": "success" }||END||
```

观察：
- 服务器仍回显请求类型（`type:"ping"`），与 v1 一致、与修订后的文档一致 ✅
- 连接 + 回复 < 1s

---

### T2a — `simtalk_syntax` 合法代码 ✅ PASS（字段名修对了）

```bash
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host host.docker.internal --port 50007 --timeout 10 \
  --data '{"type":"simtalk_syntax","action_id":"v2-t2a-valid-bool","simtalk_code":"-> boolean"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
```

stdout（exit=0）：
```
{ "type": "action_result", "action_id": "v2-t2a-valid-bool", "retsult": "has no Error", "log": "2026-08-06 13:15:59: Log file opened! Application Version: 2606.0002, UTC: 2026-08-06 05:15:59\n2026-08-06 14:25:46: print('hello from SimTalk') hasError ： Syntax error near line 1 at '''. (in row :1)\n", "result": "success" }||END||
```

观察：
- ✅ 服务端**收到**了请求（v1 报 `simtalk_code was not found`，这次没报）
- ✅ 返回 `action_result`，`action_id` 正确回显
- ✅ `result: "success"`，符合合法 SimTalk
- ⚠️ **新发现 1：`retsult` 字段拼错了**（应该是 `result`）。这个带拼写错误的字段承载了人类可读的诊断（`"has no Error"` / `" hasError ： Syntax error near line 1 at ..."`），不是状态
- ⚠️ **新发现 2：`log` 字段看起来是静态/历史内容**，两次请求（T2a / T2b）拿到的是**完全一样**的 log 字符串，跟本次请求无关；不像本次执行的实时日志

---

### T2b — `simtalk_syntax` 非法代码 ✅ PASS

```bash
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host host.docker.internal --port 50007 --timeout 10 \
  --data '{"type":"simtalk_syntax","action_id":"v2-t2b-invalid-simtalk","simtalk_code":"this is not valid simtalk @#$"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
```

stdout（exit=0）：
```
{ "type": "action_result", "action_id": "v2-t2b-invalid-simtalk", "retsult": " hasError ： Syntax error near line 1 at 'is'. (in row :1)", "log": "2026-08-06 13:15:59: Log file opened! Application Version: 2606.0002, UTC: 2026-08-06 05:15:59\n2026-08-06 14:25:46: print('hello from SimTalk') hasError ： Syntax error near line 1 at '''. (in row :1)\n", "result": "failed" }||END||
```

观察：
- ✅ 收到 `action_result`，`action_id` 正确回显
- ✅ `result: "failed"`，符合预期
- ✅ 实际诊断在 `retsult` 字段：`Syntax error near line 1 at 'is'. (in row :1)` — 指向非法代码里第一个 token `is`
- ⚠️ `log` 字段与 T2a 一字不差，确认是静态/历史内容，**不是**本次执行的日志

---

### T3 — `simtalk_run` 执行表达式 ❌ TIMEOUT

```bash
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host host.docker.internal --port 50007 --timeout 10 \
  --data '{"type":"simtalk_run","action_id":"v2-t3-print1","simtalk_code":"print(1)"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
```

stderr（exit=1）：
```
TIMEOUT: no reply within 10.0s
```

观察：
- TCP 连接成功（无 `cannot connect` 错），`sendall` 也成功
- 但 10s 内没收到任何字节，与 v1 的 T2 表现完全一致
- 两种可能（需看服务端日志才能定）：
  1. `simtalk_run` 在这个 build 里根本没实现
  2. `simtalk_run` 走的是不同的代码路径，又踩到了"服务端吞错不发包"那个坑（`m_callback` 在某些分支崩了不写回包）
- 建议下次拿到服务器日志后重点排查 `SocketServer.m_callback` 是否对 `type=="simtalk_run"` 写了处理分支

---

### T4 — `ping` 用默认 `eof` 分帧 ❌ TIMEOUT

```bash
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host host.docker.internal --port 50007 --timeout 5 \
  --data '{"type":"ping","timestamp":"v2-eof-probe"}' 2>&1
```

stderr（exit=1）：
```
TIMEOUT: no reply within 5.0s
```

观察：
- 没加 `--resp-mode delimiter --resp-delimiter '||END||'` → 走默认的 `eof` 模式（等到对端关闭连接）
- 服务器**不会**关闭连接，连接会一直挂着直到超时
- 这是个**重大发现**：v1 测试日志和当前文档都假设 `eof` 模式对"短回复"也能工作（毕竟 `socket_client.md` 把 `eof` 列为默认），但实际**所有回复都必须用 `delimiter` 模式读 `||END||`**，否则一定超时
- 文档应当把 `eof` 从「可用模式」里降级，或在 `eof` 段落里加一句"本服务端不会主动关闭连接，必须用 delimiter"

---

## 3. 总结 / Summary

| # | Test | Verdict | 关键观察 |
|---|---|---|---|
| T1 | `ping` (delimiter) | ✅ PASS | echo `type:"ping"`，< 1s |
| T2a | `simtalk_syntax` 合法 | ✅ PASS | 字段名 `simtalk_code` 修对了，服务端真正处理 |
| T2b | `simtalk_syntax` 非法 | ✅ PASS | `result:"failed"` + 诊断信息（拼写错字段 `retsult`） |
| T3 | `simtalk_run` | ❌ TIMEOUT | 10s 无回复，需看服务端日志定位 |
| T4 | `ping` 用 `eof` 模式 | ❌ TIMEOUT | **服务端不关连接**，必须 `delimiter` |

## 4. 服务端实际形态 / Server Reality (from this session)

> 与 `references/message-schema.md` 当前文档相比的偏差汇总，**下次拿到服务端日志后建议核实**。

| 项 | 文档说 | 实际 | 严重程度 |
|---|---|---|---|
| `simtalk_syntax` 字段名 | （v1 错为 `simtalk`，v2 已改） `simtalk_code` | `simtalk_code` ✅ | 已修 |
| `simtalk_run` 字段名 | （v1 错为 `expression`，v2 已改） `simtalk_code` | （T3 没回包，无法判断） | 待定 |
| 诊断字段拼写 | 文档里没明确说，统一叫 `error` / `log` | 服务端拼成 **`retsult`**（注意拼错），承载人类可读诊断 | 需在文档注明 |
| `log` 字段语义 | 文档说"服务器原文日志，可换行" | 实际是**静态历史 dump**，跟本次请求无关；两次 simtalk_syntax 拿到一字不差 | 需修正文档，或排查服务端是否在 `log` 字段写错位置 |
| `result` 字段 | `success` / `failed` / `timeout` | ✅ `success` / `failed` 都已确认 | OK |
| 帧读取模式 | 默认 `eof` 也行 | **必须** `delimiter` + `||END||`；`eof` 一定超时 | 文档需降级 `eof` 或加红字警告 |

## 5. 待下次核对的开放问题 / Open Questions

1. `simtalk_run` 是不实现、还是又踩了"服务端吞错"坑？
2. `log` 字段为什么是静态内容？是文档笔误、还是服务端在 `m_callback` 里把别的日志塞到了这个 key？
3. `retsult` 拼错字段是 bug 还是历史包袱？要不要在文档里教消费者按"`result` 是 boolean 状态、`retsult` 是诊断"两路读？
4. 服务端是否会主动 `shutdown` / `close` socket？如果不会，需要在 `socket_client.md` 里把 `eof` 模式标为"本服务端不可用"