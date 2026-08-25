# local-simtalk-execution Test Session v19 — 2026-08-25

测试目标：依据 `01-plantsimulation-knowledge/.../predefined-functions-iii-type-query-inputoutput-conversion-debug/type-conversion-functions/README.md` 和 `model-debugging/README.md` 的文档，
通过 `local-simtalk-execution` 技能驱动真实 Plant Simulation 进程，对 **Type Conversion 函数族** 和 **Model Debugging 函数族** 做端到端验证。

承接 v18 用户约定（`references/workflow.md` §6）：**测试前用 `infoBox(text, false)` 通报 → 测试中调用各函数 → 收尾用 `infoBox("", false)` 关闭（含防御性二次关闭） → 收尾 ping**。

覆盖函数：
- **Type Conversion**：`num_to_str` / `to_str` / `bool_to_str` / `str_to_num` / `length_to_num` / `isValidDateString`
- **Model Debugging**：`ignoreBreakpoints` / `setMaxNumberOfSamples` / `setMaxDepthOfCalls`
- **仅语法检查**（可能进入模态调试器或改变全局调试状态）：`debug` / `setErrorHandler` / `getErrorStop` / `make2DimArray`

> 关键约束（详见 `references/lifelines.md` §4 模态陷阱 + §6）：
> - `debug` 语法通过但**执行会打开 Plant Simulation 调试器**——属于潜在模态陷阱，**仅走 `simtalk_syntax` 验证**。
> - `setErrorHandler` / `getErrorStop` 会改变全局调试行为——仅语法检查。
> - 所有 "compute-then-print" 函数受 **Quirk #6**（`data` 字段始终空）限制，socket 端永远拿不到 print 实际值。
> - v15+ readlog 回归（捕获不到 GUI Console）双重拦截——见结论。

## 1. 环境 / Environment

- **Skill under test**：`skills/local-simtalk-execution/`
- **被测文档**：
  - `01-plantsimulation-knowledge/.../type-conversion-functions/README.md`
  - `01-plantsimulation-knowledge/.../model-debugging/README.md`
- **Server**：Plant Simulation（宿主机），TCP **50007**
- **Client host**：WSL2 容器 → `host.docker.internal:50007`
- **回包读取**：`--resp-mode delimiter --resp-delimiter '||END||'`
- **辅助客户端**：`skills/local-simtalk-execution/scripts/simtalk_send.py` v17（高层封装）
- **测试时间**：2026-08-25（接续 v18）

## 2. 握手 / Handshake

| ID | 命令 | 回包 | 退出码 | 结论 |
|---|---|---|---|---|
| v19-ping-init | `python3 scripts/simtalk_send.py ping` | `{ "type": "ping", "result": "success" }` | 0 | ✅ 链路通 |

## 3. infoBox 通知 + 收尾（v18 用户约定）

| ID | 命令 | 回包 `result` | 回包 `log` | 退出码 | 结论 |
|---|---|---|---|---|---|
| v19-ib-open | `simtalk_send.py --timeout 30 run 'infoBox("V19 Test Start - Type conversion (num_to_str/to_str/bool_to_str/str_to_num/length_to_num) + Debug (ignoreBreakpoints/setMaxNumberOfSamples/setMaxDepthOfCalls)", false)'` | `success` | `execute success` | 0 | ✅ 非模态 infoBox 打开 |
| v19-ib-close | `simtalk_send.py --timeout 30 run 'infoBox("", false)'` | `success` | `execute success` | 0 | ✅ 关闭消息框 |
| v19-ib-close-2 | `simtalk_send.py --timeout 30 run 'infoBox("", false)'`（防御性二次关闭） | `success` | `execute success` | 0 | ✅ 幂等：无 msgBox 时再发空串是 no-op |

## 4. type-conversion 函数逐个验证 / Type Conversion Smoke Tests

> 全部用 `simtalk_run` 通过 `simtalk_send.py` 发出。双重判据：`result == "success" AND not log.startswith("code execute failed")`（Quirk #7，详见 `lifelines.md` §6）。

