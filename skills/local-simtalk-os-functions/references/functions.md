# 20 OS Functions — Consolidated Reference

> **来源**：官方文档 `01-plantsimulation-knowledge/01-plant-simulation-help/simtalk/predefined-functions-i-os-math-string-datetime/operating-system/operating-system.md`
>
> **实测**：v14 测试 session（2026-08-25），本地 Plant Simulation 通过 `local-simtalk-execution` 验证了真实返回值。详见 `v14-findings.md` 与 `log/README.md`。
>
> **图例**：
> - ✅ PASS — v14 实测签名 / 返回值与文档一致
> - ❌ FAIL — v14 实测发现限制（Method-only / 模态）
> - ⏭ SKIP — 跳过测试（模态对话框会让服务端阻塞）
> - ⚠️ — 前置条件 / 安全设置要求

---

## 分组索引 / Grouped Index

| 分组 | 函数 |
|---|---|
| 系统信息查询 | `availableMemory` / `getApplicationProcessID` / `getCurrentDirectory` / `getEnv` / `getRegistry` / `SHGetKnownFolderPath` |
| 文件与目录 | `browseForFolder` / `copyFile` / `getFilesOfFolder` / `selectFileForOpen` / `selectFileForSave` / `setCurrentDirectory` |
| 剪贴板 | `copyObjectsToClipboard` / `copyTextToClipboard` / `getTextFromClipboard` |
| 外部进程与系统命令 | `startExtProc` / `system` |
| 运行控制与配置 | `setCodePage` / `setEnv` / `sleep` |

---

## 1. `availableMemory` — 返回可用主内存总量（MB）

- **签名**：`availableMemory → real`
- **返回**：`real`（单位 MB；v14 实测 `10536.9765625` ≈ 10.3 GB）
- **状态**：✅ PASS
- **示例**：
  ```simtalk
  print availableMemory
  ```
- **备注**：无参数；调用极快。

---

## 2. `browseForFolder` — 打开文件夹选择/新建对话框

- **签名**：`browseForFolder(Message:string) → string`
- **参数**：`Message`（string，提示语）
- **返回**：`string`（所选文件夹路径）
- **状态**：⏭ SKIP — **模态**，弹 Windows 对话框阻塞 GUI 线程，socket 永远拿不到回包（Quirk #8）
- **示例**：
  ```simtalk
  browseForFolder("Select the folder you would like to open:")
  ```
- **备注**：**不要**在自动化测试里调用——会让服务端 hang。GUI 手动调用可用。

---

## 3. `copyFile` — 复制文件

- **签名**：`copyFile(Source:string, Destination:string) → boolean`
- **参数**：
  - `Source`（string）— 源文件路径
  - `Destination`（string）— 目标文件夹
- **返回**：`boolean`（`true` = 成功，`false` = 失败；v14 实测 `true`）
- **状态**：✅ PASS（需"Allow access to the computer"模型设置）
- **示例**：
  ```simtalk
  print copyFile("C:\\file.txt", "C:\\temp\\file.txt")
  ```
- **备注**：受 `File > Model Settings > General > Prohibit Access to the Computer` 约束——启用后函数被禁止。文档说：启用时不能从模型文件夹往外拷，安全模式下仅允许向模型文件夹写入。

---

## 4. `copyObjectsToClipboard` — 复制对象到内部剪贴板

- **签名**：`copyObjectsToClipboard(Objects:object/object[])`
- **参数**：`Objects`（单对象或 `object[]`）
- **返回**：`void`
- **状态**：✅ PASS（执行成功）
- **示例**：
  ```simtalk
  var objs: object[]
  objs := [Station, Station1, Connector]
  copyObjectsToClipboard(objs)
  .Models.Frame2.pasteClipboard
  ```
- **备注**：复制会清空剪贴板旧内容。Connector 必须连同前后对象一起复制才能成功。

---

