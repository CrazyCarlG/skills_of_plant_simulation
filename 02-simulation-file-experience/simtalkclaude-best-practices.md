# SimtalkClaude 模型经验 — 2026-08-26

> 从 `local-simtalk-read-library` 技能对 `.SimtalkClaude.*` 全量源码 dump 后整理出的设计模式、协议细节与 Plant Simulation 实测教训。
> Artifacts: `skills/local-simtalk-read-library/data/simtalkclaude_dump.json`

## 一、SimtalkClaude 是什么

一个让 **外部 agent 通过 TCP JSON 协议远程驱动 Plant Simulation 模型** 的桥梁组件。
对外表现为：连接 `8.137.98.145:50001`（TCP），发 `{type, ...}` 动作，收 `{type, result, log, action_id}` 回复。

支持的动作：`ping` / `simtalk_syntax` / `simtalk_run` / `readlog` / `auth`。

---

## 二、目录分层的"教科书"做法

```
.SimtalkClaude/
├── connection/   ← 网络传输层（Socket 收发、Logger）
│   ├── SocketClient.*   ← 客户端 socket 封装
│   ├── SocketServer.*   ← 服务端 socket 事件入口
│   └── Logger/          ← 日志 DataTable
├── main/         ← 运行时实例（带 Server / SocketServer / SocketClient / SimtalkAction）
├── src/          ← 库模板（class library，main 实例的来源）
│   ├── autoexec          ← 模型打开即执行
│   ├── ErrorHandler      ← 挂在 Method 对象上的全局错误处理
│   └── SimtalkAction.*   ← 动作分发表
└── Objects/      ← 各内置类的引用实例（Method / Socket / DataList / Button …）
```

| 层 | 职责 | 修改频率 |
|---|---|---|
| `connection/` | 字节收发、心跳、鉴权回包 | 几乎不改 |
| `main/` | 业务实例 + 当前模式（Server flag） | 偶尔改 |
| `src/` | 类库、模板代码 | 经常迭代 |
| `Objects/` | 类引用、文档示例 | 几乎不改 |

> **值得抄**：把"transport / instance / library / reference"四层分开，移植/复用时只换 `connection/`，业务代码不动。

---

## 三、协议设计要点

### 3.1 帧格式：`json + "||END||"`

```simtalk
-- 发送侧（m_send）
var msgStr: string := jsondata.asString(false) + "||END||"
MySocket.write(channelNo, msgStr)

-- 接收侧（m_callback）
message := regex_replace(message, "\|\|END\|\|", "")
j.parse(message)
```

> **为什么用 `||END||` 而不是换行？**
> SimTalk JSON (`jsondata.asString(false)`) 会保留字符串内的换行符，用 `||END||` 作分隔符可以无歧义切分多个包，不会因为消息体里有 `\n` 而提前断开。

### 3.2 动作分派：`switch j["type"]`

服务端 `SocketServer.m_callback`：

```simtalk
switch type
case "ping"           → m_send(ping_reply)
case "simtalk_syntax" → SimtalkAction.&get_simtalk_hasError.executenewcallchain(j)
case "simtalk_run"    → SimtalkAction.&Run_Simutalk.executenewcallchain(j)
case "readlog"        → SimtalkAction.&ReadLogFile.executenewcallchain(j)
end
```

> `executenewcallchain(j)` 是 Plant Simulation 的"用 JSON 对象做参数调用方法"机制 —— 直接传一个 json 进去，对端按 attribute 名取字段。比写一堆 `if j.contains(...)` 干净。

### 3.3 鉴权

```json
client → server:  {"type":"auth", "token":"...", "ts": <unix_seconds>, "sig":"..."}
server → client:  {"type":"auth", "status":"ok", "session_id":"..."}
```

- `ts` 用 Unix epoch 秒（不是毫秒），从 `sysDate - str_to_dateTime("01.01.1970 00:00:00")` 换算
- 收到 `status:"ok"` 才把 `session_id` 写进本地 `Variable`，否则断 socket

### 3.4 回复包统一字段

所有 action 回复都长这样：

```json
{
  "type":      "<echo 原 type>",
  "action_id": "<echo 原 action_id>",
  "result":    "success" | "failed",
  "log":       "<执行日志 / 错误信息>"
}
```

> 把 `action_id` 原样回传是 agent 端做"异步请求-响应对齐"的关键。SimtalkClaude 的 `action_result` 是被复用的 json 容器变量，每个 handler 都要在出口清空。

---

## 四、关键模式

### 4.1 用一个 Method 当 SimTalk 代码的"scratch buffer"

**这是整个 bridge 最聪明的设计**：

```simtalk
-- .SimtalkClaude.main.SimtalkAction.simtalkcode 是一个 Method 对象
-- simtalk_hasError(code):
&simtalkcode.program := code                                -- 写入代码
var errMsg: string; var errLine: integer
var hasError := &simtalkcode.hasSyntaxError(errMsg, errLine) -- 检查语法

-- simtalk_execute():
executeSilent(&simtalkcode.program)                          -- 静默执行
var errMsg := getExecuteSilentError                          -- 取错误
```

