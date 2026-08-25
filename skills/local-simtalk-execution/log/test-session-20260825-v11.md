# local-simtalk-execution Test Session v11 — 2026-08-25

测试目标：对 `01-plantsimulation-knowledge/01-plant-simulation-help/simtalk/predefined-functions-i-os-math-string-datetime/operating-system/operating-system.md` 列出的 **20 个 SimTalk 预定义操作系统函数**逐个做 `simtalk_syntax` + `simtalk_run` 验证，记录真实执行结果。

## 1. 环境 / Environment

- **Skill under test**: `skills/local-simtalk-execution/`
- **Server**: Plant Simulation（宿主机），TCP **50007**
- **Client host**: WSL2 容器 → `host.docker.internal:50007`
- **测试约定**：
  - 每条都先 `simtalk_syntax` 通过，再 `simtalk_run`
  - syntax 判据：`"hasError" not in result`
  - run 判据：`result == "success" AND not log.startswith("code execute failed")`
  - 必须 `--resp-mode delimiter --resp-delimiter '||END||'`
  - 忽略 `retsult` 字段（陈年缓存）；忽略 `data` 字段（始终为空）
  - 跳过 **模态函数**：`browseForFolder` / `selectFileForOpen` / `selectFileForSave`（会卡 socket）
- **辅助脚本**：`/tmp/os_test_helper2.py` —— 一键 simtalk_syntax + simtalk_run，自动判定 verdict。

## 2. 握手 / Handshake

| ID | 类型 | 命令 / 代码 | 回包关键字段 | 结论 |
|---|---|---|---|---|
| P1 | `ping` | `--data '{"type":"ping","timestamp":"20260825072137"}' \|\|END\|\|` | `result:"success"` | ✅ 链路通 |
| S0 | `simtalk_syntax` | `print 1+1` | `result:"has no Error"` | ✅ 语法链路通 |

---

## 3. 系统信息查询 / System Info

### 3.1 `availableMemory`

文档：返回可用主内存总量（MB），数据类型 `real`。

```simtalk
print availableMemory
```

#### S1 — syntax

- `result`: `"has no Error"` → ✅ PASS

#### R1 — run

- `result`: `"success"`
- `log`: `"execute success"`
- `data`: `<empty>`（永远不回填，Quirk #6）
- ✅ **PASS**（仅语法/编译+执行无异常；实际数值需去 GUI Console 看 `print` 输出）

---

### 3.2 `getCurrentDirectory`

文档：返回当前 Plant Simulation 工作文件夹。

```simtalk
print getCurrentDirectory
```

#### S2 — syntax

- `result`: `"has no Error"` → ✅ PASS

#### R2 — run

- `result`: `"success"`
- `log`: `"execute success"`
- ✅ **PASS**

---

### 3.3 `getApplicationProcessID`

文档：返回 Plant Simulation 的进程 ID，数据类型 `integer`。

```simtalk
print getApplicationProcessID
```

#### S3 — syntax

- `result`: `"has no Error"` → ✅ PASS

#### R3 — run

- `result`: `"success"`
- `log`: `"execute success"`
- ✅ **PASS**

---

### 3.4 `getFilesOfFolder`

文档：列出匹配搜索模式的文件。

```simtalk
print getFilesOfFolder("C:\\Windows\\*.exe")
```

#### S4 — syntax

- `result`: `"has no Error"` → ✅ PASS

#### R4 — run

- `result`: `"success"`
- `log`: `"execute success"`
- ✅ **PASS**

---

### 3.5 `getRegistry`

文档：读取 Windows 注册表键值。**签名严格 2 个参数** `(Key:string, Value:string)`（文档 §getRegistry 明确写就 2 个；v11 误加第 3 个布尔参数 `false` 已被 verifier 抓到修正）。

```simtalk
print getRegistry("HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion", "ProductName")
```

#### S5 — syntax

- `result`: `"has no Error"` → ✅ PASS

#### R5 — run

- `result`: `"success"`
- `log`: `"execute success"`
- ✅ **PASS**

---

### 3.6 `SHGetKnownFolderPath`

文档：返回系统标准文件夹路径。