## 5. `copyTextToClipboard` — 复制文本到剪贴板

- **签名**：`copyTextToClipboard(TextToBeCopied:string)`
- **参数**：`TextToBeCopied`（string）
- **返回**：`void`
- **状态**：✅ PASS（通过后续 `getTextFromClipboard` 验证）
- **示例**：
  ```simtalk
  copyTextToClipboard("My long text, text, text.")
  ```
- **备注**：复制会清空剪贴板旧内容。

---

## 6. `getApplicationProcessID` — 返回当前 Plant Simulation 会话的 PID

- **签名**：`getApplicationProcessID → integer`
- **返回**：`integer`（v14 实测 `18720`）
- **状态**：✅ PASS
- **示例**：
  ```simtalk
  print getApplicationProcessID -- e.g. 8252
  ```
- **备注**：每次启动 Plant Simulation 时 PID 会变化。

---

## 7. `getCurrentDirectory` — 返回当前工作目录

- **签名**：`getCurrentDirectory → string`
- **返回**：`string`（v14 实测 `C:\Users\z004bjuu\Documents\plantsimulaion_agents`）
- **状态**：✅ PASS
- **示例**：
  ```simtalk
  print getCurrentDirectory
  ```
- **备注**：对应启动选项 `-cwd dir`。

---

## 8. `getEnv` — 读取环境变量

- **签名**：`getEnv(EnvironmentVariable:string) → string`
- **参数**：`EnvironmentVariable`（string）
- **返回**：`string`（变量不存在时返回空字符串 `""`；v14 实测 `PATH` 返回 700+ 字符完整路径）
- **状态**：✅ PASS
- **示例**：
  ```simtalk
  print getEnv("PATH")
  ```

---

## 9. `getFilesOfFolder` — 列出匹配搜索模式的文件/文件夹

- **签名**：`getFilesOfFolder(SearchPattern:string) → list`
- **参数**：`SearchPattern`（string，目录 + 模式；`*` = 任意串，`?` = 单字符）
- **返回**：`list`（v14 实测按索引取元素：`l[1]=bfsvc.exe`、`l[2]=explorer.exe`、`l[3]=HelpPane.exe`）
- **状态**：✅ PASS
- **示例**：
  ```simtalk
  var allFiles, executables: list
  allFiles := getFilesOfFolder("C:\\Temp\\*")
  executables := getFilesOfFolder("C:\\Windows\\*.exe")
  ```
- **⚠️ 重要**：`print <list>` 只打印类型名（如 `FilesOfFolder`），**不会**自动展开 list 元素。要拿元素必须：
  ```simtalk
  var l: list
  l := getFilesOfFolder("C:\\Windows\\*.exe")
  print l[1]
  print l[2]
  print l[3]
  ```
  详见 `v14-findings.md` Finding #1。

- **⚠️ List 长度查询用 `.dim` 不是 `.length`**（v16 新发现）：
  ```simtalk
  var l: list
  l := getFilesOfFolder("C:\\Windows\\*.exe")
  print l.dim       -- ✅ 正确：返回 list 元素数量
  ```
  其它语言常见的 `.length` / `.size` / `.count` 在 Plant Simulation `list` 上**全部不存在**——`l.length` 会触发 Quirk #7 软失败，错误信息 `Unknown identifier 'Length'`。详见 `references/lifelines.md` §??（list API 章节）。

- **⚠️ List 字面量不能直接赋给 `var l: list`**（v16 新发现）：
  ```simtalk
  var l: list; l := [1,2,3,4,5]   -- ❌ 报 "Left and right sides of the assignment are incompatible."
  var l: list[integer]; l := [1,2,3,4,5]   -- ❌ 同样报 type 不兼容
  ```
  Plant Simulation 不允许把数组字面量 `[1,2,3]` 直接赋给 `list` 或 `list[integer]` 变量。要构造 list **只能**走 list-returning 的内置函数：
  ```simtalk
  var l: list
  l := getFilesOfFolder("C:\\Windows\\*.exe")   -- ✅ 函数返回的 list
  -- 或：表 / Table / Method 的 list 实参位置直接用 [1,2,3]
  ```
  字面量语法仅在函数**实参**位置合法（如 `print([1,2,3])` 直接传给 print）。

