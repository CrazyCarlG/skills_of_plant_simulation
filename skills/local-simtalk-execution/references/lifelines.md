# 硬规则 / Hard Rules

> 本文件是 `local-simtalk-execution` 技能的**唯一事实来源**——所有"必须 / 禁止 / 会挂死"的铁律集中在这里。其它文档（SKILL.md / workflow.md / example.md / code-templates.md / message-schema.md）一律用简短引用，**不再重复展开**。
>
> 维护约定：任何"硬规则"变更（服务端行为、连接方式、字段语义）只改本文件 + `message-schema.md`；其它文档的引用关系会自动跟上。

---

## 1. 连接目标 / Connection Target

| 场景 | `--host` | `--port` | 备注 |
|---|---|---|---|
| **WSL2 容器 → Plant Simulation 主机**（默认） | `host.docker.internal` | `50007` | 端口固定；`127.0.0.1` / `localhost` 在容器内会落到容器自身、连接被拒（v1 T0 验证） |
| 其它环境 | 按实际部署 | `50007` | 端口固定 |

## 2. 回复分帧 / Response Framing（必读）

**服务端不会主动关闭 socket**（v2 T4 验证）。`--resp-mode` 必须显式指定为：

```bash
--resp-mode delimiter --resp-delimiter '||END||'
```

- **`eof` 模式（脚本默认）一定超时**——服务端不发 FIN，socket 永远收不到回复结束标记
- **`line` / `fixed` 模式在当前协议下也不可用**
- **请求侧**：`--data` 末尾追加 `||END||`（用 `||END||` 显式分帧）
- **响应侧**：回包以 `||END||` 结尾，分隔符读取后丢弃

## 3. `type` 字段白名单（必读）

请求 `type` 字段只能取以下四个值，**其它任何值都会让服务端静默挂死到 timeout**（v16 bad-07 验证）：

| `type` | 用途 |
|---|---|
| `ping` | 连通性检查 |
| `simtalk_syntax` | 仅编译/语法检查 |
| `simtalk_run` | 真跑一段 SimTalk |
| `readlog` | 拉取 GUI Console 输出 + 日志起始标记 |

**消费规则**：
- **客户端必须**对 `type` 做白名单校验，不要直接发送外部传入的 `type`
- 服务端在 `type` 不在白名单时**不写回包**，必须靠 `--timeout` 兜底
- 这是 **Quirk #13**

## 4. 模态陷阱 / Modal Traps（必读）

以下写法放进 `simtalk_run` 会让服务端阻塞等用户在 GUI 里点 OK，**socket 永远没回包**：

| 写法 | 为什么挂死 | 规避 |
|---|---|---|
| `prompt("...")` | 弹出 GUI 模态框等点击 | 用 `print` 输出 |
| `infoBox("...")` | 同上 | 同上 |
| `promptList1(...)` / `promptListN(...)` | 同上 | 同上 |
| `MyAttr := X` 写**尚未声明**的全局 attribute | Plant Simulation 弹"是否创建 MyAttr？"模态框 | 用局部 `var`；或先在 GUI 手工建好 attribute |

> ⚠️ **陷阱特征**：`simtalk_syntax` 不需要 namespace 上下文，所以这些代码**语法检查能过**——陷阱只在执行时触发。

## 5. 当前 readlog 状态（v15 回归，⚠️ 不可信）

| 版本 | readlog 行为 |
|---|---|
| **v13**（短暂修复） | ✅ 独立缓冲 + 重置 + 捕获 GUI Console `print(...)` 输出 |
| **v15+**（当前服务端构建 2606.0002） | ⚠️ **回归** —— 反馈循环 + buffer 体积爆炸 + **捕获不到 print 值** |