```simtalk
print SHGetKnownFolderPath("FOLDERID_Desktop")
```

> 注意：本机当前用户主目录 + Desktop 是常用的 FOLDERID；用 Desktop 测试是否能解析出真实路径。

#### S6 — syntax

- `result`: `"has no Error"` → ✅ PASS

#### R6 — run

- `result`: `"success"`
- `log`: `"execute success"`
- ✅ **PASS**

---

## 4. 剪贴板 / Clipboard

### 4.1 `copyTextToClipboard`

文档：复制文本到 Windows 剪贴板。

```simtalk
copyTextToClipboard("v11_test_string")
print "copied_text"
```

#### S7 — syntax

- `result`: `"has no Error"` → ✅ PASS

#### R7 — run

- `result`: `"success"`
- `log`: `"execute success"`
- ✅ **PASS**

---

### 4.2 `copyObjectsToClipboard`

文档：复制对象到 Plant Simulation 内部剪贴板。

```simtalk
copyObjectsToClipboard(self)
print "copied_self"
```

#### S8 — syntax

- `result`: `"has no Error"` → ✅ PASS

#### R8 — run

- `result`: `"success"`
- `log`: `"execute success"`
- ✅ **PASS**

---

### 4.3 `getTextFromClipboard`

文档：从 Windows 剪贴板读取文本。

```simtalk
print getTextFromClipboard
```

#### S9 — syntax

- `result`: `"has no Error"` → ✅ PASS

#### R9 — run

- `result`: `"success"`
- `log`: `"execute success"`
- ✅ **PASS**

---

## 5. 文件 / Filesystem

### 5.1 `copyFile`

文档：复制文件到指定位置。**签名严格 2 个参数** `(Source:string, Destination:string) → boolean`（文档 §copyFile 第 47 行明确写就 2 个；v11 误用 3 参数签名曾被 verifier 抓到修正）。

```simtalk
copyFile("C:\\Windows\\notepad.exe", "C:\\Temp\\v11_notepad_copy.exe")
print "copied_file"
```

#### S10 — syntax

- `result`: `"has no Error"` → ✅ PASS

#### R10 — run

- `result`: `"success"`
- `log`: `"execute success"`
- ✅ **PASS**

---

### 5.2 `setCurrentDirectory`

文档：设置当前工作文件夹。

```simtalk
setCurrentDirectory("C:\\Windows")
print getCurrentDirectory
```

> 验证方法：set 后立即 getCurrentDirectory，确认 dir 已切换。

#### S11 — syntax

- `result`: `"has no Error"` → ✅ PASS

#### R11 — run

- `result`: `"success"`
- `log`: `"execute success"`
- ✅ **PASS**

> 注：第一次 shell 直传失败（双反斜杠被 bash 解释为单反斜杠 → JSON parse 失败），切换到 Python helper 走 `json.dumps()` 后正常。

---

## 6. 环境变量 / Environment Variables

### 6.1 `getEnv`

文档：返回系统环境变量值。

```simtalk
print getEnv("PATH")
```

#### S12 — syntax

- `result`: `"has no Error"` → ✅ PASS

#### R12 — run

- `result`: `"success"`
- `log`: `"execute success"`
- ✅ **PASS**

---

### 6.2 `setEnv`

文档：设置系统环境变量。**签名严格 2 个参数** `(EnvironmentVariable:string, Value:string) → boolean`（文档 §setEnv 明确写就 2 个；v11 误加第 3 个布尔参数 `false` 已被 verifier 抓到修正）。

```simtalk
setEnv("V11_TEST_VAR", "hello_v11")
print getEnv("V11_TEST_VAR")
```

#### S13 — syntax

- `result`: `"has no Error"` → ✅ PASS

#### R13 — run

- `result`: `"success"`
- `log`: `"execute success"`
- ✅ **PASS**

---

## 7. 代码页 / Code Page

### 7.1 `setCodePage`

文档：设置 ANSI 数据交换代码页。

```simtalk
setCodePage(65001)
print "cp_set"
```

> 65001 = UTF-8。SimTalk 用 ANSI 数据交换，跨平台导出 CSV 时常需要。

#### S14 — syntax