---

## 10. `getRegistry` — 读取 Windows 注册表

- **签名**：`getRegistry(Key:string, Value:string)`
- **参数**：
  - `Key`（string）— 注册表键
  - `Value`（string）— 键值名
- **返回**：**三态**（取决于键值类型）：
  - `void` — 键值不存在（v14 实测打印 `VOID`，字面量字符串；详见 `v14-findings.md` Finding #3）
  - `integer` — REG_DWORD
  - `string` — REG_SZ / REG_EXPAND_SZ / REG_MULTI_SZ / REG_BINARY
- **状态**：✅ PASS（本次落在 `void` 分支）
- **示例**：
  ```simtalk
  print getRegistry("HKEY_LOCAL_MACHINE\\SOFTWARE\\Siemens\\Tecnomatix Plant Simulation 2606", "")
  ```
- **备注**：键名根支持 `HKEY_CLASSES_ROOT` / `HKEY_CURRENT_USER` / `HKEY_LOCAL_MACHINE`（缩写 `HKCR` / `HKCU` / `HKLM` 都接受）。

---

## 11. `getTextFromClipboard` — 从剪贴板读取文本

- **签名**：`getTextFromClipboard → string`
- **返回**：`string`（v14 实测 `V14_GETTEST`）
- **状态**：✅ PASS
- **示例**：
  ```simtalk
  print getTextFromClipboard
  ```

---

## 12. `selectFileForOpen` — 打开"打开文件"对话框

- **签名**：`selectFileForOpen([FileFilter:string[, PredefinedName:string]]) → string`
- **参数**：
  - `FileFilter`（string，可选）— Microsoft 风格过滤器 `Comment1|Filter1|Comment2|Filter2||`
  - `PredefinedName`（string，可选）— 默认路径
- **返回**：`string`（所选文件路径；点 Cancel 返回 `""`）
- **状态**：⏭ SKIP — **模态**（Quirk #8）
- **示例**：
  ```simtalk
  var str: string
  str := selectFileForOpen
  if str /= ""
     statTable.readFile(str)
  end
  ```

---

## 13. `selectFileForSave` — 打开"另存为"对话框

- **签名**：`selectFileForSave([FileFilter:string[, PredefinedName:string]]) → string`
- **参数**：
  - `FileFilter`（string，可选）— 同 `selectFileForOpen`
  - `PredefinedName`（string，可选）— 预填文件名
- **返回**：`string`（保存路径；点 Cancel 返回 `""`）
- **状态**：⏭ SKIP — **模态**（Quirk #8）
- **示例**：
  ```simtalk
  var str: string
  str := selectFileForSave
  if str /= ""
     saveModel(str)
  end
  ```

---

## 14. `setCodePage` — 设置 ANSI 数据交换代码页

- **签名**：`setCodePage([CodePageName:integer]) → integer`
- **参数**：`CodePageName`（integer，可选；常用：932 日文 / 936 中文 / 1250 匈牙利 / 1252 英德 / 0 = 操作系统代码页 / 65001 = UTF-8）
- **返回**：`integer` —— **设置前**的旧代码页（v14 实测从 `0` → `65001`，返回 `0`；详见 `v14-findings.md` Finding #4）
- **状态**：✅ PASS
- **示例**：
  ```simtalk
  setCodePage(932)   -- Japanese
  setCodePage(936)   -- Chinese
  setCodePage(1250)  -- Hungarian
  setCodePage(1252)  -- English, German
  setCodePage(0)     -- OS default
  print setCodePage  -- returns CURRENT code page (no arg = query)
  ```
