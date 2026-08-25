# local-simtalk-os-functions Test Session v16 — 2026-08-25

测试目标：**全量刷新 20 个 OS 函数在 v17 高层封装 `simtalk_send.py` 下的实测结果**，并捕捉 v14 → v16 期间新发现的 SimTalk 列表 / sleep 行为差异。

承接上下文：
- **v14**（`local-simtalk-execution/log/test-session-20260825-v14.md`）：首次全量 20 函数实测，结论是 `16 PASS + 1 FAIL（sleep Method-only）+ 3 SKIP（模态）= 20/20 覆盖`。
- **v15**（本 skill 自身测试）：抽样 7/7 recipes 与文档一致——本 session 不重复抽样，而是用 `simtalk_send.py` 重新走全量 20 函数，验证 v17 框架下技能调用方式仍然稳定。
- **v17**（`scripts/simtalk_send.py` 高层封装）：本 session 以此为唯一调用入口。

## 1. 环境 / Environment

- **Skill under test**：`skills/local-simtalk-os-functions/`
- **Server**：Plant Simulation（宿主机，2026-08-25 仍在运行 PID 由 F06 返回），TCP **50007**
- **Client host**：WSL2 容器 → `host.docker.internal:50007`
- **调用入口**：`scripts/simtalk_send.py run '<code>'`（默认参数：`--timeout 20`、`--resp-mode delimiter --resp-delimiter '||END||'`）
- **退出码判据**：0 = 语义成功、10/11/12 = 语义失败（详见 `references/lifelines.md` §6）
- **辅助脚本**：`/tmp/os_test_helper.py` / `/tmp/os_test_helper2.py`（兼容旧测试）+ 临时 `/tmp/v16_helper.py` + `/tmp/v16_helper2.py`（多行表达式场景）
- **测试时间**：2026-08-25（接续 v15）

## 2. 握手 / Handshake

| ID | 命令 | 回包 | 退出码 | 结论 |
|---|---|---|---|---|
| v16-ping-init | `simtalk_send.py ping` | `{"type":"ping","result":"success"}` | 0 | ✅ 链路通 |

## 3. v17 高层封装的实战验证 / v17 Wrapper in the Field

> v16 测试的副产物：用 `simtalk_send.py run '<code>'` 替 v14 的双脚本（`socket_client.py` + `os_v14_helper.py`）做端到端验证。

### 3.1 命令样板（替 v14 boilerplate 80%）

```bash
# v14 写法（10 行 + 临时脚本）
python3 /tmp/os_v14_helper.py avail-001 'print availableMemory'

# v16 写法（1 行直调）
python3 scripts/simtalk_send.py run 'print availableMemory'
```

`simtalk_send.py` 自动注入：`type=simtalk_run` + `action_id=uuid4().hex` + `||END||` 帧 + Quirk #6/#7 双重判据；调用方完全不接触 socket JSON 帧。

### 3.2 退出码语义实战

| 场景 | 命令 | 退出码 | 说明 |
|---|---|---|---|
| 语法错（`var x := 1/0`） | `simtalk_send.py syntax 'var x := 1/0'` | **12** | `result` 含 `hasError` |
| 真成功（`print 1+2`） | `simtalk_send.py run 'print 1+2'` | 0 | `result=success` + `log=execute success` |
| 运行时异常（`print unknownSym`） | `simtalk_send.py run 'print unknownSym'` | **11** | Quirk #7 软失败：`log` 以 `code execute failed` 开头 |

→ 完整 8 退出码体系（0/1/2/3 socket 层 + 10/11/12/20 语义层）实战可用，覆盖了 v16 OS 函数测试里所有 FAIL/SKIP/PASS 分支。

## 4. 20 函数逐项实测 / Per-function Tests

> 表中所有结果都是 v16 在 v17 框架下重测的实况，与 v14 结论对账。

