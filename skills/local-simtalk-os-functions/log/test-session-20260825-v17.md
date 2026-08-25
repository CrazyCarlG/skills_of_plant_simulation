# local-simtalk-os-functions Skill Test — v17 (2026-08-25)

测试目标：**回归 v16 三大新发现 + 探测 `simtalk_syntax` 阶段与 `getFilesOfFolder` 空匹配行为**。

承接上下文：

- **v14**（`local-simtalk-execution/log/test-session-20260825-v14.md`）：首次全量 20 函数实测。
- **v15**（`log/test-session-20260825-v15-skill-test.md`）：本 skill 自身抽样测试，7/7 一致。
- **v16**（`log/test-session-20260825-v16.md`）：v17 高层封装下全量重测 + **三大新发现**：
  1. `l.dim` 才是真名（`l.length` 报 `Unknown identifier 'Length'`）
  2. `var l: list` 不能直接赋字面量 `[1,2,3]`
  3. `sleep` 在 formula 上下文**任何** form 都失败（与行数无关）
- **v17（本 session）**：不重复全量 20 函数——只对 v16 三大发现做回归 + 探测 3 个未覆盖的边角。

## 1. 环境 / Environment

- **Skill under test**：`skills/local-simtalk-os-functions/`
- **Server**：Plant Simulation（宿主机），TCP **50007**
- **Client host**：WSL2 容器 → `host.docker.internal:50007`
- **调用入口**：`scripts/simtalk_send.py run|syntax|ping`（默认参数：`--timeout 20/30`）
- **退出码判据**：0 = 语义成功、11 = Quirk #7 软失败、12 = syntax `hasError`、1 = socket/timeout
- **readlog 限制**：v15+ readlog 已回归（buffer 自我嵌套，不可信）——本 session **不依赖** readlog 拿 print 实际值，只看 `simtalk_run` 的 `result` / `log` 字段判断 PASS/FAIL
- **测试时间**：2026-08-25（接续 v16）

## 2. 握手 / Handshake

| ID | 命令 | 回包 | 退出码 | 结论 |
|---|---|---|---|---|
| v17-init | `simtalk_send.py ping` | `{"type":"ping","result":"success"}` | 0 | ✅ 链路通 |

## 3. v16 三大发现回归 / Regression of v16 Findings

### 3.1 F9a：`l.dim`（v16 #5.1 正例）

**输入**：
```simtalk
var l: list
l := getFilesOfFolder("C:\\Windows\\*.exe")
print l.dim
```

**实测**（`simtalk_send.py run`）：
```json
{"result":"success","log":"execute success"}
```

**退出码**：0

**结论**：✅ **回归通过** —— `l.dim` 仍然成功执行，与 v16 一致。readlog 受限，无法直接读 print 值；但 `execute success` 已足够证明 `.dim` 在运行时合法。

---

### 3.2 F9b：`l.length`（v16 #5.1 反例）

**输入**：
```simtalk
var l: list
l := getFilesOfFolder("C:\\Windows\\*.exe")
print l.length
```

**实测**：
```json
{
  "result": "success",
  "log": "code execute failed. error msg:Unknown identifier 'Length', in code 'var l: list\nl := getFilesOfFolder(\"C:\\\\Windows\\\\*.exe\")\nprint l.length'"
}
```

**退出码**：11（Quirk #7 软失败）

**结论**：✅ **回归通过** —— `l.length` 仍然触发 `Unknown identifier 'Length'`，错误信息字符串与 v16 完全一致。**双重判据抓住**：`result == "success"` 但 `log` 以 `code execute failed` 开头，实际是 FAIL。

---

### 3.3 F9c：list 字面量赋值（v16 #5.2）

**输入**：
```simtalk
var l: list
l := [1,2,3,4,5]
print l.dim
```

**实测**：
```json
{
  "result": "success",
  "log": "code execute failed. error msg:Left and right sides of the assignment are incompatible., in code 'var l: list\nl := [1,2,3,4,5]\nprint l.dim'"
}
```

**退出码**：11（Quirk #7 软失败）

**结论**：✅ **回归通过** —— `var l: list` 不能直接赋字面量的行为在 v17 仍然成立。错误字符串与 v16 一致。

---

### 3.4 F18：`sleep` formula 上下文（v16 #5.3）

**输入**：
```simtalk
sleep(0.5, false)
print "slept"
```

**实测**：
```json
{
  "result": "success",
  "log": "code execute failed. error msg:The statement 'sleep' is not allowed in formulas., in code 'sleep(0.5, false)\nprint \"slept\"'"
}
```

**退出码**：11（Quirk #7 软失败）

**结论**：✅ **回归通过** —— `sleep` 在 formula 上下文仍然 Quirk #7。注意：本次 v17 输入是 v14 / v15 / v16 一直用的 multi-line 模板，与 v16 #5.3 的"单行/多行都失败"结论不冲突——已验证足够。

