# Test Cookbook — 如何实测每个 OS 函数

> 通过 `local-simtalk-execution` 把 SimTalk 代码送进本机 Plant Simulation 进程，用 v13+ `readlog` 拉回 `print(...)` 实际值，验证 OS 函数的真实行为。
>
> 完整测试日志参见 `log/README.md`（指向 `local-simtalk-execution/log/test-session-20260825-v14.md`）。

## 0. 准备 / Setup

```bash
# 默认目标（WSL2 容器 ↔ Plant Simulation 主机）
HOST=host.docker.internal
PORT=50007
```

`scripts/socket_client.py` 由 `local-simtalk-execution` 提供：
```bash
SOCKET_CLIENT="python3 /root/skills_of_plant_simulation/skills/local-simtalk-execution/scripts/socket_client.py"
```

回包读取：统一用 `--resp-mode delimiter --resp-delimiter '||END||'`（服务端不会主动关闭，`eof` 一定超时）。

## 1. 取 print 实际值的标准流程（v13+）

**为什么需要两步**：v6~v11 时代 `simtalk_run` 的 `data` 字段永远为空（Quirk #6），socket 端拿不到 `print(...)` 的值。v13 起 `readlog` 直接返回 Plant Simulation GUI Console 的 print 输出——所以需要先 `simtalk_run` 触发 print，再 `readlog` 拉回。

```bash
# Step 1: 触发 print（推荐用唯一标记，方便从 readlog 输出里定位）
UNIQUE="MARKER_$(date +%s%N | tail -c 8)"
$SOCKET_CLIENT \
  --host $HOST --port $PORT --timeout 30 \
  --data "{\"type\":\"simtalk_run\",\"action_id\":\"step1-$UNIQUE\",\"simtalk_code\":\"print UNIQUE_MARKER_QQ\\nreturn 1+1\"}||END||" \
  --resp-mode delimiter --resp-delimiter '||END||'

# Step 2: 拉 readlog（v13+ buffer 包含 UNIQUE_MARKER_QQ 行）
$SOCKET_CLIENT \
  --host $HOST --port $PORT --timeout 10 \
  --data "{\"type\":\"readlog\",\"action_id\":\"step2-$UNIQUE\"}||END||" \
  --resp-mode delimiter --resp-delimiter '||END||'
# 回包 log 字段："2026-08-25 10:30:01: Log file opened! ...\n2026-08-25 10:30:05: UNIQUE_MARKER_QQ\n"
#                                                ^^^^^^^^ 用唯一标记定位行号最稳
```

**注意**：
- `simtalk_run` 的 `data` 字段依然永远为空（Quirk #6 不变）
- print 表达式求值结果（如 `42+41` → `83`）会作为单独一行出现在 readlog 的 `log` 里
- readlog buffer 在回包后清空——同一 session 内连续多次 readlog 不会重复历史
- v13 之前 Quirk #11 / Quirk #12 已修复，可以放心在循环里调用 readlog

## 2. 20 函数的实测脚本模板

> 每个模板都可以直接复制。把 `<id>` 换成 uuid4/hex 即可。
>
> JSON 内的换行必须写成 `\n`，不能直接放真换行。

### 2.1 `availableMemory` ✅

```bash
$SOCKET_CLIENT --host $HOST --port $PORT --timeout 10 \
  --data '{"type":"simtalk_run","action_id":"avail-001","simtalk_code":"print availableMemory"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
# 紧接 readlog：log 字段第一行（去掉 Log file opened 头）是实际值
```

### 2.2 `browseForFolder` ⏭ SKIP

```bash
# ⚠️ 不要在 socket 端调用——模态对话框阻塞 GUI 线程，server hang
# 文档行为是弹出 Windows 文件夹选择框，返回 string
```

### 2.3 `copyFile` ✅（需 "Allow access to the computer"）

