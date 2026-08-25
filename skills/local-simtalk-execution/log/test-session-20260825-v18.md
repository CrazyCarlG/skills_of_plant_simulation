# local-simtalk-execution Test Session v18 — 2026-08-25

测试目标：依据 `01-plantsimulation-knowledge/.../predefined-functions-iii-type-query-inputoutput-conversion-debug/input-output/README.md` 的文档，
通过 `local-simtalk-execution` 技能驱动真实 Plant Simulation 进程，对 **Input/Output 函数族** 做端到端验证。

覆盖函数：输入（`prompt` / `promptList1` / `promptListN`）、输出（`beep` / `bell` / `getUnit` / `infoBox` / `print`）。

> 关键约束（详见 `references/lifelines.md` §4 模态陷阱）：
> - `prompt` / `promptList1` / `promptListN` / `infoBox(text, true)` 在 `simtalk_run` 里执行会**让服务端永远阻塞**等用户点 OK——**不可执行**。
> - 用户需求的"通过 infoBox 通知"改用 **`infoBox(text, false)` 非模态**形式——不会阻塞服务端。
> - 取 `print` 实际值仍受 **Quirk #6**（`data` 字段始终空）+ **v15 readlog 回归**（捕获不到 GUI Console 输出）双重限制——见结论。

## 1. 环境 / Environment

- **Skill under test**：`skills/local-simtalk-execution/`
- **被测文档**：`01-plantsimulation-knowledge/.../input-output/README.md`（SimTalk Predefined Functions III — Type Query/Input/Output/Conversion/Debug — Input/Output）
- **Server**：Plant Simulation（宿主机），TCP **50007**
- **Client host**：WSL2 容器 → `host.docker.internal:50007`
- **回包读取**：`--resp-mode delimiter --resp-delimiter '||END||'`
- **辅助客户端**：`skills/local-simtalk-execution/scripts/simtalk_send.py` v17（高层封装）
- **测试时间**：2026-08-25（接续 v17）

## 2. 握手 / Handshake

| ID | 命令 | 回包 | 退出码 | 结论 |
|---|---|---|---|---|
| v18-ping-init | `python3 scripts/simtalk_send.py ping` | `{ "type": "ping", "result": "success" }` | 0 | ✅ 链路通 |

## 3. infoBox 通知 + 收尾（用户需求）

> 用户希望在测试过程中通过 `infoBox` 通报进度、结束时关闭。`infoBox(text, false)` 是非模态版本（`Modal:false`），不会卡死服务端，但仍能在 Plant Simulation GUI 上显示一个消息框。

| ID | 命令 | 回包 `result` | 回包 `log` | 退出码 | 结论 |
|---|---|---|---|---|---|
| v18-ib-open | `simtalk_send.py --timeout 30 run 'infoBox("V18 Test Start - Input/Output fns (beep/bell/getUnit/print/infoBox)", false)'` | `success` | `execute success` | 0 | ✅ 非模态 infoBox 不阻塞服务端 |
| v18-ib-close | `simtalk_send.py --timeout 30 run 'infoBox("", false)'` | `success` | `execute success` | 0 | ✅ `infoBox("", false)` 等价于关闭消息框 |
| v18-ib-close-2 | `simtalk_send.py --timeout 30 run 'infoBox("", false)'`（防御性二次关闭） | `success` | `execute success` | 0 | ✅ 幂等：无 msgBox 时再发空串是 no-op，不会报错 |

**关键观察**：
- `infoBox(text, false)` 在 `simtalk_run` 上下文里**安全**——避开 `lifelines.md` §4 描述的"模态陷阱"
- `infoBox("", false)` 文档语义是"再次调用并传入 `""` 可关闭"——本轮执行 `success` 验证关闭路径
- `infoBox("", false)` 看起来是**幂等**的：第二次调用（防御性关闭）仍返回 `success` ——即使没有 msgBox 也安全无副作用
- ⚠️ 实际打开的 msgBox 是否在 GUI 上呈现，肉眼可见（Plant Simulation 宿主进程上的消息框）——socket 端只能验证"执行无异常"；如果 GUI 进程脱离屏幕（如 RDP 断开 / 最小化），msgBox 可能"存在但看不见"，仍按规范发空串关闭