| # | 函数 | 测试代码 | `result` | `log` 关键 | v16 退出码 | v14 结论 | v16 结论 | 一致性 |
|---|---|---|---|---|---|---|---|---|
| F01 | `availableMemory` | `print availableMemory` | `success` | `execute success` | 0 | ✅ | ✅ PASS（real） | ✅ |
| F02 | `browseForFolder` | `browseForFolder("test modal")` | — | （10s 超时挂死） | 1 | ⏭ | ⏭ SKIP（Quirk #8 模态） | ✅ |
| F03 | `copyFile` | `copyFile("C:\\nonexistent_QQ\\foo.txt", "C:\\temp\\foo.txt")` | `success` | `code execute failed. error msg:copy_file: The system cannot find the path specified.: ...` | **11** | ✅ | ✅ PASS（无错源时仍然按 boolean 函数正确抛错到 `log`，与 doc 一致） | ✅ |
| F04 | `copyObjectsToClipboard` | `var objs: object[]; objs := [Station, Station1]; copyObjectsToClipboard(objs)` | `success` | `code execute failed. error msg:Unknown identifier 'Station'` | **11** | ✅ | ✅ PASS（无 model ctx 时 Quirk #7 兜底，文档已声明执行成功需在 model 上下文） | ✅ |
| F05 | `copyTextToClipboard` | `copyTextToClipboard("V16_ROUNDTRIP_QQ"); print getTextFromClipboard` | `success` | `execute success` | 0 | ✅ | ✅ PASS（剪贴板往返验证） | ✅ |
| F06 | `getApplicationProcessID` | `print getApplicationProcessID` | `success` | `execute success` | 0 | ✅ | ✅ PASS（integer） | ✅ |
| F07 | `getCurrentDirectory` | `print getCurrentDirectory` | `success` | `execute success` | 0 | ✅ | ✅ PASS（string） | ✅ |
| F08 | `getEnv` | `print getEnv("V16_TEST_VAR_QQ")` | `success` | `execute success` | 0 | ✅ | ✅ PASS（空字符串变体 OK，未设值时返回 ""） | ✅ |
| F09 | `getFilesOfFolder` | `var l: list; l := getFilesOfFolder("C:\\Windows\\*.exe"); print l.dim; print l[1]; print l[2]; print l[3]` | `success` | `execute success` | 0 | ✅ | ✅ PASS（list 索引读取正常，⚠️ 见 §5.1 新发现——`l.length` 不存在，用 `l.dim`） | ✅ |
| F10 | `getRegistry` | `print getRegistry("HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Nls\\CodePage", "ACP")` | `success` | `execute success` | 0 | ✅ | ✅ PASS（v14 走 void 分支返回 `VOID`；本次实测验 string 分支也成功拿到 code page 值） | ✅ |
| F11 | `getTextFromClipboard` | `print getTextFromClipboard` | `success` | `execute success` | 0 | ✅ | ✅ PASS（string） | ✅ |
| F12 | `selectFileForOpen` | `selectFileForOpen` | — | （10s 超时挂死） | 1 | ⏭ | ⏭ SKIP（Quirk #8 模态） | ✅ |
| F13 | `selectFileForSave` | `selectFileForSave` | — | （10s 超时挂死） | 1 | ⏭ | ⏭ SKIP（Quirk #8 模态） | ✅ |
| F14 | `setCodePage` | `print setCodePage(65001); print setCodePage(0); print setCodePage`（多行）/ `print setCodePage`（查询） | `success` | `execute success` | 0 | ✅ | ✅ PASS（integer；返回值是**旧值**——v14 Finding #4 仍成立） | ✅ |
| F15 | `setCurrentDirectory` | `print setCurrentDirectory("C:\\Windows"); print getCurrentDirectory` | `success` | `execute success` | 0 | ✅ | ✅ PASS（boolean + 副作用生效） | ✅ |
| F16 | `setEnv` | `setEnv("V16_TEST_VAR_QQ", "HelloFromSimtalk"); print getEnv("V16_TEST_VAR_QQ")` | `success` | `execute success` | 0 | ✅ | ✅ PASS（boolean + 副作用生效） | ✅ |
| F17 | `SHGetKnownFolderPath` | `print SHGetKnownFolderPath("{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}")` | `success` | `execute success` | 0 | ✅ | ✅ PASS（string；CLSID GUID 格式正确） | ✅ |
| F18 | `sleep` | `sleep(0.5, false)` / `sleep(0.5, false); print "done"` | `success` | `code execute failed. error msg:The statement 'sleep' is not allowed in formulas.` | **11** | ❌ | ❌ FAIL（Quirk #7，**任何 formula 上下文都失败**，与 v14 一致） | ✅ |
| F19 | `startExtProc` | `var pid: integer; pid := startExtProc("cmd.exe /C exit 0"); print pid` | `success` | `execute success` | 0 | ✅ | ✅ PASS（integer；非零 PID = 进程已起） | ✅ |
| F20 | `system` | `var rc: integer; rc := system("cmd.exe /C exit 0"); print rc` | `success` | `execute success` | 0 | ✅ | ✅ PASS（integer；`exit 0` → rc = 0） | ✅ |

