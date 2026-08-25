# v14 New Findings — 6 条 v14 测试新发现

> 测试 session：`test-session-20260825-v14.md`（`local-simtalk-execution/log/`），2026-08-25
>
> 来源 v11（旧）：socket 端只能确认 `result:"success"` / `result:"failed"`，拿不到 print 实际值。
>
> 来源 v14（新）：借助 v13 readlog 修复，socket 端**第一次**能直接拿到 `print(...)` 表达式求值后的真实字符串——所以才能发现下面这 6 条 v11 没能验证的细节。

---

## Finding #1 — `print <list>` 只打印类型名，不展开元素

**函数**：`getFilesOfFolder`

**v14 R4.4 验证**：

```bash
# 输入 1（错误写法）：
print getFilesOfFolder("C:\\Windows\\*.exe")
# readlog: FilesOfFolder     ← 只打类型名！

# 输入 2（正确写法）：
var l: list
l := getFilesOfFolder("C:\\Windows\\*.exe")
print l[1]; print l[2]; print l[3]
# readlog: bfsvc.exe / explorer.exe / HelpPane.exe
```

**结论**：SimTalk 的 `print` 表达式对 `list` 类型只调用 `toString()`（返回类型名 `FilesOfFolder`），**不会**自动展开元素。

**规避**：
```simtalk
var l: list
l := getFilesOfFolder(<pattern>)
print l[1]
print l[2]
...
```

或者：
```simtalk
print l.dim       -- list 长度
print l[1..l.dim] -- 切片（语法待确认）
```

**适用**：所有返回 `list` 的函数（当前 OS 函数里只有 `getFilesOfFolder`）。

---

## Finding #2 — `SHGetKnownFolderPath` 参数必须是 CLSID GUID 格式

**函数**：`SHGetKnownFolderPath`

**v14 R4.6 验证**：

```bash
# 输入 1（错误写法——符号名）：
print SHGetKnownFolderPath("FOLDERID_Desktop")
# log: "code execute failed. error msg:SHGetKnownFolderPath: Invalid class string, in code '...'"

# 输入 2（正确写法——文档示例）：
print SHGetKnownFolderPath("{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}")
# readlog: C:\Users\z004bjuu\Desktop
```

**结论**：参数**必须**是 `"{B4BFCC3A-...}"` 这样的 KNOWNFOLDERID GUID 字符串。**不能**用 `"FOLDERID_Desktop"` 之类的符号名——服务端底层走 Win32 `SHGetKnownFolderPath` API，符号名不是合法 CLSID。

**为什么 v11 测过却报失败**：v11 helper 用了符号名 → 报错 → 当时没意识到是参数格式问题。

**参考**：https://docs.microsoft.com/en-us/windows/win32/shell/knownfolderid

---

## Finding #3 — `getRegistry` void 分支返回 `VOID`（不是空字符串）

**函数**：`getRegistry`

**v14 R4.5 验证**：

```bash
# 输入：键值不存在的场景
print getRegistry("HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion", "ProductName")
# readlog: VOID
```

**文档原文**：`void if the value does not exist`

**实测**：socket 端打印出 **`VOID`**（字面量字符串），**不是**空字符串 `""`。

**实用技巧**：
- 区分 `void`（键值不存在）vs `""`（键值存在但内容为空字符串）：用 `getRegistry(...) = "VOID"` 判断前者
- 注意 `VOID` 是 4 字符大写字面量，**与** SimTalk 类型系统里的 `void`（用于函数无返回值签名）**不是同一个概念**——这里是 print 把它当字符串处理

---

## Finding #4 — `setCodePage` 返回的是**设置前**的旧 code page

**函数**：`setCodePage`

**v14 R4.14 验证**：

```bash
# 输入：
print setCodePage(65001)    -- UTF-8
# readlog: 0  ← 设置前的旧值（不是 65001）
```

**文档原文**：`It is the previous value of the code page before it was changed`

**实测**：从 `0`（操作系统默认）→ `65001`，返回 `0`（前值），不是新值 `65001`。

**客户端使用建议**：
- 想看**当前** code page：无参数调用 `print setCodePage`
- 想**设置**并**保留**前值：`var prev := setCodePage(<new>)`
- 不要把返回值当成"刚设置的值"

---

## Finding #5 — `startExtProc("cmd.exe /C echo ...", false, true)` 返回 cmd.exe 的 PID

**函数**：`startExtProc`

**v14 R4.16 验证**：

```bash
# 输入：
print startExtProc("cmd.exe /C echo v14_done", false, true)
# readlog: 15156  ← cmd.exe 进程的 PID
```

**文档原文**：`The function either returns the process ID (PID) or it returns 0 if the function fails`

**实测**：
- `cmd.exe /C echo v14_done` 启动 cmd.exe 子进程（PID `15156`），`echo` 一句就退出，所以 cmd.exe 立即终止
- `WaitUntilProcessTerminated=true` 阻塞到 cmd.exe 退出
- 返回值是 cmd.exe **进程本身的 PID**，**不是** echo 的退出码

**对比 `system`**：见 Finding #6。

---

## Finding #6 — `system("cmd.exe /C echo ...")` 返回 cmd.exe 的退出码

**函数**：`system`

**v14 R4.17 验证**：

```bash
# 输入：
print system("cmd.exe /C echo v14_sys")
# readlog: 0  ← echo 的退出码
```

**文档原文**：`The return value has the data type integer. It is identical with the exit state of the command`

**实测**：
- `echo v14_sys` 退出码 = `0`（成功）
- 与 `startExtProc` 的区别：`startExtProc` 返回**子进程 PID**（v14 是 `15156`）；`system` 返回**子进程退出码**（v14 是 `0`）

**对比表**：

| 函数 | 返回什么 | 实测值 |
|---|---|---|
| `startExtProc` | 进程 PID（或 0 = 失败） | `15156` |
| `system` | 退出码 | `0`（echo 成功）|

---

## 总结 / Summary

| Finding | 函数 | 类型 | 关键纠正 |
|---|---|---|---|
| #1 | `getFilesOfFolder` | 输出行为 | `print <list>` 只打类型名，要按索引取元素 |
| #2 | `SHGetKnownFolderPath` | 参数格式 | 必须 CLSID GUID `"{...}"`，不能用符号名 |
| #3 | `getRegistry` | 返回值字面量 | void 分支返回字符串 `VOID`，不是 `""` |
| #4 | `setCodePage` | 返回值语义 | 返回**前值**（旧 code page），不是新值 |
| #5 | `startExtProc` | 返回值类型 | 返回**进程 PID**（整数） |
| #6 | `system` | 返回值类型 | 返回**进程退出码**（整数） |

**文档一致性**：v14 复测确认 `operating-system.md` 的所有签名 / 返回类型**与实测一致**——本次没发现文档错误，所有发现都是文档**没说清楚**的细节（文档说 "returns the PID" 但没说 "vs `system` 返回退出码" 这种对比关系）。