**消费规则**（当前）：
- ⚠️ **不要**依赖 readlog 拉取 `print(...)` 实际值——可能拿不到、可能拿到陈年 I/O trace、可能 buffer 体积爆炸
- ⚠️ **不要**把 readlog 写进自动化循环——v15 回归下 buffer 体积指数膨胀（65536 字节上限截断）
- ✅ **可以**在调试时调一次 readlog 看服务端有没有响应
- 取 `print(...)` 实际值的替代方案：去 Plant Simulation GUI Console（Window ribbon → Console 按钮）肉眼读

## 6. 通用成功判据（Quirk #6 / #7）

按请求 `type` 分支：

| 请求 `type` | 成功判据 |
|---|---|
| `simtalk_syntax` | `"hasError" not in result`（`result` 是诊断文本，例如 `"has no Error"`） |
| `simtalk_run` | **双重检查**：`result == "success" AND not log.startswith("code execute failed")`（⚠️ Q-001 例外：编译期错误会返回 `result:"failed"` + 退出码 10） |
| `ping` | `type == "ping" AND result == "success"` |
| `readlog` | `result == "success"`（⚠️ v15 不可信；v15+ 上常返回退出码 20 但 stdout 仍有效 — 见 Q-002） |

**禁忌**：
- ❌ **永远不要读 `data` 字段**——`simtalk_run` 的 `data` 始终为空（Quirk #6 实测不变）
- ❌ **永远忽略 `retsult` 字段**——服务端缓存的历史诊断，与本次请求无关（Quirk #5）

### Q-001 — 编译期错误 vs Quirk #7 的边界

`simtalk_run` 在 **编译期错误**（literal `1/0`、声明位置使用未声明标识符、内置函数 arity 不匹配等）下返回的是 `result:"failed"` + 退出码 **10**，**不是** Quirk #7 的 `result:"success"` + `log:"code execute failed..."` 软失败模式。

经验法则：**Quirk #7 只对运行时异常触发**——编译器看不到坏值的情况（如除以运行时变量、未触发分支等）。遇到 literal 上的非法表达式，直接信退出码 10 + `result:"failed"`，别走 Quirk #7 的解析路径。

证据：`log/2026-08-27_ping-syntax-run-readlog-2.md` Step 6（`run '1/0'` exit=10, result=failed — 编译期除零检测，**不是** Quirk #7）。

实操建议：**始终检查 `log` 字段**，不只看 `result` —— 编译期错误时 `result` 反映"失败"，但 `log` 仍携带可读诊断信息。

### Q-002 — v15+ 上 readlog 退出码 20 但 stdout 仍有效

v15+ 回归下 `simtalk_send.py readlog` 经常返回退出码 **20**（`readlog_unreliable_warning`），但 stdout 仍携带完整的 log 内容——只是内容是陈年的 I/O trace，不是本次运行的输出。

硬规则：**退出码 20 视为读取成功**。客户端解析应当：

```python
rl_proc = subprocess.run(["simtalk_send.py", "readlog"], ...)
if rl_proc.returncode not in (0, 20):
    envelope["error"] = "readlog_fetch_failed"
    return envelope
log_text = rl_proc.stdout  # 退出码 20 也用 stdout
```

不要把退出码 20 当作硬失败而丢弃 stdout——那样会同时丢失本次 run 的合法输出和陈年 trace，对调试更有价值。

证据：`log/session-20260826.md` Part B Bug #2 修复 lines 113-137（class-management 的 `if rl_proc.returncode not in (0, 20)` 模式）。

## 7. 字段命名备忘 / Field Naming

| 字段 | 拼写 | 备注 |
|---|---|---|
| SimTalk 代码字段 | **`simtalk_code`** | 不是 `simtalk`，不是 `expression`（v2 修正） |
| `type` 字符串 | snake_case | 取值见 §3 |
| `action_id` | 推荐 uuid4 hex | 服务端原样回显，用于请求↔响应配对 |
| `simtalk_syntax` 的可选 `target_path` | 例：`.Models.Model.m` | 限定到某个对象做解析 |
| `simtalk_run` 的可选 `context_path` | 例：`path.to.Machine` | 执行上下文 |
| `simtalk_run` 的可选 `return_value:true` | —— | **实测无效**（Quirk #6），`data` 字段永远不出 |

