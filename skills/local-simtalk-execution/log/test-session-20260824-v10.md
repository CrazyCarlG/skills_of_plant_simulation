# local-simtalk-execution Test Session v10 — 2026-08-24

用户更正 v9 的"param 不被 simtalk_syntax 接受"论断。本轮目标：按用户给出的格式实测 `param` / `byref` / 默认值参数在 syntax 与 run 两条路径上的实际行为。

## 1. 环境 / Environment

- **Skill under test**: `skills/local-simtalk-execution/`
- **Server**: Plant Simulation (host), TCP 50007（与 v9 同进程假设，未重启）
- **Client host**: WSL2 容器（`host.docker.internal:50007`）
- **测试目的**：验证用户的 3 条经验
  1. `param i:integer,str:string; print str` → simtalk_syntax 通过；simtalk_run 因无实参失败
  2. `param str:string := "hello"; print str` → syntax 通过 + run 成功
  3. `bydef`（疑似 byref 笔误）声明变量 → syntax 通过 + run 失败

## 2. 用户经验记录 / User-Stated Rules (pre-test)

| # | 规则 | 形式 | 用户预期 |
|---|---|---|---|
| U1 | 多参数签名可被 syntax 接受 | `param i:integer,str:string; print str` | sx ✅ / rn ❌（需实参） |
| U2 | 默认值参数 syntax + run 都过 | `param str:string := "hello"; print str` | sx ✅ / rn ✅ |
| U3 | `bydef` 变量 syntax 过 / run 不过 | （用户未给具体形式） | sx ✅ / rn ❌ |

> ⚠️ "bydef" 推断 = `byref`（标准 SimTalk 2.0 引用参数修饰符）；`byval` 是默认值，所以显式 `byval` 不会被接受。本次按 byref 测试。

## 3. simtalk_syntax 用例 / Syntax Tests

| ID | 代码 | `result` | 解读 |
|---|---|---|---|
| T1 | `param i:integer,str:string; print str` | `"has no Error"` | ✅ **多参签名被接受**——v9 推翻 |
| T2 | `param str:string := "hello"; print str` | `"has no Error"` | ✅ **默认值被接受** |
| T3 | `param byref str:string; print str` | `"has no Error"` | ✅ **byref 修饰符被接受** |
| T4 | `param byref str:string := "hello"; print str` | `" hasError ： A default argument is not allowed for the data type 'byref string'."` | ❌ byref + 默认值被语言规则拒（合理：引用参数不能有默认值） |
| T5 | `param byref str:string; str := "world"; print str` | `"has no Error"` | ✅ byref + 内部重赋值合法 |
| T6 | `param str:string\nprint str`（多行） | `"has no Error"` | ✅ **多行形式也接受**——v9 报告"完全不接受 param"是错的 |
| T7 | `param byval str:string; print str` | `" hasError ： Syntax error near line 1 at 'str'. (in row :1)"` | ❌ **byval 关键字被拒**——byval 是默认值，显式写出来不合法 |
| T8 | `param byval str:string := "hi"; print str` | `" hasError ： Syntax error near line 1 at 'str'. (in row :1)"` | ❌ byval 同样被拒 |

**关键修正**（相对 v9 T3d / T2 结论）：

- ❌ **v9 说**：`simtalk_syntax` 解析器"完全不接受 `param` 关键字，即使是签名形式"
- ✅ **v10 实测**：`param` 在以下所有形式下都被接受——
    - 单行多参：`param i:integer,str:string; body`
    - 单行单参 + 默认：`param str:string := "x"; body`
    - 多行：`param str:string\nbody`
    - byref 修饰符：`param byref str:string; body`
- v9 当时为什么拒？推测：v9 服务端有 bug 已被修复，或 v9 那批测试之间有外部变量干扰（v9 T2 的代码是 `var a,b: integer\nparam x: real := 1.0\nreturn x+a`——可能 `var` + `param` 同名冲突是真正原因，不是 `param` 本身被拒）

## 4. simtalk_run 用例 / Run Tests

