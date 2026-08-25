# local-simtalk-execution Test Session v16 — 2026-08-25

测试目标：服务端新增"异常抛出"后，通过 `local-simtalk-execution` 技能验证**传输不符合要求的 JSON 时，服务端是否能正确抛出 / 上报异常**——分三类场景：
1. **JSON 解析失败**（不是合法 JSON）
2. **Schema 违规**（合法 JSON 但字段缺失 / 类型错 / 未知 type）
3. **SimTalk 代码层异常**（合法请求 + 合法字段 + 非法 SimTalk，验证运行时异常是否被服务端捕获并通过 `log` 回传）

## 1. 环境 / Environment

- **Skill under test**：`skills/local-simtalk-execution/`
- **Server**：Plant Simulation（宿主机），TCP **50007**
- **Client host**：WSL2 容器 → `host.docker.internal:50007`
- **回包读取**：统一 `--resp-mode delimiter --resp-delimiter '||END||'`
- **辅助客户端**：`skills/local-simtalk-execution/scripts/socket_client.py`
- **测试时间**：2026-08-25（接续 v15）

## 2. 握手 / Handshake

| ID | 命令 | 回包 | 退出码 | 结论 |
|---|---|---|---|---|
| v16-ping | `{"type":"ping","timestamp":"v16-init"}` | `{"type":"ping","result":"success"}` | 0 | ✅ 链路通 |

## 3. JSON 解析失败 / JSON Parse Failures

> 观察：服务端在 JSON 解析失败时**不走 `action_result` 信封**，直接以错误字符串 + `||END||` 返回——属于"低层级协议错误"分类。

| ID | 载荷（去帧） | 回包原文 | 退出码 | 异常类别 | 结论 |
|---|---|---|---|---|---|
| v16-bad-01 | `this is not json at all garbage` | `Error in JSON data: Syntax error near line 1 at 'this is not'.` | 0 | `JsonReaderException`（指针位置 `'this is not'`） | ✅ 抛出 |
| v16-bad-02 | `{not json, missing quotes: x}` | `Error in JSON data: Syntax error near line 1 at 'not json, missing'.` | 0 | 同上（指针位置 `'not json, missing'`） | ✅ 抛出 |
| v16-bad-03 | `{"type":"simtalk_run"`（截断） | `Error in JSON data: Error in line 1: Unexpected end of string` | 0 | "Unexpected end of string" | ✅ 抛出 |
| v16-bad-04 | `[1,2,3]`（数组而非对象） | `An item with the identifier 'type' was not found.` | 0 | 服务端尝试按对象 schema 取 `type`，得到 array，报字段缺失（**不是 JSON 解析错**——`[1,2,3]` 是合法 JSON） | ⚠️ 错误类目偏离（应是"非法 schema"而非"JSON 错"） |
| v16-bad-11 | `\|\|END\|\|`（帧前空载荷） | `Error in JSON data: Error in line 1: Unexpected end of string` | 0 | 同 bad-03 | ✅ 抛出 |

**小结**：JSON 层错误 100% 可拿到清晰异常文本，且**不会让连接挂死**——`||END||` 帧格式保留完整。

## 4. Schema 违规 / Schema Violations

| ID | 载荷（去帧） | 回包 | 退出码 | 异常类别 | 结论 |
|---|---|---|---|---|---|
| v16-bad-05 | `{"action_id":"v16-bad-05"}`（缺 `type`） | `An item with the identifier 'type' was not found.` | 0 | `IdentifierNotFoundException` | ✅ 抛出 |
| v16-bad-06 | `{"type":123,...}`（type 为整数） | `Illegal data type: 'string' or compatible type expected.` | 0 | `IllegalDataTypeException` | ✅ 抛出 |
| v16-bad-07 | `{"type":"totally_made_up_type",...}`（未知 type） | **（无回包，5s 超时）** | **1 (TIMEOUT)** | —— | ❌ **服务端挂死**——异常分支不写回包，复现 v9 Quirk #3 |
| v16-bad-08 | `{"type":"simtalk_run",...}`（simtalk_run 无 `simtalk_code`） | `{ "type":"action_result","action_id":"v16-bad-08","result":"success","log":"There is no calling method in which the thrown runtime error can be raised." }` | 0 | **走 action_result 信封 + Quirk #7 软失败**：result="success" + log 描述"无可抛出的调用上下文" | ✅ 异常被服务端捕获并通过 `log` 字段回传 |
| v16-bad-09 | `{}`（空对象） | `An item with the identifier 'type' was not found.` | 0 | 同 bad-05 | ✅ 抛出 |
| v16-bad-10 | `null` | `An item with the identifier 'type' was not found.` | 0 | 同 bad-05（服务端把 `null` 当成空对象处理） | ✅ 抛出 |
| v16-bad-12 | `{"type":"simtalk_run","simtalk_code":12345}`（code 为整数） | `{ "type":"","action_id":"v16-bad-12","result":"","log":"Incompatible types of argument 1: expecting string, passed integer." }` | 0 | 字段类型校验在请求处理路径中触发 | ✅ 抛出（但 `type`/`result` 字段为空字符串——细节，见 §6） |