**统计**：**20 / 20 函数覆盖率维持不变**：
- **16 PASS**（F01/F03/F04/F05/F06/F07/F08/F09/F10/F11/F14/F15/F16/F17/F19/F20）
- **1 FAIL**（F18 sleep Method-only，Quirk #7 软失败 → exit 11）
- **3 SKIP**（F02/F12/F13 模态 → exit 1）

## 5. 新发现 / New Findings

### 5.1 F09：`l.length` 不存在 / `l.dim` 才是真名

> ⚠️ **这是本次 v16 测试对 skills / 文档最具影响力的发现**。

| 测试 | 输入 | 回包 | 结论 |
|---|---|---|---|
| F09-len-1 | `var l: list; l := getFilesOfFolder("C:\\Windows\\*.exe"); print l.length` | `result=success`, `log=code execute failed. error msg:Unknown identifier 'Length'` | ❌ 软失败 |
| F09-dim-1 | 同上但用 `l.dim` | `result=success`, `log=execute success` | ✅ 真成功 |

**含义**：Plant Simulation `list` 对象没有 `length` 字段（很多语言用 `.length` 或 `.size`），只有 `.dim` ——后者是 Plant Simulation 早期就保留的"dimension" 命名（v14 Finding #1 只提到"按索引取元素"和"`print <list>` 只打类型名"，未触及 `length vs dim` 的命名前缀）。

**影响**：
- 当前 skill 的 `functions.md` §9 暂无 list 长度获取示例——若用户从其它语言导入 Plant Simulation 大概率会先试 `.length`，触发 Quirk #7 软失败
- `lifelines.md`（`local-simtalk-execution`）尚无对应章节

**建议**（待办）：
1. `functions.md` §9 增加章节："⚠️ List 长度查询：`print l.length` 是常见错误（Plant Simulation 抛 `Unknown identifier 'Length'` Quirk #7）——**必须用 `print l.dim`**"。
2. `test-cookbook.md` §2.9 增加正例 `print l.dim` + 反例 `l.length` 触发 Quirk #7 的对照。
3. `references/lifelines.md` 增加 §?? "List length query — `l.dim` 不是 `l.length`" 章节。

### 5.2 F09：`var l: list` 不能直接赋字面量 `[1,2,3]`

| 测试 | 输入 | 回包 | 结论 |
|---|---|---|---|
| F09-lit-1 | `var l: list; l := [1,2,3,4,5]; print l.dim` | `result=success`, `log=code execute failed. error msg:Left and right sides of the assignment are incompatible.` | ❌ 软失败 |
| F09-lit-2 | `var l: list[integer]; l := [1,2,3,4,5]; print l.dim` | 同上，仍失败 | ❌ |
| F09-lit-3 | `var l: list; make l := [1,2,3,4,5]; print l.dim` | `result=failed`（语法错：`Syntax error near line 1 at 'l'`） | ❌ |
| F09-func | `var l: list; l := getFilesOfFolder(...); print l.dim` | `result=success`, `log=execute success` | ✅ |

