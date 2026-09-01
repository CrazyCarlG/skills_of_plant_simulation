---
last_updated: 2026-09-01
contributors: [@z004bjuu, @plant-simulation-expert, @plant-simulation-experience-curator]
scope: SimtalkClaude TCP 桥 v1+v2 文档入口 + 协议层静默失败模式 Quirk #1-#19 + 单语句约束 + multi-bridge build 差异
---

# SimtalkClaude —— v1 + v2 文档入口

> v1 在 2026-08-26 dump 实测；v2 在 2026-08-27 Factory51 集成场景下离线分析。
> 业务侧（与具体模型的耦合、隔离策略）见 [`04-model-case-studies/factory51/factory51-simtalkclaude-integration.md`](../04-model-case-studies/factory51/factory51-simtalkclaude-integration.md)。

## 主题文件

| 主题 | 文件 | 内容 |
|---|---|---|
| 概览与目录 | [`simtalkclaude-overview.md`](./simtalkclaude-overview.md) | v1/v2 定位、支持动作、四层目录、后续方向 |
| 协议与模式 | [`simtalkclaude-protocol.md`](./simtalkclaude-protocol.md) | 帧格式、动作路由、鉴权、回复字段、scratch buffer、handler 模式、复现命令 |
| v2 新增功能 | [`simtalkclaude-v2-features.md`](./simtalkclaude-v2-features.md) | 鉴权握手、双协议分帧、连接状态机、输入校验、容器清理、实例结构 |
| 经验与避坑 | [`simtalkclaude-lessons.md`](./simtalkclaude-lessons.md) | Plant Simulation 实测教训、推荐实践、反模式 |
| 版本速查 | [`simtalkclaude-v1-v2-delta.md`](./simtalkclaude-v1-v2-delta.md) | v1 vs v2 方法清单与迁移风险 |

## 数据来源

- v1：`skills/local-simtalk-read-library/data/simtalkclaude_dump.json`
- v2：`skills/local-simtalk-add-note-to-method/code_log/SimtalkClaude2_*_program_original.txt`（22 个 method 备份）

**经验来源**：2026-08-26 用 `local-simtalk-read-library` v1 + `local-simtalk-get-folder-tree` 跑全量 dump 实测 v1；2026-08-27 离线分析 v2 备份。§五中的 Plant Simulation 行为均经过一次 `simtalk_run` + `readlog` 实测验证。

---

## 经验 Log

> 本节是 **append-only** 时间线——新发现直接追加在末尾，**不要修改主体**。
> 贡献流程、entry 字段格式、Supersede 模式见 [`CONTRIBUTING.md`](../../CONTRIBUTING.md)。

> [curator-audited 2026-08-28 by @plant-simulation-experience-curator — pre-curator entry; see `agents/curator-reports/2026-08-28-curator-report.md` audit-003]

### 2026-08-28 by @plant-simulation-expert — `json.dumps()` 推 SimTalk source 到 Method.Program 是反模式
- **症状**：用 `json.dumps(body)` 把多行 SimTalk 源串起来发到 `m.Program` 后，`simtalk_syntax` 报 `Syntax error at '\'`。检查 `m.Program` 实际内容：所有真 newline 都被编码成两字符字面 `\n`——Program 是一行长串，不是期望的 60+ 行源码。
- **根因**：
  1. `json.dumps()` 把 newline 编码为 `\n` 两字符 escape。
  2. SimTalk 不解释字符串字面量里的 `\n` 转义序列，服务端按字面存储。
  3. 结果是源码挤成一行并包含大量 `\n` 字符，编译失败。
- **Workaround / 结论**：用 `escape(line) + chr(10)` 拼接模式。每行独立字符串字面量，行间以 `+ chr(10) +` 拼接，服务端收到真 multi-line 源码。
- **衍生约束**：SimTalk 字符串字面量有约 1KB raw char cap，chunk_size 通常 500 字节、5-10 行。
- **tags**：`json.dumps`, `antipattern`, `Method.Program`, `chunked-writer`, `chr(10)`, `escape`
- **see also**：`01-domain-concepts/derived-methods-quirks.md §Quirk #1`；`skills/local-simtalk-write-simtalk/scripts/push_mpaste_remaining.py`

> [curator-audited 2026-08-28 by @plant-simulation-experience-curator — pre-curator entry; see `agents/curator-reports/2026-08-28-curator-report.md` audit-004]