- **备注**：无参数调用 = 查询当前代码页（不改变值）；带参数 = 设置并返回**前值**。

---

## 15. `setCurrentDirectory` — 设置当前工作目录

- **签名**：`setCurrentDirectory(WorkingFolder:string) → boolean`
- **参数**：`WorkingFolder`（string）
- **返回**：`boolean`（`true` = 成功，`false` = 失败；v14 实测 `true`，后续 `getCurrentDirectory` 返回 `C:\Windows`）
- **状态**：✅ PASS（需"Allow access to the computer"）
- **示例**：
  ```simtalk
  print setCurrentDirectory("C:\\users\\hank")
  ```

---

## 16. `setEnv` — 设置环境变量

- **签名**：`setEnv(EnvironmentVariable:string, Value:string) → boolean`
- **参数**：
  - `EnvironmentVariable`（string）
  - `Value`（string）
- **返回**：`boolean`（v14 通过后续 `getEnv` 验证生效）
- **状态**：✅ PASS（需"Allow access to the computer"）
- **示例**：
  ```simtalk
  setEnv("ralf", "0")
  startExtProc("PlantSimulation2606.exe")
  -- in the external process:
  print getEnv("ralf")
  ```

---

## 17. `SHGetKnownFolderPath` — 返回系统标准文件夹路径

- **签名**：`SHGetKnownFolderPath(CLSID:string) → string`
- **参数**：`CLSID`（string）— **必须**是 `{GUID}` 格式的 KNOWNFOLDERID
- **返回**：`string`（v14 实测 `{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}` → `C:\Users\z004bjuu\Desktop`）
- **状态**：✅ PASS
- **示例**：
  ```simtalk
  print SHGetKnownFolderPath("{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}")
  -- returns e.g. C:\Users\MyLoginName\Desktop
  ```
- **⚠️ 重要**：参数必须是 **`"{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}"`** 这样的 GUID 格式，**不能**用 `"FOLDERID_Desktop"` 这种符号名——会报 `Invalid class string`。详见 `v14-findings.md` Finding #2。
- **参考**：https://docs.microsoft.com/en-us/windows/win32/shell/knownfolderid

---

## 18. `sleep` — 按真实时间挂起 Method

- **签名**：`sleep(Time:real[, SuspendProcess:boolean:=true])`
- **参数**：
  - `Time`（real，秒数）
  - `SuspendProcess`（boolean，默认 `true`）— `true` = 整个进程挂起，`false` = 只停当前 Method（类似 `wait`，但用真实时间）
- **返回**：`void`
- **状态**：❌ FAIL — **Method-only**（Quirk #7）
  - 文档原话："The statement 'sleep' is not allowed in formulas."
  - `simtalk_run` 的执行上下文是 formula 评估，所以 sleep 永远走不到
  - v14 实测：`sleep(0.5, false)\nprint "slept"` → `code execute failed. error msg:The statement 'sleep' is not allowed in formulas.`
  - **规避**：把 sleep 写到一个**真正的 Method**里再 `simtalk_run "m()"` 调用
- **示例**：
  ```simtalk
  sleep(3.5, false)
  ```

---

## 19. `startExtProc` — 启动外部进程

- **签名**：`startExtProc(PathToProgram:string[, Visible:boolean, WaitUntilProcessTerminated:boolean]) → integer`
- **参数**：
  - `PathToProgram`（string）— 外部进程路径，路径分隔符用 `\\`
  - `Visible`（boolean，可选）— `true` = 窗口可见，`false` = 隐藏；默认 `true`
  - `WaitUntilProcessTerminated`（boolean，可选）— `true` = 等待进程退出；默认 `false`