**小结**：除 bad-07 未知 type 外，所有 schema 违规都能拿到具体异常。但**有 3 处需要关注**：

1. **bad-07 复现 Quirk #3**——未知 type 让服务端完全静默挂死，必须靠 timeout 兜底。
2. **bad-04 错误归类偏移**——`[1,2,3]` 是合法 JSON，服务端却用"字段缺失"敷衍；应明确区分"非法 JSON"和"非法 schema"。
3. **bad-08 异常能被正确抛出并通过 `log` 字段透传**——这正是用户"异常抛出"在 `simtalk_run` 路径下的预期行为（与团队记忆 `simtalk-run-soft-failure-design` 完全一致）。

## 5. SimTalk 代码层异常 / SimTalk Code-Level Exceptions

> 验证合法请求 + 非法 SimTalk 时，服务端**是否捕获运行时异常**并通过 `log` 字段回传。

| ID | `simtalk_code` | `result` | `log` | 退出码 | 异常类别 | 结论 |
|---|---|---|---|---|---|---|
| v16-bad-13 | `throw`（未知关键字） | `success` | `code execute failed. error msg:Unknown identifier 'throw', in code 'throw'` | 0 | 运行时"未声明标识符"异常 | ✅ **Quirk #7 软失败命中**——result="success" + log 前缀 `"code execute failed"` 双重判据生效 |
| v16-bad-14 | `var x:integer := 1/0; print x`（常量除零） | `failed` | ` hasError ： Error in line 1: Division by zero. (in row :1)` | 0 | **编译期**常量折叠抛错 | ✅ 编译错误正常返回 |
| v16-bad-15 | `raise`（未知关键字） | `success` | `code execute failed. error msg:Unknown identifier 'raise', in code 'raise'` | 0 | 运行时"未声明标识符"异常 | ✅ 同 bad-13 |
| v16-throw-01 | `var i:integer; i := 1; print i/0`（运行时除零） | `failed` | ` hasError ： Error in line 1: Division by zero. (in row :1)` | 0 | **编译期**抛错（Plant Simulation 把 `i/0` 当常量折叠） | ✅ 编译错误正常返回（与 v15-sx-18 行为一致） |
| v16-throw-02 | `print nonExistentSymbol`（未知标识符） | `success` | `code execute failed. error msg:Unknown identifier 'nonExistentSymbol', in code 'print nonExistentSymbol'` | 0 | 运行时异常 | ✅ Quirk #7 软失败命中 |

**小结**：
- 运行时异常（未知标识符）：服务端**主动抛出** Plant Simulation 异常 → **捕获** → 写入 `log` 字段 → **仍返回 `result:"success"`**（软失败设计，按用户预期）
- 编译期错误：服务端**主动抛出**编译错 → 写入 `log` 字段 → **`result:"failed"`**（硬失败）

两种异常都被服务端正确捕获并回传，**没有让连接挂死**。

## 6. 服务器稳定性 / Server Stability After Exception Storm

> 跑完 §3-§5 共 16 次坏请求后，验证服务端进程是否仍然健在。

| ID | 命令 | 回包 | 退出码 | 结论 |
|---|---|---|---|---|
| v16-stab-ping-1 | ping | `{"type":"ping","result":"success"}` | 0 | ✅ 服务端进程健在 |
| v16-stable-01 | `simtalk_run` `print 1+2` | `result="success"` / `log="execute success"` | 0 | ✅ 合法请求正常执行 |
| v16-stab-ping-2 | ping | `{"type":"ping","result":"success"}` | 0 | ✅ 仍健在 |

**小结**：服务端在 16 次坏 JSON + 异常风暴后仍能正常处理新连接与合法请求，**唯一失败模式**是 bad-07 未知 type 导致的 socket 静默挂死（Quirk #3 行为）。