### 2026-08-28 by @plant-simulation-expert — `simtalk_hasError` 在 v15+ 对 Method body 报错有 false-positive
- **症状**：把 MLayout body push 进 `.Program` 后跑 `simtalk_hasError`，返回 `result:success`，但 `log` 开头是 `code execute failed. error msg: Left and right sides of the assignment are incompatible`；Method 自身执行却是 success，节点验证全部正确。
- **根因**：`simtalk_hasError` 在 v15+ 对某些合法 SimTalk 模式误报 incompatible type。
- **Workaround / 结论**：判断 Method body 正确性依靠 Method 自身执行结果和返回状态，不以 `simtalk_hasError` probe 单独判真。
- **tags**：`simtalk_hasError`, `false-positive`, `v15+`, `assignment-type-check`
- **see also**：`skills/local-simtalk-execution/references/lifelines.md §6`

> [curator-audited 2026-08-28 by @plant-simulation-experience-curator — pre-curator entry; see `agents/curator-reports/2026-08-28-curator-report.md` audit-005]

### 2026-08-28 by @plant-simulation-expert — `lp.Value := ""` 在 v15+ 能清空 Variable
- **症状**：实测 string Variable 显式赋值 `lp.Value := ""` 正常工作，Variable 立刻恢复空字符串，关联 3D bounding box 同步收缩。
- **根因**：typed Variable 使用 `:=` 可能丢失 length 类型，但纯 string Variable 使用 `Value := ""` 是合法的。
- **Workaround / 结论**：报告和状态容器优先使用纯 string Variable。
- **tags**：`Variable.Value`, `string-clear`, `v15+`, `auto-clear-pattern`
- **see also**：`01-domain-concepts/derived-methods-quirks.md §经验 Log`

> [curator-audited 2026-08-28 by @plant-simulation-experience-curator — pre-curator entry; see `agents/curator-reports/2026-08-28-curator-report.md` audit-006]

### 2026-08-28 by @plant-simulation-expert — `simtalk_run` 无法捕获 Method 返回值
- **症状**：通过桥执行 Method 试 `return X` 报 `method has no return value`；试 `print X` 又可能被 multi-callchain statement parser 吞掉。
- **根因**：`simtalk_run` 的 wrapper 是 void method，没有合法的 return path；`print` 在多语句上下文中的输出不可靠。
- **Workaround / 结论**：Method 内写入 string Variable，桥外用只读属性读取；不要依赖 print log 传递返回值。
- **tags**：`simtalk_run`, `return-value`, `readback`, `Quirk-#6`, `attr_modify`
- **see also**：`skills/local-simtalk-execution/references/lifelines.md §6`

> [curator-audited 2026-08-28 by @plant-simulation-experience-curator — pre-curator entry; see `agents/curator-reports/2026-08-28-curator-report.md` audit-007]

### 2026-08-28 by @plant-simulation-expert — Bridge + SimTalk 死循环耦合（只能 PS 重启恢复）
- **症状**：Method 进入 `while` 死循环后，bridge socket timeout 无法终止；后续 `simtalk_run` 全部 stall，bridge 进入半死状态。
- **根因**：Plant Simulation 服务端把 SimTalk 执行 attach 到 UI 进程组，socket 关闭后服务端进入等待 UI 响应状态，没有 watchdog。
- **Workaround / 结论**：
  1. 唯一可靠恢复方式是重启 Plant Simulation，重建自定义方法。
  2. 所有 `while` 循环必须带 termination sentinel。
  3. 同时使用 bridge `--timeout N` 和外层 `subprocess.run(..., timeout=N+5)`。
  4. 非平凡算法先做 smoke test，并为每个成功步骤设置独立成功信号。
- **tags**：`bridge-deadlock`, `infinite-loop`, `while-sentinel`, `restart-required`, `v15+`, `no-watchdog`
- **see also**：团队记忆 `memory/team/bridge-infinite-loop-safety.md`；`derived-methods-quirks.md §经验 Log`
- **反思**：桥卡死后不要盲目重试；应直接说明需要重启 Plant Simulation 并重建方法。

### 2026-09-01 by @plant-simulation-experience-curator — Plant Simulation `.execute()` 不刷新 `.Program` 编译缓存;write→execute 路径必须 reopen model 或走 `executeSilent(<expr>)` 模式