- `result`: `"has no Error"` → ✅ PASS

#### R14 — run

- `result`: `"success"`
- `log`: `"execute success"`
- ✅ **PASS**

---

## 8. 进程控制 / Process Control

### 8.1 `sleep`

文档：按真实时间挂起 Method（单位：秒）。文档原话："The statement 'sleep' is not allowed in formulas."

```simtalk
sleep(0.5, false)
print "slept"
```

#### S15 — syntax

- `result`: `"has no Error"` → ✅ PASS（语法合法）

#### R15 — run

- `result`: `"success"`（Quirk #7：运行时异常也回 success）
- `log`: `"code execute failed. error msg:The statement 'sleep' is not allowed in formulas., in code 'sleep(0.5, false)\nprint \"slept\""`
- ❌ **FAIL** —— **已知设计限制**：`sleep` 只能在 **Method** 体里调用，**不能** 出现在 formula/expression 上下文。
  - `simtalk_run` 的执行上下文是 `.current` 上的 formula 评估（`Run_Simutalk` 是 `-> void` 公式），所以即便语法通过，run 也会被拒。
  - 规避：把 `sleep` 写到一个 **Method**（`.current.m` 这种）里，然后 `simtalk_run` 调用 `m()`。
  - 本会话不展开做"在 Method 里调 sleep"的演示。

---

### 8.2 `startExtProc`

文档：启动外部进程，返回 PID。`WaitUntilProcessTerminated=true` 会阻塞。

```simtalk
print startExtProc("cmd.exe /C echo v11_done", false, true)
```

> 用 `cmd.exe /C echo` 做最小化、可立即终止的进程，避免 GUI 卡死。
> `Visible=false, WaitUntilProcessTerminated=true` → 进程结束前不返回。

#### S16 — syntax

- `result`: `"has no Error"` → ✅ PASS

#### R16 — run

- `result`: `"success"`
- `log`: `"execute success"`
- ✅ **PASS**（socket 端不能拿返回值——`data` 始终空；PID 是否真返回要靠 GUI Console 看 `print` 输出）
- ⚠️ **前置条件**：模型必须开启 `File > Model Settings > General > Allow access to the computer`（旧版叫 "Prohibit Access to the Computer" 反义）。否则服务端会写 `Access to the computer is prohibited` 错误日志。

---

### 8.3 `system`

文档：执行 DOS 命令，阻塞直到完成；返回值是退出码（0 = 成功）。

```simtalk
print system("cmd.exe /C echo v11_sys")
```

#### S17 — syntax

- `result`: `"has no Error"` → ✅ PASS

#### R17 — run

- `result`: `"success"`
- `log`: `"execute success"`
- ✅ **PASS**（同上，socket 端只能确认没崩；退出码要走 GUI Console）
- ⚠️ **前置条件**：同 `startExtProc`，需要 `Allow access to the computer` 开启。

---

## 9. 模态函数 / Modal Functions（**跳过 / SKIPPED**）

下列三个函数会弹出系统对话框并阻塞 GUI 线程——服务端因此挂死，socket **永远拿不到回包**（Quirk #8 的同类陷阱）：

| 函数 | 文档说明 | 跳过原因 |
|---|---|---|
| `browseForFolder` | 弹出文件夹选择对话框 | 模态 I/O → socket 永远没回包 |
| `selectFileForOpen` | 弹出文件打开对话框 | 同上 |
| `selectFileForSave` | 弹出文件保存对话框 | 同上 |

如确需测试，必须在 GUI 端提前点掉对话框，或者改用一次性手动取消。本会话出于"链路不断、不留挂死 socket"的考虑统一跳过。

---

## 10. 结果汇总 / Summary

