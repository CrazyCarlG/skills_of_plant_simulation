---
last_updated: 2026-09-01
contributors: [@plant-simulation-expert]
scope: SimtalkClaude 桥的 Plant Simulation 实测教训、推荐实践与反模式(11 类 Quirk + 12 项推荐 + 8 个反模式)
---

# SimtalkClaude 运营模式与坑

本文档整合 SimtalkClaude 桥在 Plant Simulation 上的**实测教训、推荐做法与反模式**。

## 一、Plant Simulation 侧实测教训(11 类 Quirk)

### 1.1 `&` 只在"方法名 → 方法对象"时用

```simtalk
-- ✅ 正确:Method 名(内容形式)→ Method 对象
&simtalkcode.program
&simtalkcode.hasSyntaxError(...)

-- ✅ 正确:已经是 object 变量 → 直接取属性
var o: object := str_to_obj(".SimtalkClaude.main.SocketServer.m_send")
o.Encrypted            -- 不需要 &
o.Program              -- 不需要 &

-- ❌ 编译错误:"The ref-operator has no effect in this context."
&o.Encrypted
```

### 1.2 `readlog` v15+ 批量 `simtalk_run` 会丢内容

批量探测 8 个方法时,`readlog` 的累积 buffer 会因 65536 byte 截断而返回被截断的 JSON envelope,表现为空方法。

**正确做法**:单方法一次 + `sleep(1.2)` 再 `readlog`,或把 batch 拆到 4 以下。长方法、含多行字符串的方法尤其要单方法探针。

### 1.3 `simtalk_run` 运行时异常仍返回 `result:"success"`

`simtalk_run` 的运行时错误从 `log` 字段返回,错误前缀是 `code execute failed. error msg:...`。`result` 字段不能作为唯一成功判据,必须 parse `log`。

> **致命陷阱**:永远只看 `result == "success"` 就以为成功——这会漏掉 100% 的运行时异常。

### 1.4 `simtalkcode` Method 的 `Program` 会被覆盖

每次 `simtalk_run` 都会把传入代码写到 `.SimtalkClaude.main.SimtalkAction.simtalkcode.Program`,因此它是临时 scratch buffer,不是固定源码。需要看原始代码时,应读 `src/` 模板或在未执行 agent 动作前 dump。

### 1.5 日志文件可能被独占锁:先 copy 再读

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

不要直接 `readStringFromFile(getLogFile)`;Plant Simulation 可能持有独占句柄。路径含多个点时,建议使用 `getLogFile + ".copy"`,不要依赖 `splitstring` 的前半段。

### 1.6 `json.asString(false)` 的第二参数控制缩进

```simtalk
jsondata.asString(false)  -- 单行紧凑(网络传输)
jsondata.asString(true)   -- 多行带缩进(调试)
```

网络发送应使用 `false`;不要依赖兼容性较差的 `jsondata.toString`。

### 1.7 `.execute()` 不刷新 `.Program` 编译缓存

写入新 `.Program` 后调用 `.execute()` 仍跑**首次编译**的旧版本——即使 `.Program` 已更新、`simtalk_syntax` 验证编译通过、`.execute()` 的 wrapper 是合法的。

**唯一可靠路径**:走 `executeSilent(str_to_obj(...).Program)` 模式——永远 fresh compile,无缓存问题。`executeSilent(<expr>)` 内 `print` 也不通过桥转发,必须用 `getExecuteSilentError` 捕获 error。

### 1.8 `simtalk_run` 单语句限制

`for/next` / `if/then/end` block 全部 "Syntax error near 'print'"——必须外层 shell 循环 + 多次 send。

```bash
# canonical 模式:外层 shell for-loop + 每次 send 一个最小语句
python3 simtalk_send.py run 'print "###START###"'
for i in $(seq 1 N); do
    python3 simtalk_send.py run "var n := str_to_obj(\".X\").node(${i}); ..."
done
python3 simtalk_send.py run 'print "###END###"'
```

### 1.9 TCP 服务端口可手动 rebind(50007 → 50009)

Plant Simulation 端 `.SimtalkClaude2` Frame 的 init 代码里 `mySocket.create("<port>")` 是 user-editable Variable。任何 hardcode `--port 50007` 的 skill 在用户切端口后全部失败。

**判定**:`simtalk_send.py ping` timeout → 检查 `--host`,再 wide-scan port;看到 TCP accept OK 但所有 simtalk_call timeout → zombie port。

### 1.10 inner `executeSilent(<expr>)` 内的 print 完全不通过桥转发

`executeSilent` 是"静默执行"模式——它有独立的 error 缓冲区 + 独立的 print 缓冲区,**不**走 server-side handler 的"stdout → bridge log"转发通道。