- **症状**:用 `m.Program := "<new body>"` 写入新 program 后,调用 `m.execute()` 仍跑**首次编译**的旧版本——即使 `.Program` 已更新、`simtalk_syntax` 验证编译通过、`.execute()` 的 wrapper 是合法的。本次 `.AGV_Claude` 7 method 案例:08-31 写入 → 09-01 readback 发现 7/7 method 全空(其实更早的版本是:即使 `.Program` 写入成功,`.execute()` 仍跑首次 compile 的代码)。
- **根因**:Plant Simulation 对每个 Method object 维护一份"已编译的 bytecode 缓存",挂在 Method object 自身。`.Program` 属性改变时缓存**不**自动失效——`.execute()` 直接调缓存,**绕过 `.Program` 的重新 parse**。`simtalk_syntax` 单独调时是 fresh compile(不读缓存),所以验证通过 ≠ `.execute()` 行为正确。
- **Workaround / 结论**:**两条独立路径**:

  ```simtalk
  -- 路径 A (推荐):不依赖 .execute() 缓存,走 executeSilent(str_to_obj(...).Program) 模式
  -- 永远 fresh compile,无缓存问题
  var m : any
  m := str_to_obj(".MyObj.MyMethod")
  executeSilent(m.Program)
  var err := getExecuteSilentError
  if err /= ""
      print "runtime error: " + err
  end
  ```

  ```text
  -- 路径 B (仅在 path A 不适用时):关闭 + 重新打开 model file
  -- 1. Plant Simulation GUI: File → Close (保存)
  -- 2. File → Open → 选 .psfm
  -- 3. 重启桥 server(.~.~.~.~.Server init → start)
  -- 4. 现在 .execute() 会用新 .Program
  ```

  **路径选择的判定**:
  - Agent 频繁跑 + 改 method body → 路径 A(`executeSilent` 模式)→ 无需 GUI 操作
  - Model 不可频繁重启(用户工作流)→ 路径 A
  - 一次性脚本测试 + 不想写 executeSilent wrapper → 路径 B(关+开 model)
  - **绝对禁忌**:`m.Program := new; m.execute()` —— **永远** 不会跑新 body

  **`.execute()` 的合法使用场景**:
  - Method body 第一次写入时(syntax check 模式)
  - Method body 从未改过(缓存与 .Program 一致)
  - 用户已 close+reopen model 后(缓存被清)
  - Method 是 GUI Methods 编辑器里手写的(缓存与 GUI .Program 一致)

- **tags**:`simtalk`, `method-execute`, `program-cache`, `compile-cache`, `invalidate-cache`, `executeSilent-alternative`, `model-reopen`, `silent-failure-mode-5`
- **see also**:`02-bridge-tool/simtalkclaude-v1-and-v2.md §经验 Log entry 2026-08-28 (Bridge + SimTalk 死循环)`(相关但不同——这是死循环,本条是 stale cache);`skills/local-simtalk-execution/references/lifelines.md §Quirk #6/#7/#13`(现有 3 种静默失败模式;本条是第 5 种);`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-recovery.md` §03-workflow-playbook;`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-wrap.md` §Key findings 第 3 条;`skills/local-simtalk-execution/log/2026-09-01_agv-v2-write-and-cache.md` Finding #3

> 这条经验教会我:
> - **缓存与属性的非对称失效** 是 Plant Simulation 长期未修的隐式合约。任何 "你写的 .Program 立即生效" 的直觉都是错的——**必须考虑 compile 缓存的生命周期**。这是 08-31 → 09-01 整个 .AGV_Claude 修复链"7 method 全 verify OK 但全空 / 全跑老代码"的**根因**。
> - **`simtalk_syntax` 通过 ≠ `.execute()` 行为正确**——前者 fresh compile,后者用缓存。两个判据不能互相替代。本次 agent 反复被 "syntax check PASS" 误导,以为 method 可用,**实际上 .execute() 跑的是首次 compile 的 body**(可能是空 / 可能是上次版本)。
> - **跨 skill 连锁影响**:任何上层 skill(`write_simtalk.py` / `add_note.py` / `class_management`)如果依赖 "write 后立刻 `.execute()` 验证"——它们的 verify 步骤**全是 silent failure**。需要从根上改 skill 行为(走 `executeSilent` 模式),否则 agent 看到的 "verify OK" 都是幻觉。**本次 quarantine-001 + 本条 entry 是同一个根因的不同层面**——一个修 workflow、一个修 bridge 认识。

### 2026-09-01 by @plant-simulation-experience-curator — Bridge JSON 层在大 batch probe 后卡死;TCP accept 仍工作但所有 ping/run/readlog 无 JSON 回包

- **症状**:跑完 `read_library.py` 的 14 batch × 8 paths 大批量探针后,服务端 TCP `host.docker.internal:50007` 仍显示 `CONNECTED`(accept() 工作),但任何后续 `simtalk_send.py ping` / `simtalk_send.py run <...>` / `simtalk_send.py readlog` / `bfs_full.py ...` 全部:
  - `EXIT=1`(timeout)
  - 或 "JSON decode error"(server 返回非合法 JSON)
  - 或纯 hang(无 stdout/stderr,直到 `--timeout` 触发)
  服务端 `handler` 不再回包,但进程没崩。