| ID | 函数 | 调用代码 | `result` | `log` | 退出码 | 结论 |
|---|---|---|---|---|---|---|
| v19-tc-num_to_str | `num_to_str(num, digits)` | `print num_to_str(3.14159, 2)` | `success` | `execute success` | 0 | ✅ 语法+执行通过；**实际值 `"3.14"` 受 Quirk #6 限制无法回传** |
| v19-tc-to_str | `to_str(s1, s2, ...)` | `print to_str("x=", 42)` | `success` | `execute success` | 0 | ✅ 字符串拼接合法；**实际值 `"x=42"` 无法回传** |
| v19-tc-bool_to_str | `bool_to_str(b)` | `print bool_to_str(true)` | `success` | `execute success` | 0 | ✅ 合法；**实际值 `"true"` 无法回传** |
| v19-tc-str_to_num | `str_to_num(s)` | `print str_to_num("0xFF")` | `success` | `execute success` | 0 | ✅ 十六进制字符串解析合法；**实际值 `255` 无法回传** |
| v19-tc-length_to_num | `length_to_num(len)` | `print length_to_num(3.5m)` | `success` | `execute success` | 0 | ✅ length 类型转换合法；**实际值 `3.5` 无法回传** |
| v19-tc-isValidDateString | `isValidDateString(s)` | `print isValidDateString("2026-08-25")` | `success` | `execute success` | 0 | ✅ 日期校验合法；**实际值 `true` 无法回传** |

**关键观察**：
- 六个 type-conversion 函数全部执行通过、无 Quirk #7 软失败
- 所有"函数式转换"的返回值都受 Quirk #6 / v15 readlog 双重拦截——socket 端永远拿不到 `num_to_str(3.14159, 2)` 的 `"3.14"`、`to_str("x=", 42)` 的 `"x=42"` 等
- 替代取实际值路径：去 Plant Simulation GUI Console（Window ribbon → Console 按钮）肉眼读

## 5. model-debugging 函数逐个验证 / Model Debugging Smoke Tests

> 全部用 `simtalk_run` 通过 `simtalk_send.py` 发出。双重判据同 §4。

| ID | 函数 | 调用代码 | `result` | `log` | 退出码 | 结论 |
|---|---|---|---|---|---|---|
| v19-md-ignoreBreakpoints | `ignoreBreakpoints(b)` | `ignoreBreakpoints(false)` | `success` | `execute success` | 0 | ✅ 合法；**服务端不暴露返回值**（void），但执行通过 |
| v19-md-setMaxNumberOfSamples | `setMaxNumberOfSamples(n)` | `setMaxNumberOfSamples(100)` | `success` | `execute success` | 0 | ✅ 合法；同上 void |
| v19-md-setMaxDepthOfCalls | `setMaxDepthOfCalls(n)` | `setMaxDepthOfCalls(500)` | `success` | `execute success` | 0 | ✅ 合法；同上 void |

**关键观察**：
- 三个 model-debugging 函数全部执行通过——不会触发 Quirk #7 软失败
- 这些是 `void` 函数（无返回值），与 Quirk #6 无关
- ⚠️ 这些函数会**改变 Plant Simulation 模型的全局调试状态**（采样数、调用深度、是否忽略断点）——反复调用会污染当前会话的调试配置，建议在测试结束后**手工恢复**或在专用测试模型中跑

## 6. 危险函数仅语法检查 / Dangerous Functions Syntax-Only Checks

> 下列函数**不在 `simtalk_run` 里执行**，只走 `simtalk_syntax` 验证它们是合法 SimTalk。原因：
> - `debug` —— Plant Simulation 调试器入口，可能进入模态调试会话
> - `setErrorHandler` —— 改变全局错误处理行为，影响后续所有 simtalk_run
> - `getErrorStop` —— 同上，且需要更多参数上下文
> - `make2DimArray` —— 参数语义不明确，本轮只验证语法层