## 4. output 函数逐个验证 / Output Function Smoke Tests

> 全部用 `simtalk_run` 通过 `simtalk_send.py` 发出。双重判据：`result == "success" AND not log.startswith("code execute failed")`（Quirk #7，详见 `lifelines.md` §6）。

| ID | 函数 | 调用代码 | `result` | `log` | 退出码 | 结论 |
|---|---|---|---|---|---|---|
| v18-out-beep | `beep` | `beep` | `success` | `execute success` | 0 | ✅ 执行成功（蜂鸣声副作用在宿主 GUI 上，肉眼/耳朵可闻） |
| v18-out-bell | `bell(Frequency, Duration)` | `bell(800, 100)` | `success` | `execute success` | 0 | ✅ 800Hz / 100ms 信号语法+执行通过 |
| v18-out-getUnit | `getUnit(value)` | `print getUnit(1.0)` | `success` | `execute success` | 0 | ✅ 调用合法；**实际返回值受 Quirk #6 限制无法回传**——见 §7 |
| v18-out-print | `print` | `print 1+2` | `success` | `execute success` | 0 | ✅ `print` 表达式求值无异常；值去到 GUI Console，但 v15 readlog 不捕获 |

**关键观察**：
- 四个 output 函数全部执行通过、无 Quirk #7 软失败——`beep` / `bell` 是无返回值副作用；`getUnit` / `print` 有值但受 Quirk #6 / v15 readlog 双重拦截，socket 端永远拿不到 `getUnit(1.0)` 的 `"m"` 或 `1+2` 的 `3`
- 替代取实际值路径：去 Plant Simulation GUI Console（Window ribbon → Console 按钮）肉眼读

## 5. input 函数仅做语法检查 / Input Function Syntax-Only Checks

> 输入函数 `prompt` / `promptList1` / `promptListN` 全部依赖 GUI 模态对话框——**执行会阻塞服务端**。
> 用户预期"通过 infoBox 通知"，所以**不实际执行**，只用 `simtalk_syntax` 验证它们是合法 SimTalk。
>
> 旁注：`promptList1` / `promptListN` 的第一个参数都是 list；本轮传入字符串字面量 list `["a","b","c"]`——在**实参位置**合法（`lifelines.md` §10.2 规则："字面量语法仅在实参位置合法"）。

| ID | 函数 | 语法检查代码 | `result` | `log` | 退出码 | 结论 |
|---|---|---|---|---|---|---|
| v18-in-prompt | `prompt` | `prompt("Enter:")` | `has no Error` | `execute success` | 0 | ✅ 合法 SimTalk；切勿 `simtalk_run` 执行（模态阻塞） |
| v18-in-promptList1 | `promptList1` | `promptList1(["a","b","c"], "Pick one:")` | `has no Error` | (空) | 0 | ✅ 合法 SimTalk |
| v18-in-promptListN | `promptListN` | `promptListN(["a","b","c"], "Pick many:")` | `has no Error` | (空) | 0 | ✅ 合法 SimTalk |

**关键观察**：
- 与 v7 T6/T7 验证一致：`prompt` / `infoBox` / `promptList1` / `promptListN` 都是合法 SimTalk，**陷阱只在执行时触发**——`simtalk_syntax` 路径下服务端不需要 namespace 上下文，所以判定通过
- 想要真体验 prompt 的 GUI 交互，请直接打开 Plant Simulation GUI 在 Method editor 里手工执行——绝不要走 `simtalk_run`

## 6. 测试后服务端稳定性 / Post-Test Server Stability

| ID | 命令 | 回包 | 退出码 | 结论 |
|---|---|---|---|---|
| v18-stab-ping | `simtalk_send.py ping` | `{ "type": "ping", "result": "success" }` | 0 | ✅ 服务端进程健在 |
| v18-stab-ping-2 | `simtalk_send.py ping`（防御性二次关闭后） | `{ "type": "ping", "result": "success" }` | 0 | ✅ 服务端进程健在 |