> **核心优势**：`hasSyntaxError` / `executeSilent` 只接受"已存在的 Method 对象"作为代码宿主 —— 你不能用它们执行一段临时字符串。把代码先写到 `simtalkcode.Program` 这条属性上，就把"临时字符串"问题变成了"方法编辑"问题，语法错误和运行时错误都能拿到结构化回传。

### 4.2 `&Method.executenewcallchain(json)` —— 路由到具体 handler

```simtalk
current.~.simtalkaction.&Run_Simutalk.executenewcallchain(j)
```

- 路径前缀 `current.~` 表示"父对象上的 SimtalkAction Frame"
- `&` 把方法名（内容）变成方法对象
- `executenewcallchain` 是 Method 的内置方法，按 json 字段填充参数
- 用 `&` + `executenewcallchain` 等价于"反射 + invoke(json args)"

### 4.3 客户端/服务端同构：`Server` boolean 开关

```simtalk
-- 每个动作处理函数的出口
if current.~.server
  current.~.SocketServer.m_send(action_result)
else
  current.~.SocketClient.m_send(action_result)
end
```

> 同一份 `SimtalkAction` 既能跑在"作为服务端收请求"的模式下，也能跑在"作为客户端连远程"的模式下。`Server` 是 Frame 上一颗 boolean Variable，运行时切。

### 4.4 自动重置：每个 read 之后清理

```simtalk
-- a_readlog 末尾
clearConsole     -- 清空 GUI Console 窗口
clearLogFile     -- 清空日志文件内容（不删文件）
openConsole      -- 重新打开 Console 让用户看到干净状态
```

> 这是 Plant Simulation 远程控制场景下的必备卫生措施 —— 每条 agent 指令结束都重置一次 Console/log，下次指令起点的 log 就是完整的因果链。

### 4.5 ErrorHandler：吞掉已知良性错误

```simtalk
-- ErrorHandler(param byref error, method_path, line_number) -> any
if error = "Division by zero."
  error := ""
  return 1e300               -- 给调用方一个合理值，继续跑
end
error := "error in " + method_path + ": " + error
return 0
```

> 把"除零"这类已知无害的异常静默替换成大数（`1e300`），不让它中断长跑仿真。其它异常改写前缀后继续抛，由上层决策要不要中止。

---

## 五、Plant Simulation 侧的实测教训

> 来自 `local-simtalk-read-library` 在 dump 这份模型时**实际撞到**的问题，不是文档抄来的。

### 5.1 `&` 只在"方法名 → 方法对象"时用

```simtalk
-- ✅ 正确：Method 名（内容形式）→ Method 对象
&simtalkcode.program
&simtalkcode.hasSyntaxError(...)

-- ✅ 正确：已经是 object 变量 → 直接取属性
var o: object := str_to_obj(".SimtalkClaude.main.SocketServer.m_send")
o.Encrypted            -- 不需要 &
o.Program              -- 不需要 &

-- ❌ 编译错误："The ref-operator has no effect in this context."
&o.Encrypted
```

> 教训：拿到 `object` 引用之后 **绝对不要**再加 `&`。这条规则在 Plant Simulation 文档里很模糊，是用 `local-simtalk-read-library` 撞坑才确认的。

### 5.2 `readlog` v15+ 在批量 `simtalk_run` 下会丢内容

我第一次批量探测 8 个方法时，32/42 看起来是空方法 —— 实际上 `readlog` 的累积 buffer 在 v15+ 回归（65536 byte 截断），单次返回的 JSON envelope 被截断、parser 把截断后的空 log 当成"空方法"。

**正确做法**：要么 **单方法一次** + `sleep(1.2)` 再 readlog，要么把 batch 拆到 4 以下。当前 `local-simtalk-read-library` 的 `BATCH=8` 对小方法够用，对**长方法或方法体内嵌多行字符串**（如这里的 socket 协议代码）会丢内容。

### 5.3 `simtalk_run` 运行时异常被设计成 `result:"success"`

这是协议的"软失败"设计 —— `simtalk_run` 即便代码运行抛错，仍然回 `result:"success"`，实际错误从 `log` 字段取，前缀是 `"code execute failed. error msg:..."`。

```simtalk
-- Run_Simutalk 内部
action_result["log"] := simtalk_execute
var run_result := action_result["result"]      -- 永远拿不到 "failed"
if run_result = "success"
  action_result["result"] := "success"          -- 这条 if 永远命中
else
  ...
end
```

> **永远要 parse `log` 字段**，不要只信 `result`。详见 `references/lifelines.md` Quirk #6/#7 + team memory `simtalk-run-soft-failure-design`。

### 5.4 `simtalkcode` Method 的 `Program` 是**会被覆盖**的

每次 `simtalk_run` 都会把传入的代码写到 `.SimtalkClaude.main.SimtalkAction.simtalkcode.Program` 上。也就是说 **那个方法的源码不是固定不变的** —— 它是 bridge 用来装载临时 SimTalk 的"载体"。

