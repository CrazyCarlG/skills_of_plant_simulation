---
last_updated: 2026-08-28
contributors: [@z004bjuu, @plant-simulation-expert]
scope: SimtalkClaude v1/v2 的 Plant Simulation 实测教训、推荐实践与反模式
---

# SimtalkClaude 经验与避坑

## 五、Plant Simulation 侧的实测教训（v1 撞坑，v2 全部继承）

来自 `local-simtalk-read-library` 在实际 dump 这份模型时遇到的问题，不是文档推测。

### 5.1 `&` 只在“方法名 → 方法对象”时用

```simtalk
-- ✅ 正确：Method 名（内容形式）→ Method 对象
&simtalkcode.program
&simtalkcode.hasSyntaxError(...)

-- ✅ 正确：已经是 object 变量 → 直接取属性
var o: object := str_to_obj(".SimtalkClaude.main.SocketServer.m_send")
o.Encrypted
o.Program

-- ❌ 编译错误
&o.Encrypted
```

拿到 `object` 引用后不要再加 `&`。

### 5.2 `readlog` v15+ 批量 `simtalk_run` 会丢内容

批量探测 8 个方法时，`readlog` 的累积 buffer 会因 65536 byte 截断而返回被截断的 JSON envelope，表现为空方法。

**正确做法**：单方法一次 + `sleep(1.2)` 再 `readlog`，或把 batch 拆到 4 以下。长方法、含多行字符串的方法尤其要单方法探针。

### 5.3 `simtalk_run` 运行时异常仍返回 `result:"success"`

`simtalk_run` 的运行时错误从 `log` 字段返回，错误前缀是 `code execute failed. error msg:...`。`result` 字段不能作为唯一成功判据，必须 parse `log`。

### 5.4 `simtalkcode` Method 的 `Program` 会被覆盖

每次 `simtalk_run` 都会把传入代码写到 `.SimtalkClaude.main.SimtalkAction.simtalkcode.Program`，因此它是临时 scratch buffer，不是固定源码。需要看原始代码时，应读 `src/` 模板或在未执行 agent 动作前 dump。

### 5.5 日志文件可能被独占锁：先 copy 再读

```simtalk
var logFilePath := getLogFile
var paths := splitstring(logFilePath, ".")
var copyPath := paths[1] + "_copy.txt"
if copyFile(logFilePath, copyPath)
  result := readStringFromFile(copyPath)
else
  result := "can not read log, the log file might be in use by another program"
end
deletefile(copyPath)
```

不要直接 `readStringFromFile(getLogFile)`；Plant Simulation 可能持有独占句柄。路径含多个点时，建议使用 `getLogFile + ".copy"`，不要依赖 `splitstring` 的前半段。

### 5.6 `json.asString(false)` 的第二参数控制缩进

```simtalk
jsondata.asString(false)  -- 单行紧凑（网络传输）
jsondata.asString(true)   -- 多行带缩进（调试）
```

网络发送应使用 `false`；不要依赖兼容性较差的 `jsondata.toString`。

## 七、值得抄的做法

| 做法 | 出处 | v1 | v2 |
|---|---|---|---|
| 四层目录拆分：connection / main / src / Objects | `.SimtalkClaude` | ✅ | ✅ |
| `||END||` 作为 TCP 帧分隔符 | `m_send` / `m_callback` | ✅ | ✅ |
| 一个 Method 当 scratch buffer | `simtalkcode` | ✅ | ✅ |
| `executenewcallchain(j)` 做动作路由 | `SocketServer.m_callback` | ✅ | ✅ |
| `action_id` 原样回传 | `Run_Simutalk` / `get_simtalk_hasError` | ✅ | ✅ |
| `Server` boolean 让同一份代码跑两种模式 | handler 出口 | ✅ | ✅ |
| `clearConsole + clearLogFile + openConsole` 三连 | `autoexec` / `a_readlog` | ✅ | ✅ |
| ErrorHandler 静默已知错误 | `ErrorHandler` | ✅ | ✅ |
| 探针式 log reader：copy → read → delete | `m_getlog` / `a_readlog` | ✅ | ✅ |
| `m_sendauth` + `m_authback` 鉴权握手 | — | ❌ | ✅ |
| `m_openconnection` 原子化 connect + auth | — | ❌ | ✅ |
| handler 入口校验必填字段 | — | ❌ | ✅ |
| handler 出口清理 JSON 容器 | — | ❌ | ✅ |

## 八、不建议照搬

| 反模式 | 原因 |
|---|---|
| `result: "success"` 即使运行时异常也返回 | agent 必须 parse `log`；建议使用独立 status code |
| `current.~.x.&y.executenewcallchain(j)` 嵌套链 | 路径深后难读、难维护；扁平化为单层 `x.y(j)` |
| 在 receive 回调里用 `print()` 调试 | 输出进入 GUI console，不回到 agent |
| 将“除零 → 1e300”硬编码到 ErrorHandler | 业务语义是模拟器特定的，应配置化 |
| 用 `splitstring` 派生副本名 | 路径可能有多个点；建议 `getLogFile + ".copy"` |
| `m_str_send` 与 `m_send` 并存 | 多种帧格式增加 parser 复杂度；新工程只保留 `m_send` |
| 把 `ServerIP` 写在 Method 源码中 | 应放入 Variable，方便运行时修改 |
| `sig` 字段留空 | 必须实现 HMAC，否则 auth 退化为 no-op |