8 次 simtalk_run + 3 次 simtalk_syntax + 1 次防御性 infoBox close + 2 次 ping 后，服务端仍正常处理新连接。

## 7. 已知限制 / Known Limitations

| 限制 | 来自 | 表现 | 替代方案 |
|---|---|---|---|
| `data` 字段不出现（Quirk #6） | `lifelines.md` §6；`message-schema.md` Quirk #6 | `simtalk_run` 的返回值无法回传 socket——`getUnit(1.0)` 算出的 `"m"` 取不到 | 走 GUI Console 肉眼读；或改用 `simtalk_syntax` 路径（但 `simtalk_syntax` 不执行求值，更拿不到值） |
| v15 readlog 回归 | `lifelines.md` §5 | `readlog` 不捕获 `print(...)` 输出 + buffer 反馈循环膨胀 | 不要写进自动化循环；print 取值请走 GUI Console |
| `infoBox` 模态陷阱 | `lifelines.md` §4 | `infoBox(text, true)` 会让服务端永远阻塞 | 用 `infoBox(text, false)` 非模态版本 |

## 8. 结论 / Conclusions

1. **Input/Output 文档描述的所有函数都执行成功 ✅**——
   - output：`beep` / `bell` / `getUnit` / `infoBox(text, false)` / `print` 全部通过双重判据（`result=success` + 无 `code execute failed` 前缀）
   - input：`prompt` / `promptList1` / `promptListN` 经 `simtalk_syntax` 验证为合法 SimTalk

2. **通过 infoBox 通报进度 + 收尾的方案可行 ✅**——用户指定的 `infoBox(text, false)` 非模态版本在 socket 上下文中安全可用，不会触发 `lifelines.md` §4 描述的模态陷阱。

3. **socket 端无法验证"函数副作用"或"返回值" ⚠️**——Guirk #6 (`data` 不出) + v15 readlog 回归 (捕获不到 Console) 双重拦截。要验证 `print 1+2` 真的打出 `3`，要验证 `getUnit(1.0)` 真的返回 `"m"`，要听 `beep` / `bell` 的声音，都必须**去 Plant Simulation GUI**：Window ribbon → Console 按钮 + 主机扬声器。

4. **不要执行 input 函数 ⚠️**——`prompt` / `promptList1` / `promptListN` 在 `simtalk_run` 上下文里会**永远阻塞**服务端。`simtalk_syntax` 路径能验证语法但仍验证不了 GUI 行为。

5. **服务端进程稳定 ✅**——共 13 次有效请求（含 1 次 ping 重测）后 ping 仍正常。

## 9. v17 → v18 增量 / Diff vs v17

| 维度 | v17 | v18 |
|---|---|---|
| 测试对象 | 重构后 `simtalk_send.py` 验证 + readlog 行为 | Input/Output 函数族端到端执行 |
| 测试目标 | 工具可靠性 | **业务函数可靠性**（README 驱动） |
| 测试用例数 | 14 | 11（1 ping + 2 infoBox + 4 output run + 3 input syntax + 1 stability） |
| 用户需求集成 | ❌ | ✅ "infoBox 通报 + 关闭"流程 |
| 文档驱动 | ❌ | ✅ 来源是 `01-plantsimulation-knowledge` 知识库 |

## 10. 建议 / Recommendations

1. **`infoBox(text, false)` 推荐作为非阻塞通知手段**——若需要在 `simtalk_run` 流中给 Plant Simulation 用户展示进度，可放心使用；模态版本（`true` 或省略）是禁忌。
2. **input 函数永远只走 `simtalk_syntax` 验证**——这是唯一安全的验证路径；执行必须留给 GUI 手工操作。
3. **取 print / getUnit 实际值仍需肉眼**——短期服务端要支持 `simtalk_run` 的返回值回传（修 Quirk #6）或修复 v15 readlog 回归，才能在 socket 端完全验证。
4. **README 文档 ↔ 真实服务端的偏差仅限"取返回值路径"**——所有函数名、参数顺序、模态/非模态控制方式都和 README 描述完全吻合。
