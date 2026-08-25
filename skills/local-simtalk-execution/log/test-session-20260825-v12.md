# local-simtalk-execution Test Session v12 — 2026-08-25

> **⚠️ v12 记录的 readlog bug 在 v13 已修复——见 `test-session-20260825-v13.md`**：
> - ~~Quirk #11: readlog 不返回 GUI Console 输出~~ → v13 修复
> - ~~Quirk #12: readlog 反馈循环 / 体积膨胀~~ → v13 修复
>
> 本日志保留为 v12 历史快照（首次发现 bug 的过程）。所有技能文档已基于 v13 结果更新。

测试目标：用户在服务端**新增了一个 `readlog` 消息体类别**，意图让客户端通过 `{"type":"readlog","action_id":"..."}` 拉回 **Plant Simulation GUI Console** 的 `print(...)` 输出。本次会话验证 `readlog` 实际行为是否符合用户意图，并测试该消息的副作用。

## 1. 用户意图 / User Intent

> "我在服务端增加了一个消息体类别,客户端可以发送 `{"type":"readlog","action_id": "644c86747baa465b8e67b7457a4529f4"}` 返回 GUI Console 打印的日志，请修改这个技能，测试一下"

按字面理解：`readlog` 应当把 Plant Simulation GUI Console（Window ribbon → Console 面板）里 `print(...)` 写进去的内容作为日志返回。

## 2. 环境 / Environment

- **Skill under test**: `skills/local-simtalk-execution/`
- **Server**: Plant Simulation（宿主机），TCP **50007**
- **Client host**: WSL2 容器 → `host.docker.internal:50007`
- **回包读取**：统一 `--resp-mode delimiter --resp-delimiter '||END||'`（v2 T4 验证必须）
- **辅助客户端**：`/root/skills_of_plant_simulation/skills/local-simtalk-execution/scripts/socket_client.py`

---

## 3. 握手 / Handshake

服务端在用户添加 `readlog` 后已重启过一次。先 `ping` 确认链路恢复：

| ID | 类型 | 命令 | 回包 | 结论 |
|---|---|---|---|---|
| P1 | `ping` | `--data '{"type":"ping","timestamp":"20260825081200"}' \|\|END\|\|` | `{"type":"ping","result":"success"}` | ✅ 链路通 |

---

## 4. 第一次 readlog（无前置操作） / T1

直接发一个 readlog，看回包形状：

**请求**：
```json
{"type":"readlog","action_id":"readlog-t1"}
```

**回包关键字段**：
- `result`: `"success"`
- `log`: 形如 `"2026-08-25 08:12:NN: Log file opened! Application Version: 2606.0002, UTC: ...\n2026-08-25 08:12:NN: Copilot -->> Local: ping\n2026-08-25 08:12:NN: Local -->> Copilot: { \"type\": \"ping\", \"result\": \"success\" }||END||\n2026-08-25 08:12:NN: { \"type\": \"ping\", \"result\": \"success\" }||END|| Sent successfully\n..."`

**观察**：
- ✅ 回包格式是标准 `action_result`
- ⚠️ `log` 内容是**服务端 socket wrapper 自己的应用日志**——socket I/O trace（`Copilot -->> Local: ...` / `Local -->> Copilot: ...`）、`Log file opened! Application Version: ...`、`Sent successfully` 收发确认
- ❌ **没看到任何 Plant Simulation GUI Console 的 `print(...)` 输出**

**初步结论**：readlog 返回的不是 GUI Console 的 print 输出。需做对照实验确认。

---

## 5. 对照实验：先 print 唯一标记，再 readlog / T2

### 5.1 在 GUI 里 print 唯一标记字符串

通过 `simtalk_run` 让 Plant Simulation 执行一条 `print` 表达式，**绝对不可能与 readlog 输出巧合相同**的字符串：

```simtalk
print("MARKER_XYZZY_42_UNIQUE_TO_CONSOLE")
```

请求：`{"type":"simtalk_run","action_id":"print-marker-1","simtalk_code":"print(\"MARKER_XYZZY_42_UNIQUE_TO_CONSOLE\")"}`

回包：
- `result`: `"success"`
- `log`: `"execute success"`

> **注意**：socket 端**永远拿不到** `print` 的实际值（v6/v8/v9/v11 已验证 Quirk #6：`data` 字段始终为空；print 的输出只能在 Plant Simulation GUI 的 Console 面板看）。

### 5.2 立即 readlog

```json
{"type":"readlog","action_id":"readlog-t2"}
```

**预期（按用户意图）**：`log` 里能看到 `MARKER_XYZZY_42_UNIQUE_TO_CONSOLE`。

