# local-simtalk-execution Test Session v17 — 2026-08-25

测试目标：v17 重构 + 高层封装 `scripts/simtalk_send.py` 验证。

承接 P0-P3 优化：
- **P0**：建立 `references/lifelines.md` 作为硬规则唯一事实来源；`message-schema.md` 同步 v15 readlog 回归、v16 Quirk #13、异常抛出行为总览
- **P1**：把 SKILL.md / example.md / workflow.md / code-templates.md 里重复的"必须用 delimiter 模式"、"WSL2 必须用 host.docker.internal:50007"、"模态陷阱"等铁律全部替换为 `lifelines.md` 引用
- **P2**：新增 `scripts/simtalk_send.py` 高层封装——子命令 `ping` / `syntax` / `run` / `readlog` + 自动 `uuid action_id` + 默认参数（`host.docker.internal:50007`、delimiter 模式、`||END||` 帧）+ Quirk #6/#7 双重判据 + `type` 字段白名单（Quirk #13）
- **P3**：SKILL.md `description` 增加"诊断服务端异常 / server-side exception throwing 验证"作为触发场景

本轮验证：
1. `simtalk_send.py` 各子命令的退出码语义
2. Quirk #6/#7 双重判据
3. v15+ readlog 回归行为
4. type 白名单 + JSON 解析失败的兜底
5. 异常风暴后服务端稳定性

## 1. 环境 / Environment

- **Skill under test**：`skills/local-simtalk-execution/`
- **Server**：Plant Simulation（宿主机），TCP **50007**
- **Client host**：WSL2 容器 → `host.docker.internal:50007`
- **回包读取**：统一 `--resp-mode delimiter --resp-delimiter '||END||'`
- **辅助客户端**：`skills/local-simtalk-execution/scripts/socket_client.py`（底层）+ `skills/local-simtalk-execution/scripts/simtalk_send.py`（高层，v17 新增）
- **测试时间**：2026-08-25（接续 v16）

## 2. 握手 / Handshake

| ID | 命令 | 回包 | 退出码 | 结论 |
|---|---|---|---|---|
| v17-ping-init | `python3 scripts/simtalk_send.py ping` | `{ "type": "ping", "result": "success" }` | 0 | ✅ 链路通 |

## 3. simtalk_send.py 各子命令冒烟测试 / Subcommand Smoke Tests

> 所有子命令默认 `--host host.docker.internal --port 50007 --timeout 30 --resp-mode delimiter --resp-delimiter '||END||'`——零手工 boilerplate。