**canonical 模式**:

```simtalk
executeSilent("<sim_code>")
var err := getExecuteSilentError
if err /= ""
  print "runtime error: " + err    -- outer scope print,会被转发
end
```

### 1.11 Bridge JSON 层在大 batch probe 后卡死

跑完大 batch 探针后,服务端 TCP `host.docker.internal:50007` 仍显示 `CONNECTED`(accept() 工作),但任何后续 `simtalk_run` / `readlog` 全部 timeout / JSON decode error。

**Mitigation**:
1. 立刻停手,不要 retry
2. Mitigation A:在 batch 之间插 ping
3. Mitigation B:调长 timeout(默认 10s → 30s)
4. Mitigation C:调 Server.Reconnect
5. 终极方案:用户手动重启 Plant Simulation server

## 二、值得抄的 12 项推荐做法

| 做法 | 出处 | v1 | v2 |
|---|---|---|---|
| 四层目录拆分:connection / main / src / Objects | `.SimtalkClaude` | ✅ | ✅ |
| `\|\|END\|\|` 作为 TCP 帧分隔符 | `m_send` / `m_callback` | ✅ | ✅ |
| 一个 Method 当 scratch buffer | `simtalkcode` | ✅ | ✅ |
| `executenewcallchain(j)` 做动作路由 | `SocketServer.m_callback` | ✅ | ✅ |
| `action_id` 原样回传 | `Run_Simutalk` / `get_simtalk_hasError` | ✅ | ✅ |
| `Server` boolean 让同一份代码跑两种模式 | handler 出口 | ✅ | ✅ |
| `clearConsole + clearLogFile + openConsole` 三连 | `autoexec` / `a_readlog` | ✅ | ✅ |
| ErrorHandler 静默已知错误 | `ErrorHandler` | ✅ | ✅ |
| 探针式 log reader:copy → read → delete | `m_getlog` / `a_readlog` | ✅ | ✅ |
| `m_sendauth` + `m_authback` 鉴权握手 | — | ❌ | ✅ |
| `m_openconnection` 原子化 connect + auth | — | ❌ | ✅ |
| handler 入口校验必填字段 | — | ❌ | ✅ |
| handler 出口清理 JSON 容器 | — | ❌ | ✅ |

## 三、8 个不建议照搬的反模式

| 反模式 | 原因 |
|---|---|
| `result: "success"` 即使运行时异常也返回 | agent 必须 parse `log`;建议使用独立 status code |
| `current.~.x.&y.executenewcallchain(j)` 嵌套链 | 路径深后难读、难维护;扁平化为单层 `x.y(j)` |
| 在 receive 回调里用 `print()` 调试 | 输出进入 GUI console,不回到 agent |
| 将"除零 → 1e300"硬编码到 ErrorHandler | 业务语义是模拟器特定的,应配置化 |
| 用 `splitstring` 派生副本名 | 路径可能有多个点;建议 `getLogFile + ".copy"` |
| `m_str_send` 与 `m_send` 并存 | 多种帧格式增加 parser 复杂度;新工程只保留 `m_send` |
| 把 `ServerIP` 写在 Method 源码中 | 应放入 Variable,方便运行时修改 |
| `sig` 字段留空 | 必须实现 HMAC,否则 auth 退化为 no-op |
| 用 `.execute()` 验证 `.Program` 写入 | `.execute()` 不刷编译缓存——走 `executeSilent(<expr>)` 模式 |

## 四、SimTalk 2.0 字符串字面量速查

| 写法 | 错误/正确 |
|---|---|
| 字符串长度 | `strLen(s)` ✅ (不是 `s.length`) |
| 字符串切片 | `strCopy(s, pos, n)` ✅ (不是 `s.copy`) |
| JSON 序列化(紧凑) | `jsondata.asString(false)` ✅ |
| JSON 序列化(带缩进) | `jsondata.asString(true)` ✅ 用于调试 |
| JSON 字段读取 | `j["key"]` ✅ 不存在返回 void |
| JSON 字段存在判断 | `j.contains("key")` ✅ |
| JSON 字段删除 | (无内建方法)用 `j["key"] := ""` 模拟清空 |

## 五、action_result 软失败契约(必读)

判断成功 = `result == "success" AND log` 不以 `"code execute failed"` 开头。两个条件都满足才是真成功。

**不要把 `result: "success"` 当作"代码一定跑通了"——读 `log` 字段是硬纪律。**

团队记忆 `memory/team/simtalk-run-soft-failure-design.md` 是源头,所有 `simtalk_run` 调用前应先读。

## 经验 Log

> 本节是 **append-only** 时间线——新发现直接追加在末尾。

<!-- 暂无 entry——首个 entry 由下次踩坑时 append -->