## 8. 常见反模式 / Common Anti-patterns（速查）

| ❌ 反模式 | ✅ 替代 |
|---|---|
| shell 里直接写未转义的真换行 | `\n` 转义或 Python 拼 JSON |
| 同一 `action_id` 复用 | 每次 `uuid4().hex` |
| 默认 10s `--timeout` 跑长仿真 | 显式 `--timeout 600` 之类 |
| 失败后立刻同 payload 再发 | 看 `log`、改代码、再发 |
| 请求末尾漏 `\|\|END\|\|`，或读回包未指定 `--resp-delimiter` | 见 §2 |
| `simtalk_run` 里写 `prompt` / `infoBox` / `promptList*` | 见 §4 |
| `simtalk_run` 写未声明的全局 attr | 见 §4 |
| `simtalk_run` 只写 `return X` 无 `-> T` 声明 | 加 `-> integer\nreturn X`（v8 修正） |
| 把 readlog 当"完整历史"拉 | 见 §5 |

## 9. 退出码 / Exit Codes

`scripts/socket_client.py` 退出码：

| 退出码 | 含义 |
|---|---|
| `0` | 成功（stdout 是原始回复字节） |
| `1` | `TIMEOUT`（在 `--timeout` 内未收到完整回复） |
| `2` | `ERR: cannot connect` / 参数错误 |
| `3` | `ERR: connection closed before reply` |

> ⚠️ 退出码 `0` **不代表语义成功**——只代表 socket 收到了 `||END||` 帧。语义成功/失败必须按 §6 的判据检查 `result` / `log` 字段。

---

## 10. List API 陷阱 / List API Traps（v16 新增）

Plant Simulation `list` 对象的命名与其它语言（Java / Python / JS / C#）不一致——从其它语言迁移的代码极易踩坑：

### 10.1 长度查询：`.dim` 不是 `.length`

```simtalk
var l: list
l := getFilesOfFolder("C:\\Windows\\*.exe")
print l.dim        -- ✅ 正确：返回 list 元素数量
print l.length     -- ❌ 触发 Quirk #7：`code execute failed. error msg:Unknown identifier 'Length'`
print l.size       -- ❌ 同上：`Unknown identifier 'Size'`
print l.count      -- ❌ 同上：`Unknown identifier 'Count'`
```

**硬规则**：
- Plant Simulation `list` **只有 `.dim` 一个内置属性**——`dim` 是"dimension"的缩写
- 其它语言常见的 `.length` / `.size` / `.count` **全部不存在**
- `l.length` 等写法会触发 Quirk #7 软失败（`result=success` 但 `log=code execute failed`）

### 10.2 List 字面量不能直接赋给 `var l: list`

```simtalk
var l: list; l := [1,2,3,4,5]            -- ❌ "Left and right sides of the assignment are incompatible."
var l: list[integer]; l := [1,2,3,4,5]   -- ❌ 同上：即使 typed list 也拒绝字面量
var l: list; make l := [1,2,3,4,5]       -- ❌ 语法错："Syntax error near line 1 at 'l'"

var l: list
l := getFilesOfFolder("C:\\Windows\\*.exe")   -- ✅ 走 list-returning 函数
print([1,2,3,4,5])                            -- ✅ 字面量在函数实参位置合法
```

**硬规则**：
- Plant Simulation 不允许把数组字面量 `[1,2,3]` 直接赋给 `list` / `list[T]` 变量——只能通过 list-returning 函数（`getFilesOfFolder` / `makeList` / 表/Table 操作）构造
- 字面量语法仅在**实参**位置合法（`print([1,2,3])`、`foo([1,2,3])`）
- 字面量赋值的失败同样触发 Quirk #7 软失败（`log` 报 `Left and right sides of the assignment are incompatible.`）

### 10.3 print 行为