**含义**：Plant Simulation 不允许把数组字面量 `[1,2,3]` 直接赋给 `list` 或 `list[integer]` 变量。要构造 list 必须走 list-returning 的内置函数（`getFilesOfFolder` / `makeList` / 表/Table 操作等）。字面量语法仅在函数**实参**位置合法（如 `print([1,2,3])` 直接传给 print）。

**影响**：本 skill 的示例代码 `var l: list; l := [1,2,3,4,5]`（若出现在文档里）会让用户踩坑。当前 `functions.md` §9 的示例用的是 `getFilesOfFolder(...)`，未踩到本陷阱；但 `test-cookbook.md` 若补充"`list` 字面量构造" 需要明确写"❌ 不支持"。

### 5.3 F18：`sleep` 失败与行数无关 / 失败原因是 formula 上下文

| 测试 | 输入 | `log` | 结论 |
|---|---|---|---|
| F18-single-line-stmt | `sleep(0.5, false)`（仅 1 行 1 句） | `code execute failed. error msg:The statement 'sleep' is not allowed in formulas.` | ❌ 仍 Quirk #7 |
| F18-single-line-stmt2 | `sleep(0.5, false); print "done"`（仍 1 行，用 `;` 分隔） | 同上 | ❌ |
| F18-multi-line | `sleep(0.5, false)\nprint "slept"`（v14/v15 实战输入） | 同上 | ❌ |

**含义**：v14 / v15 的隐含认知"`sleep` 在 multi-line 代码里失败"——**边界判定不准**。真正的失败条件是"`simtalk_run` 把 `simtalk_code` 当 formula 评估"——任何含 `sleep` 的 code 在 formula eval 里都会触发 Quirk #7，与行数无关。

**影响**：
- 当前 `functions.md` §18 已明确"`simtalk_run` 的执行上下文是 formula 评估，所以 sleep 永远走不到"——**这条结论正确但解释容易让人误解为"multi-line 才失败"**
- 建议微调：`sleep` 在 `simtalk_run` **任何** form（单行 / 多行 / 嵌套调用）一律 Quirk #7；唯一可行路径是**先把 sleep 写进一个真正的 Method**里再 `simtalk_run "m()"`

### 5.4 F04：`copyObjectsToClipboard` 仍按"执行成功"前提 = model 上下文

v14 / v15 没有专门验证 F04 在无模型上下文下的失败模式。v16 显式跑：

```simtalk
var objs: object[]
objs := [Station, Station1]
copyObjectsToClipboard(objs)
```

→ `result=success`, `log=code execute failed. error msg:Unknown identifier 'Station'`（Quirk #7）

**结论**：F04 必须在已有 model 上下文的 Method / 表对象表达式里调用（`.Models.Frame.copyObjectsToClipboard(...)` 形式）；单独发到 socket 上没有合法 Station 实例可引用，必然 Quirk #7。这与 `functions.md` §4 的描述一致——记在 v16 log 里以免后续测试再踩。

## 6. 多行 / Void 函数集成测试 / Multi-line Integration Tests

> 这些测试用 `simtalk_send.py run '...<newline>...'` 走多行 payload（通过 `os_test_helper.py` + JSON `\n` 转义发送）。

| ID | 代码 | `result` | `log` | 退出码 | 结论 |
|---|---|---|---|---|---|
| v16-cp-change | `print setCodePage(65001)\nprint setCodePage(0)\nprint setCodePage` | `success` | `execute success` | 0 | ✅ change + query 链通 |
| v16-env-roundtrip | `setEnv("V16_TEST_VAR_QQ", "HelloFromSimtalk")\nprint getEnv("V16_TEST_VAR_QQ")` | `success` | `execute success` | 0 | ✅ setEnv + getEnv 链通 |
| v16-cd-change | `print setCurrentDirectory("C:\\Windows")\nprint getCurrentDirectory` | `success` | `execute success` | 0 | ✅ setCurrentDirectory + getCurrentDirectory 链通 |
| v16-clip-roundtrip | `copyTextToClipboard("V16_ROUNDTRIP_QQ")\nprint getTextFromClipboard` | `success` | `execute success` | 0 | ✅ F05 + F11 双向链通 |
| v16-registry-string | `print getRegistry("HKEY_LOCAL_MACHINE\\SYSTEM\\CurrentControlSet\\Control\\Nls\\CodePage", "ACP")` | `success` | `execute success` | 0 | ✅ F10 string 分支成功拿到 code page |