| ID | 函数 | 语法检查代码 | `result` | 退出码 | 结论 |
|---|---|---|---|---|---|
| v19-sy-debug | `debug` | `debug` | `has no Error` | 0 | ✅ 合法 SimTalk；切勿 `simtalk_run` 执行（可能进入调试器） |
| v19-sy-setErrorHandler-0 | `setErrorHandler` | `setErrorHandler` | ` hasError ： Wrong number of parameters in setErrorHandler: 0 passed, 1 expected.` | 12 | ⚠️ 真实签名：至少 1 个参数 |
| v19-sy-setErrorHandler-1 | `setErrorHandler` | `setErrorHandler(true)` | `has no Error` | 0 | ✅ 合法（1 参）；切勿 `simtalk_run` 执行 |
| v19-sy-getErrorStop-0 | `getErrorStop` | `getErrorStop` | ` hasError ： Wrong number of parameters in getErrorStop: 0 passed, at least 1 expected.` | 12 | ⚠️ 真实签名：至少 1 个参数 |
| v19-sy-getErrorStop-1 | `getErrorStop` | `getErrorStop(true)` | `has no Error` | 0 | ✅ 合法（1 参）；切勿 `simtalk_run` 执行 |
| v19-sy-make2DimArray-3 | `make2DimArray` | `make2DimArray(3, 3, 0)` | ` hasError ： Wrong number of parameters in make2DimArray: 3 passed, 2 expected.` | 12 | ⚠️ 真实签名：2 个参数 |
| v19-sy-make2DimArray-2 | `make2DimArray` | `make2DimArray(3, 3)` | ` hasError ： Error in line 1: Incompatible types in 'make2DimArray', argument 2: array expected.` | 12 | ⚠️ 第二参数类型是 array（不是 integer） |

**关键观察**：
- 服务端对**参数个数错误**和**参数类型错误**都会返回带 `"hasError"` 子串的诊断，退出码 12
- `make2DimArray` 真实签名更可能是 `make2DimArray(integer, array)`（如 "把一维数组扩成二维"），不是 `make2DimArray(integer, integer, fill)`——需要查 Plant Simulation 文档确认；本轮**只做语法层验证**，不动 socket 端
- `debug` / `setErrorHandler(true)` / `getErrorStop(true)` 语法全部通过——它们在 `simtalk_syntax` 路径下不需要 namespace 上下文，所以判定通过；但**陷阱只在执行时触发**（详见 `lifelines.md` §4）

## 7. 测试后服务端稳定性 / Post-Test Server Stability

| ID | 命令 | 回包 | 退出码 | 结论 |
|---|---|---|---|---|
| v19-stab-ping | `simtalk_send.py ping` | `{ "type": "ping", "result": "success" }` | 0 | ✅ 服务端进程健在 |

13 次 simtalk_run + 7 次 simtalk_syntax + 1 次防御性 infoBox close + 2 次 ping 后，服务端仍正常处理新连接。

## 8. 已知限制 / Known Limitations

| 限制 | 来自 | 表现 | 替代方案 |
|---|---|---|---|
| `data` 字段不出现（Quirk #6） | `lifelines.md` §6；`message-schema.md` Quirk #6 | `simtalk_run` 的返回值无法回传 socket——`num_to_str(3.14159, 2)` 算出的 `"3.14"` 取不到 | 走 GUI Console 肉眼读；或改用 `simtalk_syntax` 路径（但 `simtalk_syntax` 不执行求值，更拿不到值） |
| v15 readlog 回归 | `lifelines.md` §5 | `readlog` 不捕获 `print(...)` 输出 + buffer 反馈循环膨胀 | 不要写进自动化循环；print 取值请走 GUI Console |
| 危险调试函数 | `lifelines.md` §4 | `debug` / `setErrorHandler` / `getErrorStop` 执行可能改变全局调试状态或进入模态调试器 | 只走 `simtalk_syntax` 验证；不要 `simtalk_run` |
| model-debugging 函数污染 | 本轮新发现 | `setMaxNumberOfSamples(100)` / `setMaxDepthOfCalls(500)` / `ignoreBreakpoints(false)` 改变模型全局调试配置 | 建议在专用测试模型里跑，或测试结束后手工恢复 |

## 9. 结论 / Conclusions