**实际**：`log` 里出现的全是 socket I/O trace 和 `Sent successfully` 之类的服务端日志行，**完全没有** `MARKER_XYZZY_42_UNIQUE_TO_CONSOLE`。

**结论**：
- ❌ `readlog` **不是** GUI Console 取值通道
- ❌ 它返回的是**服务端 socket wrapper 自己的应用日志**
- 用户的"readlog 返回 GUI Console 打印的日志"这个**意图没有被实现**——服务端要么没把 GUI Console 输出转发到 socket wrapper 的日志源，要么 readlog 拉的是别的日志文件

### 5.3 第二次对照：再 print 一个不同标记

再 print 一次：

```simtalk
print("FOOBAR_QUUX_9999_ANOTHER_MARKER")
```

立即 readlog：`log` 里仍然只有 socket I/O 痕迹 + 上一次 readlog 的响应，**两个标记都不在**。

> 这两个 8~10 位的随机字符串 + 多个下划线 + 大写 + 数字，**不可能是巧合**——readlog 拿不到任何 GUI Console 输出。

---

## 6. 反馈循环 bug / T3

T2 的过程中观察到一个**严重问题**：每次 readlog 的响应本身被服务端写进了它自己的应用日志。下一次 readlog 把这条响应（已经 JSON 转义过）原样塞进新响应的 `log` 字段，循环递归。

### 6.1 现象：log 字段长度指数级增长

观察 readlog 连续调用 3 次的 `log` 字段长度：

| 调用次数 | `log` 字段大致行数 | 大致字节数 |
|---|---|---|
| readlog #1 | 10 行 | ~1.5 KB |
| readlog #2 | 11 行（包含 #1 的整条响应） | ~3 KB |
| readlog #3 | 12 行（包含 #2 的整条响应——双重转义） | ~6 KB |

每多调一次 readlog，体积大致翻倍（JSON 转义深度 +1）。

### 6.2 后果

- 超过 socket 缓冲区 → 客户端读取失败 / 服务端 hang
- 服务端日志文件无限膨胀（每条 readlog 都把上次 readlog 整条响应写进去）
- **本次会话第一次连续 probe 时确实观察到服务端 hang / 重启**——readlog #5 后 `ping` 不通，过了 10+ 秒才恢复（猜测是服务端进程被自动拉起 / 日志被截断）

### 6.3 根因

服务端 wrapper 把每次发出去的消息（包括 readlog 自己的响应）写进应用日志：

```
2026-08-25 08:12:NN: Local -->> Copilot: {"type":"readlog","action_id":"readlog-t1","log":"<上一次的 readlog 响应体>"}
```

这条日志本身又会被下次 readlog 拉回来：

```
readlog #2 → log: "...上面那条日志 + 上上次 readlog 响应的 JSON 转义版 + ..."
```

转义深度 +1，体积 ×2。

### 6.4 规避（已知） / Quirk #12

- **不要**在自动化循环里反复调 readlog
- **不要**把 readlog 写进任何监控 / 测试 / 重试脚本
- 现阶段 readlog **仅供人工调试**：一次性看一次近期通讯状态
- `simtalk_syntax` / `simtalk_run` 的诊断（`log` 字段）在当次 `action_result.log` 里就回来了——**不必**用 readlog 去看它们
- **服务端侧建议**：要么 readlog 不再写自己的响应进日志源，要么维护一个"上次 readlog 拉到哪里了"的游标，避免把响应再塞回去

---

## 7. readlog 字段语义（与既有消息对比） / Schema Notes

| 字段 | 必填 | 说明 |
|---|---|---|
| `type` | 是 | 固定 `"readlog"` |
| `action_id` | 是 | 客户端生成的 UUID/字符串 |
| `result` | 是 | 标准字面量 `"success"` / `"failed"` / `"timeout"` |
| `log` | 否 | 服务端应用日志内容（**不是** GUI Console print 输出） |
| `data` | — | 不出现（与 `simtalk_run` 同样：服务端 `Run_...`/日志接口是 void，不序列化数据进 socket） |
| `retsult` | — | 仍可能带陈年缓存，**忽略** |

与 `simtalk_syntax` 的 `result` 字段语义差异不同（Quirk #6），`readlog` 的 `result` 字段是**字面量**，**不**含 `"hasError"` 之类的诊断文本——成功判据直接 `result == "success"`。

---

## 8. 结论 / Summary

### 8.1 用户的意图未被满足