## 7. 异常抛出行为总览 / Exception Behavior Matrix

| 异常类别 | 触发方式 | 回包信封 | `result` 字段 | `log` 字段 | 是否会让 socket 挂死 |
|---|---|---|---|---|---|
| JSON 解析错（语法错 / 截断 / 空） | bad-01/02/03/11 | **裸字符串**（非 action_result） | —— | 错误描述以纯文本直接返回 | ❌ 不挂死 |
| Schema 字段缺失 | bad-05/09/10/04 | 裸字符串 | —— | "An item with the identifier 'X' was not found." | ❌ 不挂死 |
| Schema 字段类型错 | bad-06/12 | 裸字符串 / 部分 action_result | 字符串或空 | 错误描述 | ❌ 不挂死 |
| **未知 type 值** | bad-07 | **不回包** | —— | —— | ✅ **会挂死到 timeout** |
| SimTalk 编译错误 | bad-14 / throw-01 | action_result | `failed` | ` hasError ： ...` | ❌ 不挂死 |
| **SimTalk 运行时异常**（用户实际场景） | bad-08/13/15 / throw-02 | action_result | `success` | `code execute failed. error msg:...` 或 `There is no calling method in which the thrown runtime error can be raised.` | ❌ 不挂死 |

## 8. 结论 / Conclusions

1. **JSON 解析失败的异常抛出 ✅ 可行**——所有 JSON 语法错、截断、空载荷都能拿到清晰的错误文本，连接不挂死。
2. **Schema 字段异常的抛出 ✅ 可行**——缺失必填字段、字段类型错都能抛出明确错误，连接不挂死。
3. **SimTalk 代码层异常的抛出 ✅ 可行**——编译错走 `result:"failed"`，运行时异常走 Quirk #7 软失败（`result:"success"` + `log` 含 `"code execute failed"`），两条路径**都不挂死 socket**。
4. **唯一挂死场景：未知 type 值（Quirk #3）**——`{"type":"xxx"}` 中的 `xxx` 不在 `ping` / `simtalk_syntax` / `simtalk_run` / `readlog` 四个白名单内时，服务端**静默不写回包**，必须靠 `--timeout` 兜底。建议客户端对未知 type 提前做白名单校验，不要直接发出去。
5. **服务端进程稳定性 ✅**——16 次坏 JSON 风暴后，ping 和合法 simtalk_run 均正常返回。

## 9. 建议 / Recommendations

1. **服务端可改进点**（非阻塞，但建议）：
   - **bad-04**：`[1,2,3]` 应明确抛"期望 JSON object，实际收到 array"而非混用"字段缺失"——错误归类更准。
   - **bad-07**：未知 type 应回一个 `action_result`（`result:"failed"` + `log:"Unknown message type 'xxx'"`），避免静默挂死。
   - **bad-12**：`simtalk_code:12345` 时服务端回包的 `type:""` / `result:""` 是空字符串而非标准字段值，期望是 `"action_result"` / `"failed"`。
2. **客户端使用建议**：
   - **必须**对 `type` 字段做白名单校验（`ping` / `simtalk_syntax` / `simtalk_run` / `readlog`），否则会触发 Quirk #3 挂死。
   - 对 `simtalk_run` 路径用**双重判据**：`result == "success" AND not log.startswith("code execute failed")` —— 这是用户主动设计的软失败契约，不要"修复"服务端。
   - 对 JSON 解析错 / 字段缺失等"裸字符串"回包，客户端要做非 JSON fallback 解析。
3. **文档更新建议**：把本节的"异常抛出行为总览表"合并进 `references/message-schema.md` 的"已知服务端行为差异"小节，新增 **Quirk #13：未知 type 值会让 socket 静默挂死**。

## 10. 与 v15 的对照 / Diff vs v15

| 维度 | v15 | v16 |
|---|---|---|
| 测试对象 | A–M 函数正确路径 | 异常抛出/坏 JSON 边界路径 |
| 测试用例数 | 25（17 sx + 8 rn） | 17（11 坏 JSON + 5 SimTalk 异常 + 1 稳定性 ping） |
| 触发挂死的请求 | 0 | 1（bad-07 未知 type） |
| 验证异常抛出 | ❌ 未涉及 | ✅ 三类异常（JSON 解析 / Schema / SimTalk）全部验证 |
| readlog | ❌（v15 回归） | ❌ 本轮未涉及 |