```bash
$SOCKET_CLIENT --host $HOST --port $PORT --timeout 10 \
  --data '{"type":"simtalk_run","action_id":"copyfile-001","simtalk_code":"print copyFile(\"C:\\\\Windows\\\\notepad.exe\", \"C:\\\\Temp\\\\v14_notepad_copy.exe\")"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
# readlog 期望: true
```

### 2.4 `copyObjectsToClipboard` ✅

```bash
$SOCKET_CLIENT --host $HOST --port $PORT --timeout 10 \
  --data '{"type":"simtalk_run","action_id":"copyobj-001","simtalk_code":"copyObjectsToClipboard(self)\nprint \"OK_COPIED\""}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
# readlog 期望: OK_COPIED（执行成功无返回值）
```

### 2.5 `copyTextToClipboard` ✅

```bash
$SOCKET_CLIENT --host $HOST --port $PORT --timeout 10 \
  --data '{"type":"simtalk_run","action_id":"copytext-001","simtalk_code":"copyTextToClipboard(\"v14_test_string_42\")\nprint getTextFromClipboard"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
# readlog 期望: v14_test_string_42（间接验证 copy 成功）
```

### 2.6 `getApplicationProcessID` ✅

```bash
$SOCKET_CLIENT --host $HOST --port $PORT --timeout 10 \
  --data '{"type":"simtalk_run","action_id":"getpid-001","simtalk_code":"print getApplicationProcessID"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
# readlog 期望: <整数，如 18720>
```

### 2.7 `getCurrentDirectory` ✅

```bash
$SOCKET_CLIENT --host $HOST --port $PORT --timeout 10 \
  --data '{"type":"simtalk_run","action_id":"getcwd-001","simtalk_code":"print getCurrentDirectory"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
# readlog 期望: 当前工作目录（Plant Simulation 启动时的 -cwd）
```

### 2.8 `getEnv` ✅

```bash
$SOCKET_CLIENT --host $HOST --port $PORT --timeout 10 \
  --data '{"type":"simtalk_run","action_id":"getenv-001","simtalk_code":"print getEnv(\"PATH\")"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
# readlog 期望: 完整 PATH 环境变量字符串（700+ 字符）
```

### 2.9 `getFilesOfFolder` ✅（按索引取元素）

```bash
# ⚠️ print <list> 只打类型名，必须按索引取元素
$SOCKET_CLIENT --host $HOST --port $PORT --timeout 10 \
  --data '{"type":"simtalk_run","action_id":"getfiles-001","simtalk_code":"var l: list\nl := getFilesOfFolder(\"C:\\\\Windows\\\\*.exe\")\nprint l[1]\nprint l[2]\nprint l[3]"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
# readlog 期望: bfsvc.exe / explorer.exe / HelpPane.exe（按字典序的前 3 个）
```

**List 长度查询正/反例（v16 新增）**：

```bash
# ✅ 正例：l.dim 返回 list 元素数量
$SOCKET_CLIENT --host $HOST --port $PORT --timeout 10 \
  --data '{"type":"simtalk_run","action_id":"getfiles-len-ok","simtalk_code":"var l: list\nl := getFilesOfFolder(\"C:\\\\Windows\\\\*.exe\")\nprint l.dim"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
# readlog 期望: <整数，如 50+>（C:\Windows 下 *.exe 实际数量）

# ❌ 反例：l.length 触发 Quirk #7 软失败（其它语言常见命名陷阱）
$SOCKET_CLIENT --host $HOST --port $PORT --timeout 10 \
  --data '{"type":"simtalk_run","action_id":"getfiles-len-fail","simtalk_code":"var l: list\nl := getFilesOfFolder(\"C:\\\\Windows\\\\*.exe\")\nprint l.length"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
# 期望: result:"success" 但 log:"code execute failed. error msg:Unknown identifier 'Length'"
# 双重判据（详见 local-simtalk-execution/references/lifelines.md §6）抓住：RN 实际是 FAIL
```

**List 字面量赋值的反例（v16 新增）**：