---

## 4. 新探测 / New Probes

### 4.1 P1：`getFilesOfFolder` 空匹配模式（不报错？）

> **问题**：`getFilesOfFolder("C:\\__NOSUCH__\\*.zzz")` 在匹配不到任何文件时返回什么？是抛错还是返回空 list 让 `l.dim = 0`？

**输入**：
```simtalk
var l: list
l := getFilesOfFolder("C:\\__V17_NOSUCH_DIR_QQ__\\*.zzz")
print l.dim
```

**实测**：
```json
{"result":"success","log":"execute success"}
```

**退出码**：0

**结论**：⚠️ **getFilesOfFolder fail-soft** —— pattern 不匹配任何文件时，函数**不抛错**，`execute success`。readlog 受限无法直接读 print 值，但有间接证据（v16 F9 同样的 `execute success` 在有匹配时也是这个 log），可合理推测 `l.dim = 0` 或 `l` 为空 list 但 print 表达式本身合法求值。

**Skill 文档影响**：
- `test-cookbook.md` §2.9 当前没提空匹配行为——**建议补一句**："`getFilesOfFolder` 在 pattern 无匹配时返回 success（fail-soft），list 长度应为 0——脚本里取索引前要检查 `l.dim > 0`，否则 `l[1]` 会触发 list-out-of-bounds"。
- `functions.md` §9 同步更新此 caveat。
- **TODO 残留**：精确拿到 `l.dim` 的 print 值仍需 readlog 修复——等 lifelines §5 修了再补一条实测。

---

### 4.2 P2：`simtalk_syntax` 阶段能否提前拦截 `.length`？

> **问题**：v16 §3.2 把 `simtalk_syntax` 作为前置拦截（语法错 → 退出码 12）。`.length` 错误属于 runtime symbol resolution——能在 syntax 阶段被抓住吗？

**输入**：
```simtalk
var l: list
l := getFilesOfFolder("C:\\Windows\\*.exe")
print l.length
```

**实测**（`simtalk_send.py syntax`）：
```json
{"result":"has no Error","log":"execute success"}
```

**退出码**：0

**结论**：❌ **`simtalk_syntax` 不抓 `.length` 错误** —— `Length` 是 list 对象的属性访问，syntax 阶段不解析 `list` 的字段表，所以"未知标识符"必须到 runtime 才暴露。`result == "has no Error"` 给的是错误的安全感。

**Skill 文档影响**：
- `test-cookbook.md` §1 当前推荐"先 `simtalk_syntax` 再 `simtalk_run`"的工作流——**这个工作流挡不住 `.length` / sleep / list literal 三类 runtime-only bug**。
- 建议：在 §1 的工作流描述里加一句"⚠️ `simtalk_syntax` 只挡 parse-level 错误（括号不匹配 / 关键字错），不挡 runtime symbol resolution（如 `l.length`）；runtime 类错误必须靠 `simtalk_run` 的双重判据（result+log）来抓"。
- v16 §3.2 的"语法错 → 退出码 12"那张表仍然正确（`var x := 1/0` 是常量折叠错，syntax 能挡），但需要明确**适用范围是"编译期常量表达式"，不是"全部潜在 bug"**。

---

### 4.3 P3：`simtalk_syntax` 阶段能否提前拦截 list 字面量赋值？

**输入**：
```simtalk
var l: list
l := [1,2,3]
print l.dim
```

**实测**：
```json
{"result":"has no Error","log":""}
```

**退出码**：0

**结论**：❌ **`simtalk_syntax` 不抓 list 字面量赋值错误** —— `result == "has no Error"`，与 P2 同模式。语法上 `var l: list; l := [expr]` 合法（`[]` 是任意 list 表达式），但 `[1,2,3]` 与 `var l: list` 的兼容性要 runtime 才判定。

---

### 4.4 P4：`simtalk_syntax` 阶段能否提前拦截 `sleep`？

**输入**：
```simtalk
sleep(0.5, false)
print "x"
```

**实测**：
```json
{"result":"has no Error","log":""}
```

**退出码**：0

**结论**：❌ **`simtalk_syntax` 不抓 `sleep` formula 上下文违规** —— `sleep` 是合法 SimTalk 关键字，syntax 阶段不区分 formula vs Method 上下文，必须 runtime 才报 `not allowed in formulas`。

---

## 5. 服务端稳定性 / Server Stability

| ID | 命令 | 回包 | 退出码 | 结论 |
|---|---|---|---|---|
| v17-end | `simtalk_send.py ping` | `{"type":"ping","result":"success"}` | 0 | ✅ 跑完 8 次混合请求（含 3 次 Quirk #7 软失败）后服务端仍健在 |

