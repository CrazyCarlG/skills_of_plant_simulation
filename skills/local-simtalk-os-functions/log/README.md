# Test Logs

> 本目录记录针对 SimTalk OS 函数的本地 Plant Simulation 实测 session。

## 已完成 / Completed

| Session | 日期 | 内容 | 结果 | 路径 |
|---|---|---|---|---|
| v14 | 2026-08-25 | 20 个 OS 函数全量实测（借助 v13 readlog 修复拿 print 实际值） | 16 PASS + 1 FAIL（sleep Method-only）+ 3 SKIP（模态）= 20/20 覆盖 | `local-simtalk-execution/log/test-session-20260825-v14.md` |
| v15 | 2026-08-25 | **本 skill 自身测试**：抽样 7 个 recipe 验证文档与实测一致 | 7/7 一致（100%） | `local-simtalk-os-functions/log/test-session-20260825-v15-skill-test.md` |
| v16 | 2026-08-25 | **v17 高层封装下全量重测 20 函数** + 3 项新发现（`.dim` vs `.length`、list 字面量赋、sleep 行数无关） | 16 PASS + 1 FAIL + 3 SKIP 不变；20/20 与 v14 一致 | `local-simtalk-os-functions/log/test-session-20260825-v16.md` |

### v16 关键发现 / v16 Highlights

1. **`l.length` 不存在 / `l.dim` 才是真名** —— `var l: list; l := getFilesOfFolder(...); print l.length` 触发 Quirk #7 `Unknown identifier 'Length'`；改用 `l.dim` 立即成功。这是 v14 Finding #1 之后新发现的**命名陷阱**。
2. **`var l: list` 不能直接赋字面量 `[1,2,3]`** —— `var l: list; l := [1,2,3,4,5]` 报 "Left and right sides of the assignment are incompatible."。只能走 list-returning 函数（`getFilesOfFolder` / `makeList`）。
3. **`sleep` 失败与行数无关** —— v14/v15 隐含认知 "multi-line 才失败" 不准；任何含 `sleep` 的 code 在 formula eval 上下文里**一律** Quirk #7，唯一可行路径仍是写到真正的 Method 里再 `simtalk_run "m()"`。

详见 `test-session-20260825-v16.md`。**待办**：`functions.md` §9 + `test-cookbook.md` §2.9 需补 list API 段落；`local-simtalk-execution/references/lifelines.md` 需新增 "list API: `.dim` not `.length`" 章节。

### v15 关键观察 / v15 Highlights

- PASS recipes（R1/R2.1/R3）按 `test-cookbook.md` 模板拼 JSON 一次跑通
- FAIL 案例（R4 sleep）精确匹配 Quirk #7 的 `code execute failed` 描述
- SKIP 案例（R5 browseForFolder）8s 内无回包，与 Quirk #8 一致
- v15 实测发现：`browseForFolder` 后 ping 仍能通（与 v14 "server hang" 略有出入）——猜测是 Plant Simulation 服务端多线程，模态阻塞 GUI 主线程但不影响 ping 处理线程

### v14 关键发现 / v14 Highlights

1. **`print <list>` 只打印类型名** —— `getFilesOfFolder` 必须按索引取元素（Finding #1）
2. **`SHGetKnownFolderPath` 参数必须 CLSID GUID** —— 符号名会报 `Invalid class string`（Finding #2）
3. **`getRegistry` void 分支返回字面量 `VOID`** —— 不是空字符串（Finding #3）
4. **`setCodePage` 返回设置前的旧 code page** —— 不是新值（Finding #4）
5. **`startExtProc` 返回进程 PID** —— `cmd.exe` PID = 15156（Finding #5）
6. **`system` 返回进程退出码** —— echo 退出码 = 0（Finding #6）

详见 `references/v14-findings.md` 与 `local-simtalk-execution/log/test-session-20260825-v14.md`。

## 待补 / TODO

- **`sleep` Method 包装演示**：v14 跳过（formuLa 上下文禁用）。后续可建一个真正的 Method `m()` 包含 `sleep(3.5, false)\nprint "slept"` 然后 `simtalk_run "m()"`，验证 sleep 在 Method 上下文里能跑
- **3 个模态函数的 GUI 手动验证**：GUI 端手动调用 `browseForFolder` / `selectFileForOpen` / `selectFileForSave`，记录返回值（本 skill 不覆盖自动化路径）
- **不同 OS / 不同 Windows 版本下的对照**：当前 v14 是在用户宿主机（Windows Server 2022）上的实测，可补充其它 Windows 版本（Win10 / Win11）的对照数据
- **`getRegistry` 的 string / integer 分支实测**：v14 只落在 void 分支，可补测 `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProductName`（实际可能已被 Microsoft 改名到别的键）拿到字符串值的场景

## 命名约定 / Naming Convention

测试 session 文件名格式：

```text
test-session-YYYYMMDD-v<N>-<description>.md
```

- `YYYYMMDD`：测试日期
- `v<N>`：版本号（与 `local-simtalk-execution` 的 v1~v14 主线对齐，或本技能独立 v 编号）
- `<description>`：简述（英文/拼音均可）

存放位置：跨技能的通用 session（如协议变更、readlog 修复）放在 `local-simtalk-execution/log/`；本技能专属的 OS 函数实测可以放在 `simtalk-os-functions/log/`，也可以引用 `local-simtalk-execution/log/` 已有 session。

## 引用日志 / Cross-references

- v15（本 skill 测试）：`local-simtalk-os-functions/log/test-session-20260825-v15-skill-test.md`
- v13 readlog 修复：`local-simtalk-execution/log/test-session-20260825-v13.md`
- v12 readlog bug 发现：`local-simtalk-execution/log/test-session-20260825-v12.md`（已废弃，保留作历史快照）
- 协议基础：`local-simtalk-execution/references/message-schema.md` / `code-templates.md`