```bash
# ❌ var l: list 不能直接赋数组字面量
$SOCKET_CLIENT --host $HOST --port $PORT --timeout 10 \
  --data '{"type":"simtalk_run","action_id":"getfiles-lit-fail","simtalk_code":"var l: list\nl := [1,2,3,4,5]\nprint l.dim"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
# 期望: result:"success" 但 log:"code execute failed. error msg:Left and right sides of the assignment are incompatible."
# 替代：var l: list; l := getFilesOfFolder(...)（走 list-returning 函数）
```

### 2.10 `getRegistry` ✅

```bash
$SOCKET_CLIENT --host $HOST --port $PORT --timeout 10 \
  --data '{"type":"simtalk_run","action_id":"getreg-001","simtalk_code":"print getRegistry(\"HKLM\\\\SOFTWARE\\\\Microsoft\\\\Windows NT\\\\CurrentVersion\", \"ProductName\")"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
# readlog 期望: VOID（当前 Windows 版本该键 ProductName 不存在；三态：void/int/str）
```

### 2.11 `getTextFromClipboard` ✅

```bash
$SOCKET_CLIENT --host $HOST --port $PORT --timeout 10 \
  --data '{"type":"simtalk_run","action_id":"getclip-001","simtalk_code":"copyTextToClipboard(\"V14_GETTEST\")\nprint getTextFromClipboard"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
# readlog 期望: V14_GETTEST
```

### 2.12 `selectFileForOpen` ⏭ SKIP

```bash
# ⚠️ 模态对话框，server hang，不要 socket 端调用
```

### 2.13 `selectFileForSave` ⏭ SKIP

```bash
# ⚠️ 模态对话框，server hang，不要 socket 端调用
```

### 2.14 `setCodePage` ✅（**返回前值**）

```bash
$SOCKET_CLIENT --host $HOST --port $PORT --timeout 10 \
  --data '{"type":"simtalk_run","action_id":"setcp-001","simtalk_code":"print setCodePage(65001)"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
# readlog 期望: <前一个 code page，如 0>
# ⚠️ 返回的是设置前的旧值，不是新值
```

### 2.15 `setCurrentDirectory` ✅（需 "Allow access to the computer"）

```bash
$SOCKET_CLIENT --host $HOST --port $PORT --timeout 10 \
  --data '{"type":"simtalk_run","action_id":"setcwd-001","simtalk_code":"print setCurrentDirectory(\"C:\\\\Windows\")\nprint getCurrentDirectory"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
# readlog 期望: true（设置成功） + C:\Windows（验证生效）
```

### 2.16 `setEnv` ✅（需 "Allow access to the computer"）

```bash
$SOCKET_CLIENT --host $HOST --port $PORT --timeout 10 \
  --data '{"type":"simtalk_run","action_id":"setenv-001","simtalk_code":"setEnv(\"V14_TEST_VAR\", \"hello_v14\")\nprint getEnv(\"V14_TEST_VAR\")"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
# readlog 期望: hello_v14（间接验证 set 生效）
```

### 2.17 `SHGetKnownFolderPath` ✅（**必须 CLSID GUID**）

```bash
# ⚠️ 参数必须是 "{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}" GUID 格式
# 误用 "FOLDERID_Desktop" 符号名会报 Invalid class string
$SOCKET_CLIENT --host $HOST --port $PORT --timeout 10 \
  --data '{"type":"simtalk_run","action_id":"shgetk-001","simtalk_code":"print SHGetKnownFolderPath(\"{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}\")"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
# readlog 期望: C:\Users\<user>\Desktop
```

### 2.18 `sleep` ❌ FAIL（Method-only）

```bash
# ⚠️ simtalk_run 上下文是 formula 评估，sleep 不能用
$SOCKET_CLIENT --host $HOST --port $PORT --timeout 10 \
  --data '{"type":"simtalk_run","action_id":"sleep-001","simtalk_code":"sleep(0.5, false)\nprint \"slept\""}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
# 期望: result:"success" 但 log:"code execute failed. error msg:The statement 'sleep' is not allowed in formulas."
# 规避：把 sleep 写到一个真正的 Method 里再 simtalk_run "m()"
```