- **根因**(best guess,需复测):Bridge 的 server-side handler (`SimtalkAction.Run_Simutalk` 等) 可能持有一把**未释放的 lock**——大 batch probe 之间没有 "release" 步骤,导致后续请求卡在等锁。Socket 还在 accept,所以 TCP 层 `connect` 看似 OK,但 handler 进入"等待自己"的 deadlock。
- **Workaround / 结论**:

  ```bash
  # 1. 立刻停手,不要 retry(死循环只会卡更死)
  # Hard Rule #1: 大 batch 出问题时不要盲目重试

  # 2. Mitigation A: 在 batch 之间插 ping 保持 channel
  python3 skills/local-simtalk-execution/scripts/simtalk_send.py ping
  # 然后跑下一 batch

  # 3. Mitigation B: 调长 timeout(默认 10s → 30s)
  python3 skills/local-simtalk-execution/scripts/simtalk_send.py --timeout 30 run '<sim>'

  # 4. Mitigation C: 调 Server.Reconnect 弹 socket(需要 SimTalkClaude server 暴露这个 API)
  python3 skills/local-simtalk-execution/scripts/simtalk_send.py run \
    '.SimtalkClaude.Server.Reconnect'   # 或类似 — 视 server 实现

  # 5. 终极方案:用户手动重启 Plant Simulation server
  #    - .SimtalkClaude2 Frame → init → start → 等 "Server listening on 50007"
  #    - 这是 100% 可靠但需要 GUI 操作
  ```

  **判定**:
  - TCP `CONNECTED` 但所有 simtalk_send EXIT=1 / JSON decode error → bridge JSON 层卡死
  - 看到 `Unknown identifier` / `Method not found` 等正常错误 → 不是卡死,是普通 fail
  - 看到 "Server has been shut down" / "Connection closed" → TCP 真的断了(不同情况)

- **tags**:`bridge-json-hang`, `tcp-accept-but-no-reply`, `lock-not-released`, `large-batch-trigger`, `silent-failure-mode-6`, `mitigation-required`
- **see also**:`02-bridge-tool/simtalkclaude-v1-and-v2.md §经验 Log entry 2026-08-28 (Bridge + SimTalk 死循环)`(相关:死循环卡死 = method 进入 infinite loop;本条 = bridge handler 卡死 = 大 batch 触发);`skills/local-simtalk-execution/references/lifelines.md §Quirk #13`(type 白名单外的 type 让服务端静默挂死到 timeout;本条类似但 trigger 是 batch size);`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-recovery-prep.md` §Key findings 2;`skills/local-simtalk-execution/log/2026-09-01_agv-claude-recovery-prep.md` Step 5-9

> 这条经验教会我:
> - **"TCP 连着 ≠ 桥活着"**:accept() 工作不代表 handler 没卡死。下次 batch 大小 = 14 × 8 = 112 paths 这种规模,务必在 batch 间插 ping——把"长时间无 JSON 回包"作为触发停手的信号,而不是 "看到 CONNECTED 就以为活着"。
> - **大 batch 的隐藏成本**:虽然单 batch `simtalk_run` 都成功,但 server-side handler 累积状态。**任何"批跑工具"(bfs_full / probe_methods / read_library)都应该在 batch 间留窗口**——这是工具设计需要改进的地方,不只是 user 应急。
> - **与 lifelines Quirk #13 区分**:Quirk #13 是 `type` 字段非法直接挂死;本条是 `type` 合法但 handler lock 未释放。两者表现都是 "timeout",但根因 + mitigation 不同——**两者都需要新 Quirk #N**(quarantine 给 skills-optimizer)。

### 2026-09-01 by @plant-simulation-experience-curator — inner `executeSilent(<expr>)` 内的 `print` 完全不通过桥转发;必须用 `getExecuteSilentError` 捕获 error(bridge 静默失败第 4 种模式)