| 用户期望 | 实测结果 |
|---|---|
| readlog 返回 **GUI Console** 的 `print(...)` 输出 | ❌ 返回**服务端 socket wrapper 自己的应用日志**（I/O trace + Log file opened + Sent successfully） |
| 验证：print 唯一标记字符串 `MARKER_XYZZY_42_UNIQUE_TO_CONSOLE` 后 readlog 看不到该标记 | ❌ 两个独立标记（`MARKER_XYZZY_42_UNIQUE_TO_CONSOLE` 和 `FOOBAR_QUUX_9999_ANOTHER_MARKER`）都不在 readlog 输出里 |

**服务端**需要补齐：把 Plant Simulation GUI Console 的 `print(...)` 输出写到 socket wrapper 的日志源里（或单独走另一条 socket 通道），readlog 才能拿到 GUI Console 内容。

### 8.2 readlog 还有一个**严重的反馈循环 bug**（Quirk #12）

服务端把每次发出的 readlog 响应写进自己的应用日志，下次 readlog 再把这条历史响应塞进 `log` 字段，**回包体积指数级膨胀**——几次调用就能撑爆 socket 缓冲区、让服务端 hang。

**禁止**在自动化循环里反复调 readlog。

### 8.3 现阶段 readlog 唯一安全的用法

人工调试时一次性发一个 readlog，看看最近 socket 通讯状态。**看完即弃**。

---

## 9. 给服务端维护者的修复建议 / Server-side Fix Hints

1. **readlog 不返回 GUI Console 输出**
   - **方案 A（推荐）**：在 socket wrapper 里订阅 Plant Simulation 的 GUI Console 事件，把 `print(...)` 文本追加进 wrapper 的应用日志源；下次 readlog 自然会拉回来
   - **方案 B**：给 readlog 加一个新字段（比如 `"source":"gui_console"`），wrapper 单独维护一份 GUI Console 输出缓冲；readlog 默认返回 socket wrapper 日志，加这个字段时返回 GUI Console 缓冲

2. **反馈循环 bug**
   - **方案 A（最小改动）**：readlog 响应写日志时，把 `log` 字段里的内容**先 redact** 再写——把 readlog 的响应整体替换成 `<readlog response redacted, length=N bytes>`
   - **方案 B**：readlog 内部维护一个"已拉过的最大日志偏移"游标，只返回新内容
   - **方案 C（治本）**：把"已发送消息"日志和"应用事件"日志分开存储，readlog 只读后者

3. **回归测试**：补一个 `simtalk_run print("MARKER_GUI_CONSOLE_XYZ")` → `readlog` 的端到端断言，确保 MARKER 出现在 readlog 输出里。当前 v12 实测：MARKER **不出现**。

---

## 10. 技能侧变更清单 / Skill-side Changes

本轮 readlog 测试带出的技能侧文档变更：

1. `references/message-schema.md`
   - 消息类型表新增 `readlog` 一行
   - 新增完整 `readlog` section（请求/响应字段、回包示例、与 GUI Console 区分说明）
   - 已知 Quirks 列表新增 **Quirk #11**（readlog 不返回 GUI Console 输出）和 **Quirk #12**（readlog 反馈循环 bug）
2. `references/code-templates.md`
   - 顶部协议消息清单新增 `readlog`
   - 新增 **模板 C：readlog**，明确"人工调试专用，禁止自动化循环"
   - Cheatsheet `type` 行新增 `readlog`
   - 常见反模式新增 #9（readlog 写循环）和 #10（期望从 readlog 拿 print 输出）
3. `SKILL.md`
   - 工作流 step 2 新增 `readlog` 选项 + Quirk 提示
   - `references/message-schema.md` 一句话简介的 `type` 列表里加入 `readlog`
   - 故障排查表新增两行（反馈循环 bug、找不到 print 输出）
4. `references/workflow.md`
   - 顶部协议清单 + 消息类型表新增 `readlog`
   - "避免"清单新增两条（readlog 写循环、readlog 当 print 取值通道）
   - 错误重试策略表新增"想拿 GUI Console 输出不要用 readlog"

---

## 11. 待用户确认 / Awaiting User Confirmation

- **需用户决定**：readlog 是否要走"返回 GUI Console 输出"这条路？
  - 如果**是**：服务端需要补 Console 输出 → 日志源的通道（参见 §9 修复建议 1）
  - 如果**否**：技能文档目前的 Quirk #11 警告保留，提醒"别把 readlog 当 Console 取值通道用"
- **反馈循环 bug（Quirk #12）**：建议服务端优先修复（参见 §9 修复建议 2），否则任何高频 readlog 调用都会让服务端 hang