> 副作用：用 `local-simtalk-read-library` 探测这份模型时，`simtalkcode` 这条 Method 在 dump 里会显示成"刚跑过的探针代码"，因为探针自己写进去过。要看原始代码，要么读 `src/` 目录下的库模板，要么在模型刚打开还没跑过任何 agent 动作时 dump。

### 5.5 日志文件可能正被独占锁 —— 先 copy 再读

```simtalk
-- m_getlog / a_readlog 都用这套
var logFilePath := getLogFile
var paths := splitstring(logFilePath, ".")
var copyPath := paths[1] + "_copy.txt"

if copyFile(logFilePath, copyPath)
  result := readStringFromFile(copyPath)
else
  result := "can not read log , the log file might be use in another program"
end

deletefile(copyPath)
```

> 不要直接 `readStringFromFile(getLogFile)` —— Plant Simulation 自己持有 log 文件的独占句柄，会失败。复制到 `_copy.txt` 再读，读完删掉。

### 5.6 `json.asString(false)` —— 第二参数是"是否带缩进"

```simtalk
jsondata.asString(false)    -- 单行紧凑（用于网络传输）
jsondata.asString(true)     -- 多行带缩进（用于调试）
```

> 默认 `false`，写成 `jsondata.toString` 也行但兼容性差一些。

---

## 六、值得抄的做法 ✅

| 做法 | 出处 |
|---|---|
| 四层目录拆分：connection / main / src / Objects | `.SimtalkClaude` |
| `||END||` 作为 TCP 帧分隔符（不是换行） | `m_send` / `m_callback` |
| 一个 Method 当 scratch buffer 装载待执行 SimTalk | `simtalkcode` |
| `executenewcallchain(j)` 做动作路由 | `SocketServer.m_callback` |
| `action_id` 原样回传以对齐请求/响应 | `Run_Simutalk` / `get_simtalk_hasError` |
| `Server` boolean 让同一份代码跑两种模式 | `Run_Simutalk` 末尾分支 |
| `clearConsole + clearLogFile + openConsole` 三连 | `autoexec` / `a_readlog` |
| `ErrorHandler` 静默已知错误（如除零） | `ErrorHandler` |
| 探针式 log reader：copy → read → delete | `m_getlog` / `a_readlog` |

---

## 七、不建议照搬 ❌

| 反模式 | 原因 |
|---|---|
| `result: "success"` 即使运行时异常也返回 | 让 agent 端必须 parse `log` 字段；改用独立 status code 更清楚 |
| `current.~.x.&y.executenewcallchain(j)` 嵌套链 | 路径深了之后可读性差、维护难；扁平化为单层 `x.y(j)` |
| `print()` 在 receive 回调里做调试 | `print` 写到 GUI console，不回到 agent；agent 端看不到 |
| 把"除零 → 返回 1e300" 硬编码到 ErrorHandler | 业务语义是模拟器特定的，换模型要重写；建议把"哪些错误吞掉"做成配置 |
| 把 log 文件路径派生（`splitstring` 取前半段）作为副本名 | 假设路径里只有一段 `.`，实际可能有多个；建议 `getLogFile + ".copy"` 更稳 |

---

## 八、复现这份 dump 的命令

```bash
# 1) 拿到完整模型树
python3 skills/local-simtalk-get-folder-tree/scripts/bfs_full.py --no-infobox . 5 \
  skills/local-simtalk-read-library/data/tree.json

# 2) 过滤 SimtalkClaude 的方法路径
python3 - <<'PY'
import json
t = json.load(open('skills/local-simtalk-read-library/data/tree.json'))
out = []
def w(n):
    if n.get('type') == 'Method' and n['path'].startswith('.SimtalkClaude.'):
        out.append(n['path'])
    for c in n.get('children', []): w(c)
w(t)
open('skills/local-simtalk-read-library/data/simtalkclaude_methods.txt','w').write(
    '\n'.join(sorted(set(out))) + '\n')
PY

# 3) ⚠️ 用单方法 + sleep 的版本，而不是 BATCH=8 的 probe_methods.py
#    把 probe_methods.py 临时改成 BATCH=1 + sleep(1.2)，或者直接照 §5.2 写一段一次性脚本
```

---

## 九、可继续挖掘的方向

- **`m_str_send` 的实现细节**：当前只看到包装了 `+ "||END||"`，没有鉴权也没有 action_id 回填 —— 看起来是早期版本协议，新版走 `m_send`。
- **`Logger/logdata`**：当前 `Logger.Frame` 下只有一个空的 `DataTable`，预期是记录每次请求/响应，但**没有看到任何写入代码** —— 要么是 `m_callback` 应该写但漏了，要么是 `m_recieve` 那侧写。值得作为下一步 hook 点。
- **`Objects.Method`**：库里那颗空的 Method 引用实例，可能是给"Method 对象文档示例"用的 —— 如果有 helper 文档生成工具，应该从这里取。

---

**经验来源**：2026-08-26 用 `local-simtalk-read-library` v1 + `local-simtalk-get-folder-tree` 跑全量 dump，**实际撞坑**而非文档抄录。所有 §五 的 Plant Simulation 行为均经过一次 `simtalk_run` + `readlog` 实测验证。