- **返回**：`integer` — 进程 PID 或 `0`（失败；v14 实测 `cmd.exe /C echo ...` 返回 `15156`；详见 `v14-findings.md` Finding #5）
- **状态**：✅ PASS（需"Allow access to the computer"）
- **示例**：
  ```simtalk
  startExtProc("C:\\Program Files (x86)\\Adobe\\Acrobat Reader DC\\Reader\\AcroRd32.exe")
  -- 隐藏窗口 + 等待退出：
  startExtProc("cmd.exe /C dir file.txt", false, true)
  ```
- **备注**：适合带 GUI 的程序；DOS 命令 + 隐藏窗口的常用做法见示例。

---

## 20. `system` — 执行系统命令（DOS only）

- **签名**：`system(Command:string) → integer`
- **参数**：`Command`（string）
- **返回**：`integer` — 命令退出码（v14 实测 `cmd.exe /C echo ...` 返回 `0` = 成功；详见 `v14-findings.md` Finding #6）
- **状态**：✅ PASS（需"Allow access to the computer"）
- **示例**：
  ```simtalk
  if system("del C:\\temp\\file.txt") = 0
     print "file deleted"
  end
  ```
- **备注**：
  - **仅限 DOS 命令**；GUI 程序用 `startExtProc`，否则两个程序会互相阻塞
  - Plant Simulation 会被阻塞直到命令完全执行
  - 隐藏命令窗口的窗口用 `startExtProc("cmd.exe /C ...", false, true)`

---

## 状态汇总 / Status Summary

| # | 函数 | doc 返回 | v14 实测 | SX | RN | 备注 |
|---|---|---|---|---|---|---|
| 1 | `availableMemory` | `real` | `10536.9765625` | ✅ | ✅ | |
| 2 | `browseForFolder` | `string` | — | — | — | ⏭ 模态 |
| 3 | `copyFile` | `boolean` | `true` | ✅ | ✅ | ⚠️ Allow access |
| 4 | `copyObjectsToClipboard` | `void` | 执行成功 | ✅ | ✅ | |
| 5 | `copyTextToClipboard` | `void` | 验证成功 | ✅ | ✅ | |
| 6 | `getApplicationProcessID` | `integer` | `18720` | ✅ | ✅ | |
| 7 | `getCurrentDirectory` | `string` | `C:\Users\...` | ✅ | ✅ | |
| 8 | `getEnv` | `string` | 完整 PATH | ✅ | ✅ | |
| 9 | `getFilesOfFolder` | `list` | 元素列表 | ✅ | ✅ | ⚠️ `print <list>` 只打类型名 |
| 10 | `getRegistry` | `void/int/str` | `VOID` | ✅ | ✅ | 三态都合法 |
| 11 | `getTextFromClipboard` | `string` | `V14_GETTEST` | ✅ | ✅ | |
| 12 | `selectFileForOpen` | `string` | — | — | — | ⏭ 模态 |
| 13 | `selectFileForSave` | `string` | — | — | — | ⏭ 模态 |
| 14 | `setCodePage` | `integer` | `0`（前值） | ✅ | ✅ | ⚠️ 返回的是**前值** |
| 15 | `setCurrentDirectory` | `boolean` | `true` | ✅ | ✅ | ⚠️ Allow access |
| 16 | `setEnv` | `boolean` | 验证生效 | ✅ | ✅ | ⚠️ Allow access |
| 17 | `SHGetKnownFolderPath` | `string` | `C:\Users\...\Desktop` | ✅ | ✅ | ⚠️ 参数必须 CLSID GUID |
| 18 | `sleep` | `void` | FAIL | ✅ | ❌ | ❌ Method-only |
| 19 | `startExtProc` | `integer` | `15156`（PID） | ✅ | ✅ | ⚠️ Allow access |
| 20 | `system` | `integer` | `0`（退出码） | ✅ | ✅ | ⚠️ Allow access |

**统计**：**16 PASS + 1 FAIL（sleep Method-only）+ 3 SKIP（模态）= 20 / 20 覆盖**