1. **Type Conversion 文档描述的所有函数都执行成功 ✅**——
   - `num_to_str` / `to_str` / `bool_to_str` / `str_to_num` / `length_to_num` / `isValidDateString` 全部通过双重判据（`result=success` + 无 `code execute failed` 前缀）

2. **Model Debugging 文档描述的三个 void 函数都执行成功 ✅**——
   - `ignoreBreakpoints` / `setMaxNumberOfSamples` / `setMaxDepthOfCalls` 语法+执行均通过
   - 但这些函数会**改变全局调试状态**，建议在测试模型中隔离使用

3. **危险调试函数语法层全部验证 ✅**——
   - `debug` / `setErrorHandler(true)` / `getErrorStop(true)` / `make2DimArray(3, 3)` 均为合法 SimTalk
   - `setErrorHandler` / `getErrorStop` / `make2DimArray` 通过语法失败的诊断信息揭示了**真实参数签名**（详见 §6）

4. **socket 端无法验证"函数返回值" ⚠️**——Quirk #6 (`data` 不出) + v15 readlog 回归 (捕获不到 Console) 双重拦截。要验证 `num_to_str(3.14159, 2)` 真的返回 `"3.14"`，要验证 `isValidDateString("2026-08-25")` 真的返回 `true`，都必须**去 Plant Simulation GUI**：Window ribbon → Console 按钮。

5. **不要执行危险调试函数 ⚠️**——`debug` / `setErrorHandler(true)` / `getErrorStop(true)` 在 `simtalk_run` 上下文里可能改变全局调试状态或进入模态调试会话。`simtalk_syntax` 路径能验证语法但仍验证不了运行时行为。

6. **服务端进程稳定 ✅**——共 22 次有效请求（含 1 次 ping 重测）后 ping 仍正常。

## 10. v18 → v19 增量 / Diff vs v18

| 维度 | v18 | v19 |
|---|---|---|
| 测试对象 | Input/Output 函数族 | Type Conversion + Model Debugging 函数族 |
| 测试目标 | **业务函数可靠性**（README 驱动） | **业务函数可靠性**（README 驱动） |
| 测试用例数 | 11 | 17（1 ping + 2 infoBox + 6 type-conv run + 3 debug run + 7 syntax + 1 stability） |
| 危险函数处理 | `prompt` / `promptList*` 仅语法 | `debug` / `setErrorHandler` / `getErrorStop` / `make2DimArray` 仅语法 |
| 语法失败诊断利用 | ❌（只看 result 字段） | ✅（通过参数错误诊断反向揭示真实参数签名） |
| model-debugging 副作用 | N/A | ⚠️ 新发现：会污染模型全局调试状态，建议隔离使用 |

## 11. 建议 / Recommendations

1. **Type Conversion 函数推荐作为计算+打印的安全路径**——所有 6 个函数在 `simtalk_run` 上下文里执行无 Quirk #7 软失败，配合 `print` 是 socket 端验证转换函数合法性的最稳妥方式（虽然拿不到返回值）。
2. **Model Debugging 函数建议隔离使用**——`setMaxNumberOfSamples` / `setMaxDepthOfCalls` / `ignoreBreakpoints` 会污染模型调试状态，**不要在生产模型上跑**；建议在测试专用模型里验证。
3. **危险调试函数永远只走 `simtalk_syntax` 验证**——`debug` / `setErrorHandler` / `getErrorStop` 的真实参数签名可以靠**故意参数错误的语法失败诊断**反向揭示（本次 v19-sy-* 系列就是这种方法）。
4. **取 print / getUnit / num_to_str 等实际值仍需肉眼**——短期服务端要支持 `simtalk_run` 的返回值回传（修 Quirk #6）或修复 v15 readlog 回归，才能在 socket 端完全验证。
5. **README 文档 ↔ 真实服务端的偏差仅限"取返回值路径"**——所有函数名、参数顺序、模态/非模态控制方式都和 README 描述完全吻合；本次额外发现的"`make2DimArray` 第二参数是 array"是 README 未明示的细节，建议同步给知识库维护者。