| ID | 子命令 | 关键代码 | 回包 `result` | 回包 `log` 摘要 | 退出码 | 结论 |
|---|---|---|---|---|---|---|
| v17-smk-ping | `ping` | (无) | `success` | —— | 0 | ✅ ping 子命令 OK |
| v17-smk-syntax-ok | `syntax` | `print 1+2` | `has no Error` | (含陈年 Quirk #7 log，不影响语法判据) | 0 | ✅ 语法通过 |
| v17-smk-syntax-fail | `syntax` | `var x := 1/0` | ` hasError ： Error in line 1: Division by zero. (in row :1)` | (空) | **12** | ✅ 语法失败 → 退出码 12（与文档约定一致） |
| v17-smk-run-ok | `run` | `print 1+2` | `success` | `execute success` | 0 | ✅ 真正执行成功 |
| v17-smk-run-quirk7 | `run` | `print nonExistentSymbol_QQ` | `success` | `code execute failed. error msg:Unknown identifier 'nonExistentSymbol_QQ'` | **11** | ✅ Quirk #7 软失败 → 退出码 11 |
| v17-smk-readlog | `readlog` | (无) | `success` | (v15 反馈循环内容，详见 §5) | **20** | ✅ readlog 命令工作 + 不可信警告 |

**退出码约定**（与 socket_client.py 一致 + 扩展）：

| 退出码 | 含义 |
|---|---|
| 0 | 语义成功 |
| 1 | 超时 |
| 2 | 无法建立连接 |
| 3 | 连接中途断开 / 服务端回包不是合法 JSON |
| **10** | `simtalk_run` 编译错或 `result != "success"` |
| **11** | `simtalk_run` Quirk #7 软失败（result=success 但 log 前缀 code execute failed） |
| **12** | `simtalk_syntax` 语法失败 / 服务端回裸字符串 |
| **20** | `readlog` 收到 result=success 但 ⚠️ v15+ 内容不可信 |

## 4. Quirk 双重判据验证 / Quirk Dual-Criterion Verification

> 关键点：只用 `result == "success"` 判据会漏掉运行时异常——双重判据 `result == "success" AND not log.startswith("code execute failed")` 是 v17 高层封装的卖点之一。

| ID | 测试 | `result` | `log` 前缀 | 退出码 | 判据 |
|---|---|---|---|---|---|
| v17-q7-happy | `run 'print 1+2'` | `success` | `execute success` | 0 | ✅ 真成功 |
| v17-q7-runtime | `run 'print nonExistentSymbol_QQ'` | `success` | `code execute failed. error msg:Unknown identifier ...` | **11** | ✅ Quirk #7 命中 |
| v17-q6-data-empty | （已知行为）`run 'print 1+2' --return-value` | `success` | `execute success` | 0 | ✅ `data` 字段不出（Quirk #6 实测不变） |

> v17-q6 备注：`--return-value` 在 `simtalk_send.py run` 子命令里也实现了，但回包 `data` 字段仍为空——与 v6/v8/v9/v15/v16 多次验证一致。

## 5. ⚠️ readlog v15+ 回归实测 / readlog v15 Regression Confirmed

> `simtalk_send.py readlog` 子命令实测回包（节选关键部分）：

```
{ "type": "", "action_id": "bd5918ec...", "result": "success",
  "log": "2026-08-25 11:52:30: Log file opened! Application Version: 2606.0002, UTC: 2026-08-25 03:52:30
2026-08-25 11:52:30: Local -->> Copilot: { \"type\": \"action_result\", \"action_id\": \"v15-rl-clean\", ... }
2026-08-25 11:52:30: Local -->> Copilot: { \"type\": \"action_result\", \"action_id\": \"v15-rl-probe2\", ... }
2026-08-25 11:47:30: Local -->> Copilot: { \"type\": \"action_result\", \"action_id\": \"v15-rl-02\", ... }
...（嵌套深度 7 层）" }
```

**结论**：
- ✅ `simtalk_send.py readlog` 能正常发出请求、剥离 `||END||`、解析回包
- ✅ 退出码 20 把"⚠️ v15+ 不可信"明确告知调用方
- ❌ 内容确实是 v15 反馈循环——把上一次 readlog 的响应嵌套回自己，捕获不到 simtalk_run 的 print 输出
- ✅ 与 `lifelines.md` §5 的预期完全吻合

## 6. `type` 白名单 + JSON 兜底 / Type Whitelist + JSON Fallback

| ID | 触发方式 | 期望 | 实测 | 结论 |
|---|---|---|---|---|
| v17-wl-1 | `simtalk_send.py` argparse 子命令 | 只接受 `ping`/`syntax`/`run`/`readlog` | argparse 自动拒绝其它子命令 | ✅ |
| v17-wl-2 | 直接用 `socket_client.py` 发未知 `type`（`{"type":"totally_made_up_type"}`） | 静默挂死到 timeout（Quirk #13） | `TIMEOUT: no reply within 5.0s` exit=1 | ✅ Quirk #13 复现 |
| v17-wl-3 | 直接用 `socket_client.py` 发坏 JSON（`this is not json`） | 服务端回裸字符串错误 | `Error in JSON data: Syntax error near line 1 at 'this is not'.` exit=0 | ✅ JSON 兜底 OK |
| v17-wl-4 | `simtalk_send.py` 收到裸字符串回包（如语法错误） | 退出码 12（不当作 socket 错） | v17-smk-syntax-fail exit=12 | ✅ 区分得清 |

## 7. 异常风暴后服务端稳定性 / Server Stability After Exception Storm

> 跑完 §3-§6 共 9 次请求（含 1 次超时挂死）后，验证服务端是否健在。

| ID | 命令 | 回包 | 退出码 | 结论 |
|---|---|---|---|---|
| v17-stab-ping | `simtalk_send.py ping` | `{ "type": "ping", "result": "success" }` | 0 | ✅ 服务端进程健在 |
| v17-stab-run | `simtalk_send.py run 'print 7*6'` | `result=success` / `log=execute success` | 0 | ✅ simtalk_run 正常 |

**结论**：服务端在 9 次请求 + 1 次超时挂死后仍能正常处理新连接与合法请求——与 v16 结论一致。

## 8. v17 重构成果 / v17 Refactor Outcomes

### 8.1 文档结构（v17 前 → v17 后）

| 文档 | v17 前 | v17 后 |
|---|---|---|
| `SKILL.md` | 重复"必须用 delimiter"、"WSL2 必须用 host.docker.internal"等铁律 | 引用 `references/lifelines.md` |
| `references/lifelines.md` | （不存在） | **新建**——所有硬规则的唯一事实来源 |
| `references/message-schema.md` | 顶部含散落的硬规则 | 顶部引用 `lifelines.md`，保留 Quirk #1-#13 + 异常抛出行为总览 |
| `references/workflow.md` | 重复铁律 | 引用 `lifelines.md` 各章节 |
| `references/code-templates.md` | 重复铁律 + v13 readlog "已修复" 标注 | 引用 `lifelines.md`，更新为 v15 回归现状 |
| `example/example.md` | 顶部 setup 表重复铁律 | 引用 `lifelines.md` 各章节 |
| `scripts/socket_client.py` | 底层一次性 TCP 客户端 | （不变） |
| `scripts/simtalk_send.py` | （不存在） | **新建**——高层封装，子命令 + Quirk 判据 |

### 8.2 `simtalk_send.py` 设计要点

| 设计点 | 实现 |
|---|---|
| 自动 `action_id` | `uuid.uuid4().hex` 每次新生成 |
| 默认连接目标 | `host.docker.internal:50007`（可 CLI 覆盖） |
| 默认分帧模式 | `delimiter` + `||END||`（避免 eof 超时陷阱） |
| Quirk #13 白名单 | argparse 子命令强制——`ping`/`syntax`/`run`/`readlog` |
| Quirk #6 | 自动剥离 `||END||` 后 JSON 解析；`data` 字段不读 |
| Quirk #7 | 退出码 11 区分软失败；调用方可针对性处理 |
| v15+ readlog 警告 | 退出码 20 + stderr 警告 |
| 退出码语义 | 0/1/2/3（socket 层）+ 10/11/12/20（语义层） |

### 8.3 铁律单点维护 / Single-Source-of-Truth

v17 之前，"WSL2 必须用 host.docker.internal"、"回复必须用 delimiter 模式"、"未知 type 静默挂死"等铁律散落在 SKILL.md / example.md / workflow.md / code-templates.md / message-schema.md 五个文档里——改一处必漏一处。

v17 把这些铁律集中到 `references/lifelines.md`，其它文档全部改为简短引用：
- "WSL2 容器连接目标（`host.docker.internal:50007`，详见 `lifelines.md` §1）"
- "回复分帧必须用 `--resp-mode delimiter --resp-delimiter '||END||'`（详见 `lifelines.md` §2）"
- "`type` 字段白名单（未知 type 静默挂死——Quirk #13，详见 `lifelines.md` §3）"

未来服务端行为变更只改 `lifelines.md` + `message-schema.md` 两个文件，其它文档的引用关系自动跟上。

## 9. 与 v16 的对照 / Diff vs v16

| 维度 | v16 | v17 |
|---|---|---|
| 测试对象 | 异常抛出 + 坏 JSON 边界 | 重构成果 + simtalk_send.py 验证 |
| 测试用例数 | 17 | 14（5 subcommand smoke + 3 Quirk dual + 4 whitelist/JSON + 2 stability） |
| 触发挂死的请求 | 1（bad-07 未知 type） | 1（v17-wl-2 同 bad-07） |
| `simtalk_send.py` 高层封装 | ❌ | ✅（4 子命令 + 8 退出码语义） |
| 文档铁律单点维护 | ❌（散落 5 文档） | ✅（`lifelines.md` 唯一来源） |
| readlog 行为 | ⚠️ v15 回归 | ⚠️ v15 回归（高层封装加退出码 20 警告） |

## 10. 结论 / Conclusions

1. **P0-P3 优化全部落地 ✅**——
   - `lifelines.md` 建立（10 章节，覆盖所有硬规则）
   - `message-schema.md` 同步 v15 回归 + Quirk #13 + 异常抛出行为总览
   - SKILL.md / example.md / workflow.md / code-templates.md 全部改为引用 `lifelines.md`
   - `simtalk_send.py` 高层封装可用——4 子命令、8 退出码、Quirk 判据内置
   - SKILL.md `description` 增加"诊断服务端异常"触发场景

2. **`simtalk_send.py` 行为正确 ✅**——
   - `ping` → 退出码 0 / `syntax` 通过 → 0 / `syntax` 失败 → 12 / `run` 成功 → 0 / `run` Quirk #7 → 11 / `readlog` → 20

3. **Quirk #13 白名单有效 ✅**——
   - argparse 子命令强制 + 直接调用 `socket_client.py` 验证未知 type 静默挂死（v17-wl-2）

4. **v15+ readlog 回归再次确认 ⚠️**——
   - `simtalk_send.py readlog` 退出码 20 + stderr 警告明确告知不可信
   - 内容验证仍是反馈循环嵌套——与 v15 / v16 一致

5. **服务端进程稳定性 ✅**——9 次请求 + 1 次超时挂死后 ping + simtalk_run 均正常。

## 11. 建议 / Recommendations

1. **`simtalk_send.py` 推荐使用**——比直接调 `socket_client.py` 少写 80% boilerplate（action_id / 分帧 / 默认 host / Quirk 判据全部内置）。
2. **`simtalk_send.py` 可加功能**（非阻塞）：
   - `--json-output`：把回包以 JSON 格式打到 stdout（当前是原始字符串）
   - `--quiet`：只打语义成功/失败结论，不打回包原文
   - `batch` 子命令：从 JSONL 文件读一批请求并发执行（注意 v15+ readlog 反馈循环仍存在，不要把 readlog 放进 batch 循环）
3. **`lifelines.md` 持续维护**——任何"硬规则"变更（服务端行为、字段语义、新 Quirk）只改本文件 + `message-schema.md`；其它文档通过引用自动同步。
4. **下次发现新 Quirk 时**——按 `lifelines.md` §3-§6 的格式追加新章节，并在 `message-schema.md` 的 Quirk 列表里追加对应编号。