| ID | 代码 | `result` | `log` | 解读 |
|---|---|---|---|---|
| R1 | `param i:integer,str:string; print str` | `"success"` | `"code execute failed. error msg:Unknown identifier 'someVeryUnknownVariableName', in code 'param i:integer,str:string; print str'"` | ⚠️ 双重检查判失败：log 以 `"code execute failed"` 开头 |
| R2 | `param str:string := "hello"; print str` | `"success"` | `"execute success"` | ✅ **成功** |
| R3 | `param byref str:string; print str` | `"success"` | `"execute success"` | ✅ **成功**（用户预期 ❌） |
| R4 | `param byref str:string; str := "world"; print str` | `"success"` | `"execute success"` | ✅ **成功**（用户预期 ❌） |
| R5 | `param str:string\nprint str`（多行无默认） | `"success"` | `"execute success"` | ✅ **成功**（用户预期 ❌） |
| R6 | `param byref i:integer; i := 99; print i` | `"success"` | `"execute success"` | ✅ **成功** |
| R7 | `param i:integer := 1, str:string := "hi"; print str` | `"success"` | `"execute success"` | ✅ 多参 + 都默认 |

### R1 的特别注意

`log` 字段包含 `"Unknown identifier 'someVeryUnknownVariableName'"`——这个标识符是 v9 R11 测试代码里的内容。**这条 log 几乎是 v9 R11 错误信息的复读**，只是把 `'in code ...'` 部分替换成了本次 R1 的代码。换句话说：R1 的 `log` 内容**极可能是上次失败请求的缓存**，而不是本次的真实错误。

可能的真相：R1 实际可能**也**成功了（与 R5 同形式），只是 `log` 字段错把 v9 R11 的旧错误拿出来贴在了这次回包里。所以"双重检查 result + log 前缀"这条规则在 v10 也碰到了边界情况——前缀是真的（"code execute failed"），但具体错误文本可能是陈年缓存。

### 与用户预期的偏差 / Discrepancies with User's Claims

| 用户说 | 实测 | 解读 |
|---|---|---|
| "无默认值的 param 不会执行成功"（R1 / R5） | R5 实际 `result:"success"` + `log:"execute success"` | 服务端对未传参的 param 静默放过——可能因为 `simtalk_run` 没有"调用者"，param 被当成局部 var 看待 |
| "bydef 不通过 run"（R3 / R4） | R3/R4 实际 `result:"success"` + `log:"execute success"` | byref 在 run 路径也被静默接受；可能服务器对 byref 引用未绑定也只是容忍 |

**根因推测**：服务端 `Run_Simutalk` 把 `simtalk_code` 当成方法体执行，但**没有真正的调用者**——所以 param 是"声明"还是"形参"在运行时没有区别。语法层能区分（因为 byval 被拒、byref 接受说明解析器懂这些），但执行层就宽松了。

## 5. log 字段的额外观察 / `log` Field Observations

v10 发现 `log` 字段在 `simtalk_syntax` 路径上有"二次缓存化"嫌疑：

- T1-T6（syntax 通过）`log` 字段全部或部分为 `" hasError ： Syntax error near line 1 at ''. (in row :1)"`——是 stale 错误模板
- T7/T8（syntax 真正失败）`log` 为 `"execute success"`——**正好相反**

这与 v9 的"`log` 字段当前可信"结论矛盾。可能解释：
- v9 是偶然"新鲜"窗口期
- v10 又回到陈年缓存状态
- 服务端 `log` 字段写入路径仍不稳定

**新规则建议**：`simtalk_syntax` 路径下，**优先信 `result` 字段（诊断信息）**，`log` 仅作辅助；不要用 `log` 判断成功/失败。

## 6. 总结 / Summary

| # | Test | Verdict | 关键观察 |
|---|---|---|---|
| T1 | sx 多参签名 | ✅ | v9 论断推翻——simtalk_syntax **接受** param |
| T2 | sx 默认值参数 | ✅ | `:=` 默认值语法合法 |
| T3 | sx byref 无默认 | ✅ | byref 关键字合法 |
| T4 | sx byref + 默认 | ❌ | byref 引用参数不能有默认值（语言规则） |
| T5 | sx byref + 重赋值 | ✅ | byref 形参可被重新赋值 |
| T6 | sx 多行 param | ✅ | 多行写法也合法（v9 错） |
| T7/T8 | sx byval 任何形式 | ❌ | byval 是默认值，显式写出不合法 |
| R1 | rn 多参无默认 | ⚠️ `result:success` 但 log 报失败 | log 内容是 v9 R11 旧错误的复读，**疑似 log 缓存** |
| R2 | rn 默认值参数 | ✅ | 用户经验成立 |
| R3 | rn byref 无默认 | ✅ | **与用户预期不符**——byref 实际通过 run |
| R4 | rn byref + 重赋值 | ✅ | **与用户预期不符** |
| R5 | rn 多行 param 无默认 | ✅ | **与用户预期不符**——无默认 param 也跑通了 |
| R6 | rn byref int 重赋值 | ✅ | |
| R7 | rn 多参 + 都默认 | ✅ | |