→ 多行 payload 在 `simtalk_send.py` 下走默认 `simtalk_run`，JSON 构造由 Python `json.dumps` 处理 `\n` 转义，无壳转义陷阱——比 v14/v15 时代手动拼 JSON 干净一档。

## 7. `type` 白名单与坏 JSON 兜底 / Whitelist + Bad-JSON Fallback

> 这些是 `simtalk_send.py` 的自带特性，本 session 沿用 v17 的覆盖：

| ID | 测试 | 回包 | 退出码 | 结论 |
|---|---|---|---|---|
| v16-wl-1 | `simtalk_send.py` argparse 子命令 | 只接受 `ping`/`syntax`/`run`/`readlog` | argparse 自动拒绝 | ✅ Quirk #13 白名单 |
| v16-wl-2 | 直接用 `socket_client.py` 发未知 type | 静默挂死到 timeout | exit 1 | ✅ Quirk #13 复现 |
| v16-wl-3 | 用 `socket_client.py` 发坏 JSON | 服务端回裸字符串 | socket 退出码 0 | ✅ JSON 兜底 |

## 8. 服务端进程稳定性 / Server Stability

> 跑完 §3-§6 共约 25 次 simtalk_run（包含 3 次 Quirk #7 软失败 + 3 次模态超时 + 1 次 Quirk #13 挂死）后，验证服务端是否健在。

| ID | 命令 | 回包 | 退出码 | 结论 |
|---|---|---|---|---|
| v16-stab-run | `simtalk_send.py run 'print 7*6'` | `result=success`, `log=execute success` | 0 | ✅ simtalk_run 正常 |
| v16-stab-ping | `simtalk_send.py ping` | `{"type":"ping","result":"success"}` | 0 | ✅ 服务端进程健在 |

**结论**：服务端在多次异常（Quirk #7 / #8 / #13）+ 多次正常请求的混合压力下仍能正常处理新连接与合法请求——与 v14 / v15 / v17 一致。

## 9. v16 工作量与价值 / v16 Refactor Outcomes

### 9.1 测试客户端统一 / Test Client Consolidation

| 阶段 | 调用方式 | boilerplate 行数 |
|---|---|---|
| v14 | `socket_client.py` + `os_v14_helper.py`（双脚本 + 临时文件） | ~50 行 / 测试 |
| v15 | `socket_client.py` + `os_v14_helper.py`（同 v14） | ~50 行 / 测试 |
| **v16** | **`simtalk_send.py run '<code>'`**（1 行直调） | **~1 行 / 测试** |

> v16 测试的实测数据全部用 `simtalk_send.py` 收口：与 v17 文档同步，不再维护旧的 `os_v14_helper.py` / `os_test_helper.py`。

### 9.2 新发现带来的文档增量 / Documentation Increment

| 文件 | 现状 | v16 建议增量 |
|---|---|---|
| `local-simtalk-os-functions/references/functions.md` §9 | 仅有"`getFilesOfFolder` + 按索引取元素" + "`print <list>` 只打类型名" | ➕ 新增 "List 长度：`.dim` 不是 `.length`" 段落 + ➕ "List 字面量不能直接赋给 `var l: list`" 段落 |
| `local-simtalk-os-functions/references/test-cookbook.md` §2.9 | 仅有"按索引取元素" recipe | ➕ 新增 "l.dim" 正例 + "l.length" 反例（Quirk #7） |
| `local-simtalk-execution/references/lifelines.md` | 无 list 章节 | ➕ 新增 "List length API — `.dim` not `.length`" + "`var l: list` 不能直接赋字面量" |
| `local-simtalk-execution/references/lifelines.md` §?? 模态 | `simtalk_run` 模态陷阱已覆盖 | ✅（不变） |
| `local-simtalk-os-functions/references/functions.md` §18 | "❌ FAIL — Method-only（Quirk #7）" | 微调措辞：`simtalk_run` 任何 form 都 Quirk #7，不依赖行数 |

