# Quirks — OS 函数相关的服务端 quirks

> 这些 quirks 来自 `local-simtalk-execution` 的累积测试 session（v6~v14），不是本技能专有，但**直接影响** OS 函数能否在 socket 端验证。

| Quirk # | 名称 | 影响 | OS 函数受影响 |
|---|---|---|---|
| Quirk #6 | `simtalk_run` 的 `data` 字段恒空 | socket 拿不到 `return X` 的返回值 | 所有返回非 void 的函数 |
| Quirk #7 | 运行时异常仍返回 `result:"success"` | 必须同时检查 `log` | 所有函数 |
| Quirk #8 | 模态对话框阻塞 GUI 线程 | server hang，socket 永远没回包 | `browseForFolder` / `selectFileForOpen` / `selectFileForSave` |
| Quirk #11 | ~~readlog 不返回 GUI Console 输出~~ (v13 修复) | — | — |
| Quirk #12 | ~~readlog 反馈循环 / 体积膨胀~~ (v13 修复) | — | — |

---

## Quirk #6 — `simtalk_run` 的 `data` 字段恒空

**现象**：
- `simtalk_run` 的 `data` 字段在所有用例下（integer / string / 加不加 `return_value:true` 标记）**都不出现**
- 服务端 `Run_Simutalk` 是 `-> void` 方法（不是 expression 上下文），不会把内层 `return X` 的值序列化进 socket 回传

**影响**：
- 单纯 `simtalk_run "return 1+1"` 拿不到 `2`
- 但 `simtalk_run "print 1+1"` 之后调 `readlog` 能看到 `2`（v13 起 readlog 包含 GUI Console 输出）

**OS 函数实战**：
- `availableMemory` / `getApplicationProcessID` / `getCurrentDirectory` / `getEnv` / `getRegistry` / `SHGetKnownFolderPath` / `setCodePage` / `startExtProc` / `system` / `getTextFromClipboard` / `copyFile` / `setCurrentDirectory` / `setEnv` —— 全部依赖 `print <func(...)>` + readlog 才能拿到返回值
- `getFilesOfFolder` —— 同样要 `var l: list; l := ...; print l[1]; print l[2]; ...`
- `copyTextToClipboard` / `copyObjectsToClipboard` —— `void` 函数，print 只验证执行成功（实际效果要靠后续 `getTextFromClipboard` 验证）

**规避**：所有取值统一走 `simtalk_run "print X"` + `readlog` 标准流程（详见 `test-cookbook.md` §1）。

---

## Quirk #7 — 运行时异常仍返回 `result:"success"`（错误细节在 log）

**现象**：
- 运行时异常（除零、未知标识符、Method-only 限制等）`simtalk_run` 仍返回 `result:"success"`
- 错误细节改走 `log` 字段，前缀 `"code execute failed. error msg:..."`

**影响**：
- 只看 `result == "success"` 会漏掉运行时异常
- 双重检查必须：

  ```text
  result == "success"  AND  not log.startswith("code execute failed")
  ```

**OS 函数实战**：
- `sleep` —— v14 实测：`result:"success"` + `log:"code execute failed. error msg:The statement 'sleep' is not allowed in formulas."`（这是设计限制，不是 bug）
- `SHGetKnownFolderPath("FOLDERID_Desktop")` —— v14 实测：同上模式，错误信息 `Invalid class string`
- `copyFile` / `setCurrentDirectory` / `setEnv` / `startExtProc` / `system` —— 若模型设置 "Prohibit Access to the Computer" 启用，错误信息也走 `log`

**成功的正确写法（双重判据）**：

```python
rn_pass = (rn.get("result") == "success"
           and not (rn.get("log") or "").startswith("code execute failed"))
```

---

## Quirk #8 — 模态对话框阻塞 GUI 线程

**现象**：
- `browseForFolder` / `selectFileForOpen` / `selectFileForSave` / `prompt` / `promptList1` / `promptListN` / `infoBox` 等模态函数在 `simtalk_run` 里**禁止使用**
- 它们会弹出 GUI 对话框直到用户点击 OK，服务端阻塞
- socket 永远拿不到回包（表现跟 v3-v5 的"卡死 60s"完全一致）
- 还有"是否创建全局 attr MyAttr？"等隐式模态对话框

**OS 函数实战**：
- ❌ **不要在 socket 端调用**：`browseForFolder` / `selectFileForOpen` / `selectFileForSave`
- ✅ 改用非模态替代品：
  - 文件夹选择 → `SHGetKnownFolderPath("{...}")`（系统标准文件夹）
  - 列出文件 → `getFilesOfFolder(<pattern>)`
  - 用户输入 → 写到全局 attribute（先在 GUI 建好）或让 GUI 手动触发

---

## Quirk #11 / #12 — v13 已修复

> v12 时代 readlog 的两个 bug 在 v13 已修复。本技能的所有 readlog 用法都依赖 v13+ 行为。

### Quirk #11（v12 旧 / v13 修复）

~~readlog 不返回 GUI Console 输出~~

- **v12 现象**：readlog 返回的是服务端 socket wrapper 自己的应用日志（I/O trace + Log file opened + Sent successfully），拿不到 Plant Simulation GUI Console 的 `print(...)` 输出
- **v13 修复**：readlog 现在直接拉回 GUI Console 输出——socket 端**第一次**能拿到 `print(...)` 实际值
- **OS 函数实战**：所有需要 print 取值的 OS 函数（见 Quirk #6）现在都能验证了

### Quirk #12（v12 旧 / v13 修复）

~~readlog 反馈循环 / 体积膨胀~~

- **v12 现象**：服务端把每次发出的 readlog 响应写进自己的应用日志，下次 readlog 再把这条历史响应塞进 `log` 字段，回包体积指数级膨胀（几次调用就能撑爆 socket 缓冲区、让服务端 hang）
- **v13 修复**：服务端用独立缓冲 + 重置方案根治（每次 readlog 后清空 buffer）
- **OS 函数实战**：可以放心在自动化循环里连续调 readlog 拉 print 输出——v13 R5 验证：4 次连续 readlog 体积稳定在 203 字节（vs v12 的指数级膨胀）

---

## 完整 Quirks 表参见

`local-simtalk-execution/references/message-schema.md`（Quirks 列表） + `workflow.md`（避免清单 + 错误重试策略表）。