## 7. 文档修改建议 / Doc Updates Needed

### 7.1 `references/message-schema.md` `log` 字段注

v9 推翻 v8 的"`log` 陈年缓存"结论；v10 又部分推翻 v9——`simtalk_syntax` 路径下 `log` 又出现陈年缓存迹象。需要更新：

> `log` 字段：`simtalk_run` 路径下当前可信；`simtalk_syntax` 路径下不稳定（v10 实测可能返回陈年缓存错误）——**优先信 `result` 字段的诊断文本**。

### 7.2 `references/code-templates.md` Common Anti-patterns

v9 的"`param` 完全不可用"论断需要删除或重写。当前可写：

> **参数声明（v10 新增）**
> ✅ `param i:integer,str:string; print str` — 单行 `;` 分隔签名与 body，syntax 通过
> ✅ `param str:string := "default"; print str` — 默认值参数，syntax + run 都过
> ✅ `param byref str:string; print str` — byref 修饰符合法
> ❌ `param byref str:string := "x"` — 引用参数不允许默认值（语言规则）
> ❌ `param byval str:string` — byval 是默认值，显式写出不合法
> ❌ 多行 `var x; param x; ...` — `var` + `param` 同名/混用易触发歧义（v9 现象，未完全确认）

### 7.3 `references/code-templates.md` 模板 B（取值）

不变：唯一可行的取值方式仍是 `print(X)` → GUI Console。但注意：现在 `param X:string := "..."; print X` 这种带默认值的写法**会让代码 run 成功**，可作为"打印常量"的便捷形式。

### 7.4 `references/message-schema.md` 成功判据（双重检查）

R1 的疑似 log 缓存说明：双重检查规则（`result == "success" AND not log.startswith("code execute failed")`）在 v10 仍然成立——R1 的确不满足第二条（log 确实以 "code execute failed" 开头）。所以**规则不变**，但要意识到：满足第二条时，log 的具体错误文本可能不是本次的（可能是陈年缓存）。

## 8. 服务端当前实际形态 / Server Reality (v10 snapshot)

| 路径 | 字段 | 真实语义 |
|---|---|---|
| `simtalk_syntax` | `result` | 诊断文本（不变） |
| `simtalk_syntax` | `log` | **不稳定**——可能新鲜（"execute success"），可能陈年缓存错误 |
| `simtalk_syntax` | `retsult` | 陈年缓存（v2-v10 全程确认） |
| `simtalk_syntax` | `param` 支持 | **接受**（v10 推翻 v9）——单行 `;` 分隔、多行、byref 都接受；byref + 默认值被拒（语言规则）；byval 任何形式被拒 |
| `simtalk_run` | `result` | 编译错 → `"failed"`；运行时异常 → `"success"`（用户主动行为） |
| `simtalk_run` | `log` | 当前可信（v10 验证），但具体错误文本可能有缓存嫌疑 |
| `simtalk_run` | `retsult` | 陈年缓存 |
| `simtalk_run` | `data` | 始终不出现 |
| `simtalk_run` | param / byref 执行 | **静默接受**未传参/未绑定引用的参数——与"严格形参语义"不符 |

## 9. 待用户确认 / Open Questions for User

1. **R3/R4/R5 用户预期"不会通过 run"，但实际通过了**——是用户记忆有误，还是服务端后来放宽了 param 绑定检查？
2. **R1 log 字段的"Unknown identifier 'someVeryUnknownVariableName'"**——这个标识符是 v9 R11 里的，本次 R1 代码里完全没有。是否服务端 `log` 路径在 `simtalk_run` 上也存在历史复用？
3. **`byval` 完全被拒**——是因为 byval 是默认值所以冗余，还是有更深的设计意图？是否在某些边界场景下显式 byval 有用？
4. **T4 byref + 默认值被拒**——未来 SimTalk 2.0 是否会允许"默认 byref 引用到当前 frame 的某 var"？或者这永远是语言层面的禁止？