### 2.19 `startExtProc` ✅（需 "Allow access to the computer"）

```bash
$SOCKET_CLIENT --host $HOST --port $PORT --timeout 30 \
  --data '{"type":"simtalk_run","action_id":"startproc-001","simtalk_code":"print startExtProc(\"cmd.exe /C echo v14_done\", false, true)"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
# readlog 期望: <整数 PID，如 15156>
```

### 2.20 `system` ✅（需 "Allow access to the computer"）

```bash
$SOCKET_CLIENT --host $HOST --port $PORT --timeout 30 \
  --data '{"type":"simtalk_run","action_id":"system-001","simtalk_code":"print system(\"cmd.exe /C echo v14_sys\")"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
# readlog 期望: 0（echo 退出码 0 = 成功）
```

## 3. 完整回归测试（一次性跑 20 个）

把上面 16 个非模态函数串成一个 batch，按顺序执行 + 每步 readlog 验证：

```bash
#!/usr/bin/env bash
# 用 helper 脚本（参见 §4）批量跑
for fn_id in availableMemory getCurrentDirectory getApplicationProcessID \
             getFilesOfFolder getRegistry SHGetKnownFolderPath \
             copyTextToClipboard copyObjectsToClipboard getTextFromClipboard \
             copyFile setCurrentDirectory getEnv setEnv \
             setCodePage startExtProc system; do
    python3 /tmp/os_v14_helper.py "$fn_id" '<simtalk_code>'
done
```

## 4. 自定义 helper（推荐）

v14 实测用的 helper `/tmp/os_v14_helper.py` 把 `simtalk_syntax + simtalk_run + readlog` 三步打包，自动跳过 `Log file opened` 头并提取 print 行：

```python
# 核心逻辑：
sx = call(code, "simtalk_syntax", sx_id, timeout)
sx_pass = "hasError" not in sx.get("result", "")
if sx_pass:
    rn = call(code, "simtalk_run", rn_id, timeout)
    rn_pass = (rn.get("result") == "success"
               and not (rn.get("log") or "").startswith("code execute failed"))
    # v13 起 readlog 能拉到 print 实际值
    rl = call_readlog(timeout)
    log_lines = [l for l in rl.get("log","").split("\n") if l and "Log file opened" not in l]
```

调用方式：
```bash
python3 /tmp/os_v14_helper.py <fn_id> '<simtalk_code>' [--skip-run] [--timeout N]
```

输出末尾打印 `SX_VERDICT: PASS|FAIL | RN_VERDICT: PASS|FAIL`，中间打印 `PRINT_LINES: [...]` 列出所有 print 行。

## 5. 失败处理 / Failure Handling

| 现象 | 原因 | 处理 |
|---|---|---|
| `result:"success"` 但 `log:"code execute failed..."` | 运行时异常（如除零、Method-only 限制） | 这是 Quirk #7——`result` 不可信，必须看 `log` |
| `result:"failed"` + `log:"The statement 'sleep' is not allowed in formulas."` | sleep 在 formula 上下文 | 改用真正的 Method 包装 |
| `result:"failed"` + `log:"SHGetKnownFolderPath: Invalid class string"` | 误用符号名而非 CLSID GUID | 改用 `{B4BFCC3A-...}` 格式 |
| `result:"failed"` + `log:"...Prohibit Access to the Computer..."` | 模型设置禁止访问电脑 | GUI 关闭 *File > Model Settings > General > Prohibit Access to the Computer* |
| socket 永远没回包 | 模态对话框阻塞 GUI 线程 | **不要** socket 端调 `browseForFolder` / `selectFileForOpen` / `selectFileForSave` |
| `result:"failed"` + `log:"unknown identifier 'MyAttr'"` | 全局 attr 还没建，弹模态"是否创建" | 先在 GUI 建 attr 或改用 `var` 局部变量 |

更多故障排查见 `local-simtalk-execution/SKILL.md` 的 troubleshooting 表。