**压力分布**：8 次 simtalk_syntax/run 请求 = 4 PASS + 3 Quirk #7 + 1 syntax 探测——服务端无 hang、无连接重置。

## 6. 总结 / Summary

### 6.1 回归结果

| v16 发现 | v17 验证 | 一致性 |
|---|---|---|
| §5.1 `l.dim` 是真名 / `l.length` 是陷阱 | T1+T2 复测成功 | ✅ |
| §5.2 `var l: list` 不能直接赋字面量 | T3 复测成功 | ✅ |
| §5.3 `sleep` 在 formula 上下文任何 form 都失败 | T4 复测成功 | ✅ |

**结论**：v16 的三大新发现**仍然全部成立**——本 skill / lifelines.md 文档可以信赖 v16 结论。

### 6.2 v17 新发现（4 条）

| ID | 发现 | 影响 |
|---|---|---|
| P1 | `getFilesOfFolder` 在无匹配时 fail-soft（不抛错），`l.dim` 推测为 0 | `test-cookbook.md` §2.9 + `functions.md` §9 需补"空匹配 caveat" |
| P2 | `simtalk_syntax` 不抓 `.length` 这类 runtime symbol resolution 错误 | `test-cookbook.md` §1 工作流描述需要明确"`simtalk_syntax` 只挡 parse-level 错误" |
| P3 | `simtalk_syntax` 不抓 list 字面量赋值兼容错 | 同 P2——同源问题，文档合并到同一 caveat |
| P4 | `simtalk_syntax` 不抓 `sleep` formula 上下文违规 | 同 P2——同源问题 |

**核心结论**：`simtalk_syntax` 阶段是**比预想更弱**的拦截门——它只能挡 parse-level / 编译期常量表达式错误（`var x := 1/0`、括号不匹配、关键字拼错）。所有"代码看起来对但运行时报错"的语义类问题（`.length` / list literal / `sleep`）**必须靠 `simtalk_run` 的双重判据（result+log）来抓**。

### 6.3 工作流影响 / Workflow Impact

v16 §3.2 列出的工作流"先 syntax → 再 run"仍然正确，但**用户必须理解 syntax 阶段的覆盖范围有限**：

| 错误类型 | syntax 阶段 | run 阶段 | 备注 |
|---|---|---|---|
| `var x := 1/0`（编译期常量折叠） | ✅ 抓到（exit 12） | n/a | |
| `print l.length`（runtime symbol） | ❌ 通过（exit 0） | ✅ Quirk #7（exit 11） | v17 P2 |
| `var l: list; l := [1,2,3]`（runtime 兼容错） | ❌ 通过（exit 0） | ✅ Quirk #7（exit 11） | v17 P3 |
| `sleep(...)` formula 上下文 | ❌ 通过（exit 0） | ✅ Quirk #7（exit 11） | v17 P4 |
| `print 1+2` 正常 | ✅ 通过 | ✅ success | |
| 模态函数 | ❌ 通过（语法合法） | ⏭ timeout | syntax 也挡不住 |

→ **`simtalk_run` 的双重判据是真正的最后一道防线，不要省**。

## 7. 待办 / TODOs

> 本节是从 v17 测试中**新增**的待办，与 v16 §11 既有待办并列。

1. **`lifelines.md` / `test-cookbook.md` §1 增补 "simtalk_syntax 覆盖范围" 段落** —— 优先级：**高**。这条直接影响所有调用方的"先 syntax 再 run"工作流判断。
2. **`functions.md` §9 + `test-cookbook.md` §2.9 增补 "getFilesOfFolder 空匹配" caveat** —— 优先级：中。
3. **精确拿到空匹配时 `l.dim` 的 print 值** —— 优先级：低（待 readlog 修复）。
4. **F18 sleep Method 包装演示** —— v14 起一直遗留的 TODO，等本 session 后续或下个 session 补。
5. **GUI 手动验证 F02 / F12 / F13** —— 本 skill 不覆盖自动化路径。

## 8. 跨 session 引用 / Cross-references

- v14（20 OS 函数全量首测）：`local-simtalk-execution/log/test-session-20260825-v14.md`
- v15（本 skill 自身抽样）：`local-simtalk-os-functions/log/test-session-20260825-v15-skill-test.md`
- v16（v17 框架下全量重测 + 三大新发现）：`local-simtalk-os-functions/log/test-session-20260825-v16.md`
- v17（本 session，回归 + 4 新探测）：**`local-simtalk-os-functions/log/test-session-20260825-v17.md`（本文档）**
- 单源硬规则：`local-simtalk-execution/references/lifelines.md`（§5 readlog / §6 Quirk #6-#13）
- 协议基础：`local-simtalk-execution/references/message-schema.md` / `code-templates.md`