| 写法 | 输出 |
|---|---|
| `print l`（l 是 list） | 只打类型名（如 `FilesOfFolder`），**不展开元素**——见 v14 Finding #1 |
| `print l.dim` | 打整数（list 维度） |
| `print l[1]`, `print l[2]`, ... | 按索引逐个打元素 |

> ⚠️ 三条规则共同作用：`getFilesOfFolder(...) → list` 拿到 list 后，要拿元素 / 长度必须用 `l[i]` / `l.dim`——其它语言常见的 `for x in l: print(x)` 这种迭代语法在 `simtalk_run` 的 formula eval 上下文里也受限制（需用 Method 上下文或 `for`/`while` 控制流）。

---

## 12. 命名空间保护 / Namespace Protection（v17+ 新增）

**铁律**：任何路径以 `.SimtalkClaude` 开头（**包括但不限于** `.SimtalkClaude` / `.SimtalkClaude2` / `.SimtalkClaude3` …）一律视为**禁写**。

| 路径前缀 | 性质 | 处置 |
|---|---|---|
| `.SimtalkClaude.*` | SimTalkClaude 1.x 运行时（legacy） | ❌ 禁止读写——会破坏 TCP 桥 |
| `.SimtalkClaude2.*` | SimTalkClaude 2.x 运行时（当前活跃） | ❌ 禁止读写——会破坏 TCP 桥 + 反射 runtime |
| `.SimtalkClaude3.*` … | 未来版本（未部署） | ❌ 默认禁写，部署后再评估 |

**为什么这么严**：
- 两个命名空间容易混淆（`.SimtalkClaude` vs `.SimtalkClaude2` 都"看着像 SimTalkClaude 的家"），2026-08-27 ping-syntax-run 实测在 `simtalk_syntax` 的 stale `log` 里就看到了 `.SimtalkClaude2.Objects` 的 8-child Folder dump。
- `.SimtalkClaude2.Objects.*`（Method/Socket/DataList/Dialog/HtmlReport/Variable/Button/DataTable）是反射模板，外观像普通 Frame，agent 容易误判为可写对象。
- 任何 `\d` 后缀都视为同族风险——历史已出现 `SimtalkClaude` → `SimtalkClaude2` 的扩展，未来仍可能继续。

**怎么走是对的**：
- ✅ 通过受控的协议 verb（`ping` / `simtalk_syntax` / `simtalk_run`）访问 runtime 功能
- ❌ **不要**直接 `str_to_obj(".SimtalkClaude2.*")` 然后 `.program := ...`
- ❌ **不要**把这些路径当作 BFS 的 leaf 写入（read-only 探测可以，写入一律拒）

**配合 §5**：v15+ readlog 退化下，stale log 可能含 `.SimtalkClaude\d.*` 的历史 dump——这只是让你看到，不代表可写。

---

## 11. 变更日志 / Changelog

| 日期 | 变更 |
|---|---|
| 2026-08-25 | v17 重构：抽出本文件作为硬规则唯一来源；同步 v15 readlog 回归、v16 Quirk #13 / 异常抛出矩阵 |
| 2026-08-27 | v17.1 新增 §12 命名空间保护：`.SimtalkClaude\d*` 全部禁写（基于 delta-r2 实测 stale log 含 `.SimtalkClaude2.Objects`） |
| 2026-08-25 | v16 发现：未知 type 值静默挂死 → §3 Quirk #13 |
| 2026-08-25 | v16 发现：list 长度查询 `.dim`（不是 `.length`）+ list 字面量不可赋 → §10 新增章节 |
| 2026-08-25 | v15 发现：readlog v13 修复在当前服务端构建下回归 → §5 |
| 2026-08-24 | v9 发现：写未声明全局 attr 触发模态对话框 → §4 |
| 2026-08-24 | v8 修正：`return X` 必须配 `-> T` 声明 |
| 2026-08-24 | v2 修正：字段名是 `simtalk_code`、回复分帧必须用 delimiter 模式 |
| 2026-08-24 | v1 发现：WSL2 容器必须用 `host.docker.internal` |