- **症状**:在 `executeSilent(<some expression>)` 内部用 `print "value is " + str(x)` 想看 `x` 的值——`simtalk_run` 返 `result: "success"`,`readlog` 没拿到这条 "value is ..." 字符串。但 `print` 在 GUI Console 看得到(去 Window ribbon → Console)。
- **根因**:`executeSilent` 是"静默执行"模式——它有独立的 error 缓冲区 + 独立的 print 缓冲区,**不**走 server-side handler 的 "stdout → bridge log" 转发通道。`simtalk_run` 调用 `executeSilent` 时只取 `getExecuteSilentError` 的值;`print` 的输出被 silently dropped。
- **Workaround / 结论**:

  ```simtalk
  -- 错: 想看 print 没意义
  executeSilent("var x := 1 + 2; print x")  -- print 输出 silently dropped
  -- simtalk_run 返 "success"; readlog 看不到 "3"

  -- 对: 改用变量读回
  var result : string := ""
  executeSilent("var x := 1 + 2; result := to_str(x)")  -- 把 x 写到 outer-scope Variable
  print result  -- 现在 print 在 outer scope,会被转发
  ```

  **error capture 模式**(simtalk_run 的 canonical 模式):

  ```simtalk
  executeSilent("<sim_code>")
  var err := getExecuteSilentError
  if err /= ""
      print "runtime error: " + err    -- outer scope print,会被转发
  end
  ```

  **`executeSilent` vs 普通 `simtalk_run`**:
  - **普通 `simtalk_run`**:wrapper method 不带 `executeSilent`,print 输出走桥转发 → 但 wrapper 自己 throw 任何 runtime exception 都会被捕获并以 "code execute failed" 形式返回(Quirk #7)
  - **`simtalk_run` 内 `executeSilent(<expr>)`**:print 不走桥;runtime exception 用 `getExecuteSilentError` 捕获;**只有 error string 转发,print 全 silently dropped**

- **tags**:`executeSilent`, `print-not-forwarded`, `bridge-silent-drop`, `getExecuteSilentError`, `silent-failure-mode-4`, `error-capture-canonical`
- **see also**:`02-bridge-tool/simtalkclaude-v1-and-v2.md §经验 Log entry 2026-08-28 (simtalk_run 无法捕获 Method 返回值)`(相关:都是 "bridge 看不到 method 内部状态");`skills/local-simtalk-execution/references/lifelines.md §Quirk #6/#7/#13`(3 种现有静默失败模式;本条是第 4 种);`02-bridge-tool/simtalkclaude-protocol.md §4.1`(scratch buffer pattern 已用 executeSilent);`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-recovery.md` §02-bridge-tool 第 4 条;`skills/local-simtalk-execution/log/2026-09-01_agv-v2-wrap-probe.md` §"3 bridge 行为 findings" #2

> 这条经验教会我:
> - **executeSilent 是"静默"是有意为之**——它设计目标是 "execute without raising exception, capture error string"——print 不是 error,所以被 silently dropped。**不要试图用 print 调 executeSilent**——这是 anti-pattern。
> - **bridge 静默失败模式已经累计 5 种**:Quirk #6(data 字段空)/ #7(result=success 但 log=code execute failed)/ #13(type 非法挂死) / 本条 #4 (executeSilent print 不转发) / `exec-005`(.execute() 不刷 .Program 缓存)。下次 handoff 给 skills-optimizer 时建议赋新 Quirk #14、#15。
> - **canonical capture 模式**:`executeSilent(<expr>); var err := getExecuteSilentError` 几乎是唯一可靠的"在 bridge 上下文捕获 error"路径——值得在 playbook §3.3 加一行 canonical example。

### 2026-09-01 by @plant-simulation-experience-curator — TCP 服务端口可手动 rebind(50007 → 50009);agents 必须扫/验证端口,不能假设默认 50007

- **症状**:
  - `simtalk_send.py ping` 默认 `--port 50007` 一直 EXIT=1 / timeout
  - 但 TCP `netstat -tlnp` 显示 50007 是 LISTEN——bridge accept 工作
  - 进一步 wide-scan 发现 50009 才是真正"活的"服务端口(50007 是 zombie: accept 但 handler 不回)
  - 任何 hardcode `--port 50007` 的 skill(`bfs_full.py` / `write_simtalk.py` / `add_note.py`)在用户切端口后全部失败
- **根因**:Plant Simulation 端 `.SimtalkClaude2` Frame 的 init 代码里 `mySocket.create("<port>")` 是 user-editable Variable。用户(或维护脚本)改了这个 Variable 就改了监听端口。Server 端没有"必须 50007"的硬约束——这是协议 **soft default**,不是 spec。
- **Workaround / 结论**:

  ```bash
  # 1. 启动时 wide-scan,不要假设 50007
  for port in 50001 50005 50007 50008 50009 50010; do
      python3 skills/local-simtalk-execution/scripts/simtalk_send.py --port $port ping 2>&1 | head -1
  done
  # 找到 "result: success" 那个 port = 真活端口

  # 2. 写 ~/.claude/ports.env 或 SKILL 上下文里 export SIMTALK_PORT=<discovered_port>
  export SIMTALK_PORT=50009
  # 让所有 simtalk_send 调用读这个 env

  # 3. skill 层:让 simtalk_send.py 默认读 SIMTALK_PORT 环境变量,fallback 到 50007
  # (修 SKILL.md + scripts/simtalk_send.py — quarantine 给 skills-optimizer)
  ```

  **判定**:
  - `simtalk_send.py ping` timeout → 检查 `--host` (默认 `host.docker.internal`?);再 wide-scan port
  - 看到 "Server has been shut down" → 端口对但 server 真的关了(不是 zombie)
  - 看到 "Connection refused" → 端口没监听(走 wide-scan)
  - 看到 TCP accept OK 但所有 simtalk_call timeout → zombie port(本条 quirk)

- **tags**:`tcp-port`, `port-rebind`, `50007-default`, `50009-actual`, `wide-scan-required`, `env-variable-needed`, `skill-hardcode-bug`, `silent-failure-mode-7`
- **see also**:`02-bridge-tool/simtalkclaude-protocol.md §3.1`(帧格式)+ `simtalkclaude-overview.md §支持动作`(skill 与默认 port 的约定);`skills/local-simtalk-execution/references/lifelines.md §1 连接目标`(默认 50007 + host.docker.internal);`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-wrap.md` §Key findings "TCP 探测顺序很关键";`03-agent-memory/plant-simulation-expert-memory/2026-08-31_session-summary_replicate-source-to-target.md` Finding #2(bfs_full.py 硬编码 50007 早报)

> 这条经验教会我:
> - **"默认 50007" 是约定不是协议**:任何 "我假设 server 在这个端口" 的 agent 都是 fragile 的——server 端可以改,改完 agent 静默失败。**唯一可靠 = 启动时 wide-scan**。
> - **多 skill 共享一个 hardcode port 是 anti-pattern**:`bfs_full.py` + `write_simtalk.py` + `add_note.py` 都各自硬编码 50007——任一 server 改 port,所有 skill 全错。**正确架构 = 全部读 `SIMTALK_PORT` env variable,fallback 50007**——这是 skills-optimizer 应该修的地方。
> - **wide-scan 是值得脚本化的 agent 工具**:`skills/local-simtalk-execution/scripts/` 应该有 `scan_port.py` 一键扫 50000-50100 找活端口。**当前没有 → quarantine 给 skills-optimizer 起草一个**。

### 2026-09-01 by @plant-simulation-experience-curator — `simtalk_run` 单语句限制:`for/next` / `if/then/end` block 全部 "Syntax error near 'print'";必须外层 shell 循环 + 多次 send

- **症状**:在一次 `simtalk_run` 调用里塞多语句 / 控制流,全部报 `Syntax error near 'print'`(错误指向第一行内的 print 关键字):
  ```bash
  python3 simtalk_send.py run '
    var obj : any := str_to_obj(".X")
    for i := 1 to obj.NumChildren:
      print obj.node(i).Name + "|" + obj.node(i).InternalClassType
    next
  '
  # → Syntax error near 'print' (虽然语法本身正确)
  ```
  - 同样失败:`if x > 0 then print "yes"; end`(block form)
  - 同样失败:`var a := 1; var b := 2; print a + b`(多 var 赋值)
- **根因**:`simtalk_run` 的服务端 handler 把整个 `<sim_code>` 当作**单条 SimTalk statement** parse,而不是一段完整的 SimTalk 脚本。SimTalk 自身的 parser 接受多语句 + 控制流,但 bridge 的 wrapper method(`.~.~.~.~.~.SimtalkAction.simtalk_execute`)在传入时**先做 statement-boundary 切分**(`;` 分号)→ 多语句变成多个 wrapper method 调用,但中间任何一条 statement 包含 `for/next` / `if/end` block 时,block 自身是 1 个 statement,**而 wrapper 把整个 `<sim_code>` 包成 1 个 statement**——block 嵌入就被 parser 拒。
- **Workaround / 结论**:

  ```bash
  # canonical 模式:外层 shell for-loop + 每次 send 一个最小语句
  python3 simtalk_send.py run 'print "###START###"'
  for i in $(seq 1 N); do
      python3 simtalk_send.py run "
        var n := str_to_obj(\".X\").node(${i});
        print \"${i}| \" + n.Name + \"| \" + n.InternalClassType
      " | tee -a dump.txt
  done
  python3 simtalk_send.py run 'print "###END###"'

  # 或:把多语句塞到一个表里,SIMPLIFY 一次 send
  python3 simtalk_send.py run '
    var obj : any := str_to_obj(".X")
    print "###MARKER###"
    print "TOTAL=" + to_str(obj.NumChildren)
    print "###END###"
  '
  # ↑ 多 print statement 但没有控制流 → OK(因为只是 sequential prints)
  ```

  **判定 / 快速试错**:
  - 把 `<sim_code>` 在外部用 `printf` + chr(10) 拼成一个**只有 sequential prints / single statement** 的字符串 → 99% 能跑通
  - 任何 `for/next` / `if/then/end` / `while/next` block → 必须外层 shell 包
  - 多 `var x := ...; var y := ...` 也可能崩(实测 reproduce 不一致,**safe pattern** = 单 var 或全 table 形式)

  **实测反例**(单 statement 通过):
  - `print str_to_obj(".X").node(1).Name`  ✓
  - `print to_str(str_to_obj(".X").NumChildren) + " children"`  ✓
  - `var t : table; t := str_to_obj(".X"); print t[0, 0]`  ✓
  - `print simtalk_hasError("var x := 1; print x")`  ✓(simtalk_hasError 是 wrapper,内含多语句 OK)

- **tags**:`simtalk-run`, `single-statement`, `for-next-block-rejected`, `if-end-block-rejected`, `shell-loop-canonical`, `wrapper-statement-boundary`, `silent-failure-mode-8`
- **see also**:`02-bridge-tool/simtalkclaude-v1-and-v2.md §经验 Log exp-005 (.execute() 不刷 .Program 缓存)`(同样是 bridge 层 vs SimTalk parser 的不对称);`02-bridge-tool/simtalkclaude-protocol.md §3.1 simtalk_run action`(`action` 字段 payload 必须是单 SimTalk statement 的硬约定;SKILL.md 没说);`skills/local-simtalk-execution/references/lifelines.md §2 simtalk_run 协议`(目前没明确写"单语句"约束);`skills/local-simtalk-execution/log/2026-08-28_agv-50008-discovery.md` Step 4 + §"What this run validated / learned" #1(bisect 验证: `for i:=1 to ...: print ...; next` 全部错误)

> 这条经验教会我:
> - **bridge 的 `simtalk_run` ≠ Python `exec()`**:exec 接受任意长字符串,bridge 必须 1 statement。这是 bridge 设计者为了"安全 + 简单"做的限制,但**没有文档化**给 agent。下次写 `simtalk_run` 内容时,先把代码 grep 一遍 `for/while/if/then/end/next` —— 出现就改成 shell-loop。
> - **"单语句" + "simtalk_hasError" 是个强力组合**:`simtalk_hasError("多语句 <body>")` 验证"body 自身语法对"(返回 "has no Error"),然后 bridge-side `simtalk_run` 单语句 wrapper 跑 → 比"bridge 单语句 simtalk_run 多语句 body"可靠 100 倍。本次 agv-50008-discovery 用这个 pattern 跑通了枚举。
> - **canonical batch pattern**:
>   1. `simtalk_run 'print "###START###"'`
>   2. `for i in $(seq 1 N): simtalk_run '<1-statement per i>'`
>   3. `simtalk_run 'print "###END###"'`
>   4. `readlog` 解析 START/END 之间的输出
>   这是 bridge 协议级别的"循环 + 标定"模式,值得在 playbook §3.3 + simtalkclaude-protocol.md §4.2 加 canonical example。
> - **与 lifelines Quirk 模式区分**:这是"协议层硬限制"(parser 不接受),不是"运行期静默失败"。两者 mitigation 完全不同——前者必须改 caller,后者只需加 retry。**agent 必须分清"协议错"和"运行错"**。

### 2026-09-01 by @plant-simulation-experience-curator — 不同 Plant Simulation 实例的 SimtalkClaude bridge build 可能不同,导致 readlog buffer 行为不一致;目标端 state 读回必须走 simtalk_run error 通道

- **症状**:在 `host:50010`(target PS 实例,用户加载的"空白"模型)上跑:
  ```bash
  python3 simtalk_send.py --port 50010 run 'print "hello world test marker 12345"'
  # → result: success
  python3 simtalk_send.py --port 50010 readlog
  # → 返回 715 字节固定窗口,内容是**早期** print 输出,**新 print 不出现**
  ```
  对比:同样 `print "..."` 在 `host:50007`(source PS 实例)上跑 `readlog` 正常返回新 print。
  - 两个 instance 都报 Plant Simulation 相同版本 `2606.0002`
  - 区别在**两个 instance 加载的 SimtalkClaude bridge build 不同**(用户 target 用的可能是旧 bridge 或 build 时未 enable 完整 protocol)
- **根因**(best guess,需复测):
  - target instance 的 bridge `m_str_send` / `RxBuffer` flush 机制不完整(readlog buffer ceiling 715 字节 = 早期某版本的 hard cap)
  - 或 readlog 的 handler 还在用旧的 print-buffer 而不是 scratch-buffer(参 `02-bridge-tool/simtalkclaude-protocol.md §4.1 scratch buffer pattern`)
  - PS 端 simtalk_run **确实执行了 print**(返回 success),只是 readlog 的采集端不刷新
- **Workaround / 结论**:

  ```bash
  # 1. 在 target 上做 state read-back:不要用 readlog,改用 simtalk_run error 通道
  python3 simtalk_send.py --port 50010 run '
    var obj : any := str_to_obj(".X");
    print "###MARKER###";
    print "NAME=" + obj.Name;
    print "TYPE=" + obj.InternalClassType;
    print "###END###"
  '
  # ↑ 即使 readlog 不刷新, simtalk_run 的 log 字段也会带 print 输出(timing 不一定实时,但最终能拿到)
  ```

  **判定**(在 multi-bridge / multi-instance 场景):
  - simtalk_run 返 `result: success` 但 `readlog` 不动 → readlog broken,改用 simtalk_run error/scratch channel
  - simtalk_run 返 `result: failed` 且 `log` 以 `code execute failed` 开头 → 真 runtime error,正常路径
  - simtalk_run 返 `result: success` 且 `log` 以 `execute success` 开头 → 跑成功,**用 readlog 拿 print**(默认路径)
  - **target PS 实例的 readlog 一定先 verify 一次再依赖**:`simtalk_run 'print "PROBE"'` → `readlog` 看到 PROBE → OK;看不到 → readlog broken,改 fallback

  **future-proof**:
  - 任何 "我要 dump 整个 model" 工作流,**先在每个 instance 上跑一次 readlog 探针**,不要默认 source 工作就 target 也工作
  - **`scripts/verify_readlog.py`**(建议 skill 增加):跑 ping + 单 print + readlog 三步,timeout 2s 内拿到 print = OK;否则 fallback to simtalk_run error channel

- **tags**:`multi-bridge`, `bridge-build-divergence`, `readlog-frozen`, `715-byte-window`, `state-readback-fallback`, `simtalk-run-error-channel`, `silent-failure-mode-9`, `inter-instance-non-uniform`
- **see also**:`02-bridge-tool/simtalkclaude-v1-and-v2.md §经验 Log entry 2026-08-28 (Bridge + SimTalk 死循环)`(相关:都是 bridge 死锁类问题;本条是 readlog 通道卡死,不是 handler 死锁);`02-bridge-tool/simtalkclaude-v1-and-v2.md §经验 Log exp-007 (Bridge JSON 层在大 batch probe 后卡死)`(相关:大 batch 触发 server-side 状态累积;本条是 bridge build 差异导致 readlog 永远不刷新);`02-bridge-tool/simtalkclaude-v1-and-v2.md §经验 Log exp-010 (port-can-be-rebound)`(相关:50007 ↔ 50009 ↔ 50010 切换 + bridge build 差异 = 双层 fragility);`02-bridge-tool/simtalkclaude-protocol.md §4.1 scratch buffer pattern`(readlog 实现的来源);`03-agent-memory/plant-simulation-expert-memory/2026-08-31_session-summary_replicate-source-to-target.md` Finding 3(target 50010 readlog buffer frozen,直接 source)

> 这条经验教会我:
> - **"同一 Plant Simulation 版本" ≠ "同一 bridge 行为"**:bridge 是 plant simulation 上层的 Frame + Methods + Variables + PythonModule 集合,不同 instance 加载的 bridge 可能 build 不同(自己 compile 的 vs vendor 提供的 vs 旧 commit)。**任何 read 操作都要先 verify 再依赖**——readlog 不一定刷新,simtalk_run 不一定返完整 log,**只有 ping + 单语句探针是 universal 可靠的**。
> - **多 instance 场景的工作流硬规则**:在写"我要从 instance A 读 + 写到 instance B"的工具前,**两边都要跑 ping + 单 print + readlog 三件套 verify**。本次 08-31 replicate-source-to-target session 浪费 ~1h 在假设 readlog 工作上 —— 应该 5 分钟就能 verify 出来。
> - **state read-back fallback 必须是 layer 1,不是 layer 3**:
>   1. layer 1 (默认): `readlog`
>   2. layer 2 (readlog broken): `simtalk_run` 的 log 字段(延迟几秒可见)
>   3. layer 3 (simtalk_run 也 broken):`var dest : string := ""; simtalk_run 'dest := "<value>"'` 然后再 readlog 读 dest
>   4. layer 4 (全坏): 用户 GUI 手工 + export
> - **与 exp-007 (bridge JSON hang after batch) 区分**:exp-007 是 "TCP accept OK + handler lock 不释放" → timeout;本条是 "TCP accept OK + readlog 采集端不刷新" → 拿不到 print。两者表现都是 "server 不响应",但根因完全不同——本条是**静态差异**(两个 instance 行为不同),exp-007 是**动态累积**(batch 触发)。Mitigation 也不同:本条需 layer-2 fallback;exp-007 需 mitigation A/B/C 重启 socket。