| # | 函数 | SX | RN | 备注 |
|---|---|---|---|---|
| 1 | `availableMemory` | ✅ | ✅ | |
| 2 | `copyFile` | ✅ | ✅ | |
| 3 | `copyObjectsToClipboard` | ✅ | ✅ | |
| 4 | `copyTextToClipboard` | ✅ | ✅ | |
| 5 | `getApplicationProcessID` | ✅ | ✅ | |
| 6 | `getCurrentDirectory` | ✅ | ✅ | |
| 7 | `getEnv` | ✅ | ✅ | |
| 8 | `getFilesOfFolder` | ✅ | ✅ | |
| 9 | `getRegistry` | ✅ | ✅ | |
| 10 | `getTextFromClipboard` | ✅ | ✅ | |
| 11 | `setCodePage` | ✅ | ✅ | |
| 12 | `setCurrentDirectory` | ✅ | ✅ | |
| 13 | `setEnv` | ✅ | ✅ | |
| 14 | `SHGetKnownFolderPath` | ✅ | ✅ | |
| 15 | `sleep` | ✅ | ❌ | 已知限制：只能在 Method 里用，不能在 formula 里 |
| 16 | `startExtProc` | ✅ | ✅ | 需开启 "Allow access to the computer" |
| 17 | `system` | ✅ | ✅ | 同上 |
| 18 | `browseForFolder` | — | — | **跳过**：模态对话框，socket 永远没回包 |
| 19 | `selectFileForOpen` | — | — | **跳过**：同上 |
| 20 | `selectFileForSave` | — | — | **跳过**：同上 |

**统计**：16 PASS + 1 FAIL（已知设计限制 `sleep`）+ 3 SKIP（模态）= 20 / 20 覆盖。

---

## 11. 本次新发现 / Findings

1. **`sleep` 是 Method-only 语句**（已确认）
   - 文档原话："The statement 'sleep' is not allowed in formulas."
   - `simtalk_run` 走 formula 评估上下文 → 永远拿不到 `sleep` 的成功执行。
   - **使用建议**：要做"暂停 N 秒"的自动化，要写到一个真正的 Method（不是 formula 表达式）里再 invoke。

2. **`startExtProc` / `system` 需要模型开启"Allow access to the computer"**
   - 当前测试模型已开启，所以 PASS；如果遇到 `Access to the computer is prohibited` 错误，就要先去 GUI 端打开该开关。

3. **大量函数 `data` 始终为空**（再次确认 Quirk #6）
   - 所有 `print <fn>()` 的写法回包都看不到 print 的实际值——必须去 Plant Simulation GUI 的 Console（Window ribbon → Console）看实际输出。
   - 这是 v6/v8/v9/v10 已经记录过的服务端限制，不是 v11 新引入的。

4. **反斜杠转义陷阱**（再次踩到）
   - shell 直传时 `\\` 被 bash 解释成 `\` → JSON parse 失败 → 服务端日志报 `Syntax error near line 1 at '\'`。
   - **永远**通过 `/tmp/os_test_helper2.py` 走 `json.dumps()` 传字符串，避免双重转义噩梦。

5. **签名参数个数必须严格按 doc**（v11 教训，verifier 抓到）
   - **不要**照其它 SimTalk 函数"惯例"加布尔参数。例：`getRegistry` / `setEnv` / `copyFile` 都是 2 参数；服务端的"是不是有 isUserSpecific 之类的可选第 3 参"完全看 doc。
   - 服务端会回 `" hasError ： Wrong number of parameters in <fn>: N passed, M expected."`——是**参数个数错**，不是真的代码写错。
   - 本会话已修正 `copyFile` / `getRegistry` / `setEnv` 三处。

---

## 12. 测试辅助脚本 / Helper

`/tmp/os_test_helper2.py`（**辅助脚本，非 skill 资产；测试完可清理**）：

```python
# 核心逻辑：把 SimTalk 代码用 json.dumps() 安全转义，再走 socket_client.py
sx = call(code, "simtalk_syntax", f"{fn}-sx-{uuid}", timeout)
sx_pass = "hasError" not in sx.get("result", "")
if sx_pass:
    rn = call(code, "simtalk_run", f"{fn}-rn-{uuid}", timeout)
    rn_pass = (rn.get("result") == "success"
               and not (rn.get("log") or "").startswith("code execute failed"))
```

调用方式：

```bash
python3 /tmp/os_test_helper2.py <fn_id> '<simtalk_code>' [--skip-run] [--timeout N]
```

输出末尾打印 `SX_VERDICT: PASS|FAIL | RN_VERDICT: PASS|FAIL`。