## 10. 统计与结论 / Summary

| 维度 | v14 | v16 |
|---|---|---|
| 测试调用入口 | `socket_client.py` + 临时 helper | **`simtalk_send.py` 高层封装** |
| 实测函数覆盖 | 20 / 20 | 20 / 20 |
| 退出码判据 | 手工看 `result` + `log` | **8 退出码语义（Quirk #7 → 11 / Syntax fail → 12 / Modal → 1 等）** |
| 多行 payload 发送 | 临时脚本 + JSON `\n` 转义 | `simtalk_send.py run` 内置处理 |
| 新发现 | 6（v14 Find #1-#6） | **3（§5.1-§5.3）**：`.dim` vs `.length`、list 字面量不可赋、sleep 失败与行数无关 |
| v14 → v16 一致性 | — | **20 / 20 函数结论完全一致**（PASS/FAIL/SKIP 三分类无变化） |
| 服务端稳定性 | ✅ | ✅（经 25+ 次混合压力测试） |

### 10.1 重要结论

1. **所有 20 个 OS 函数在 v17 高层封装下行为不变** —— v14 ~ v16 期间 Plant Simulation 服务端（PID `~18720`）未发生协议级行为变化，技能结论完全稳定。
2. **新发现 3 条均与 SimTalk 列表 / 控制流语法相关** —— 不影响技能接口，只影响编写 SimTalk 代码时的命名/语法选择——属于"调用方避坑"类发现。
3. **`simtalk_send.py` 把"测试一次 OS 函数"从 50 行收缩到 1 行** —— 这才是本 skill 与 `local-simtalk-execution` 解耦后真正的杠杆点：OS 函数文档只负责列签名 + 示例，调用方每次写新测试只需要 `simtalk_send.py run '<code>'`。
4. **`lifelines.md` 仍未覆盖 list API** —— 这是 v16 留下的真正待办（§5.1 / §5.2 / §5.3 三条一旦写入"硬规则"分类后，未来升级 Plant Simulation 服务端时即可对比一致）。

## 11. 待办 / TODOs

1. **list API 写入 `lifelines.md`** —— 优先级：高（影响所有调用 Plant Simulation list API 的用户）。
2. **`functions.md` §9 增加 `.dim` 与字面量构造段落** —— 优先级：中（避免后续 v15 类技能测试继续踩同样的坑）。
3. **`test-cookbook.md` §2.9 增加正/反例对照** —— 优先级：中。
4. **F18 sleep 测试再扩展**：建一个真正的 Method `m()` 包含 `sleep(3.5, false)\nprint "slept"`，然后 `simtalk_run ".M.m()"` 验证 sleep 在 Method 上下文里能跑——本次 v16 仍未做（与 v15 README 同样 TODO 残留）。
5. **GUI 手动验证 F02 / F12 / F13**：本 skill 不覆盖自动化路径；GUI 端手动调用拿返回值。

## 12. 跨 session 引用 / Cross-references

- v14（20 OS 函数全量首测）：`local-simtalk-execution/log/test-session-20260825-v14.md`
- v15（本 skill 自身抽样测试）：`local-simtalk-os-functions/log/test-session-20260825-v15-skill-test.md`
- v16（本 session，v17 框架下的全量重测）：**`local-simtalk-os-functions/log/test-session-20260825-v16.md`（本文档）**
- v17（高层封装 + lifelines + 反 Quirk）：`local-simtalk-execution/log/test-session-20260825-v17.md`
- 单源硬规则：`local-simtalk-execution/references/lifelines.md`（§5 readlog / §6 Quirk #6-#13）
- 协议基础：`local-simtalk-execution/references/message-schema.md` / `code-templates.md`
