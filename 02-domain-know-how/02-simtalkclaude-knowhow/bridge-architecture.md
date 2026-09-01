---
last_updated: 2026-09-01
contributors: [@plant-simulation-expert]
scope: SimtalkClaude TCP 桥的架构、四层目录、TCP 帧协议、动作路由与回复字段
---

# SimtalkClaude 桥架构与协议

本文档整合 SimtalkClaude TCP 桥的**架构设计与协议层**关键知识。

## 一、桥是什么

SimtalkClaude 是 Plant Simulation 上的桥梁组件,让 **外部 agent 通过 TCP JSON 协议远程驱动模型**:

- **客户端**(agent 端):发 `{type, ...}` 动作
- **服务端**(Plant Simulation 端):收请求并执行,返 `{type, result, log, action_id}` 回复
- **默认地址**:`host.docker.internal:50007`(v1) / `8.137.98.145:50001`(v2)
- **当前仓库实际使用 v1**(默认 50007);v2 用于 Factory51 等高价值模型接入

## 二、支持动作

| 动作 | v1 | v2 |
|---|---|---|
| `ping` | ✅ | ✅ |
| `simtalk_syntax` | ✅ | ✅ |
| `simtalk_run` | ✅ | ✅ |
| `readlog` | ✅ | ❌ **v2 bug**:服务端 `socketcallback` 没有 `readlog` case |
| `auth` | ❌ | ✅(v2 新增) |

## 三、四层目录"教科书"做法

```
.SimtalkClaude/
├── connection/   ← 网络传输层(Socket 收发、Logger)
│   ├── SocketClient.*   ← 客户端 socket 封装
│   ├── SocketServer.*   ← 服务端 socket 事件入口
│   └── Logger/          ← 日志 DataTable
├── main/         ← 运行时实例(Server / SocketServer / SocketClient / SimtalkAction)
├── src/          ← 库模板(class library,main 实例的来源)
│   ├── autoexec          ← 模型打开即执行
│   ├── ErrorHandler      ← 挂在 Method 对象上的全局错误处理
│   └── SimtalkAction.*   ← 动作分发表
└── Objects/      ← 各内置类的引用实例(Method / Socket / DataList / Button ...)
```

| 层 | 职责 | 修改频率 |
|---|---|---|
| `connection/` | 字节收发、心跳、鉴权回包 | 几乎不改 |
| `main/` | 业务实例 + 当前模式(Server flag) | 偶尔改 |
| `src/` | 类库、模板代码 | 经常迭代 |
| `Objects/` | 类引用、文档示例 | 几乎不改 |

> **值得抄**:把"transport / instance / library / reference"四层分开,移植/复用时只换 `connection/`,业务代码不动。

## 四、TCP 帧协议

### 4.1 帧格式:`json + "||END||"`

```simtalk
-- 发送侧(m_send)
var msgStr: string := jsondata.asString(false) + "||END||"
MySocket.write(channelNo, msgStr)

-- 接收侧(m_callback)
message := regex_replace(message, "\|\|END\|\|", "")
j.parse(message)
```

> **为什么用 `||END||` 而不是换行?**
> SimTalk JSON(`jsondata.asString(false)`)会保留字符串内的换行符,用 `||END||` 作分隔符可以无歧义切分多个包,不会因为消息体里有 `\n` 而提前断开。

### 4.2 动作分派:`switch j["type"]`

```simtalk
switch type
case "ping"           → m_send(ping_reply)
case "simtalk_syntax" → SimtalkAction.&get_simtalk_hasError.executenewcallchain(j)
case "simtalk_run"    → SimtalkAction.&Run_Simutalk.executenewcallchain(j)
case "readlog"        → SimtalkAction.&ReadLogFile.executenewcallchain(j)
end
```

> `executenewcallchain(j)` 是 Plant Simulation 的"用 JSON 对象做参数调用方法"机制——直接传一个 JSON 进去,对端按 attribute 名取字段,比写一堆 `if j.contains(...)` 干净。

### 4.3 鉴权(v2 新增,v1 无此环节)

```json
client → server:  {"type":"auth", "token":"...", "ts": <unix_seconds>, "sig":"..."}
server → client:  {"type":"auth", "status":"ok", "session_id":"..."}
```

- `ts` 用 Unix epoch 秒(不是毫秒),从 `sysDate - str_to_dateTime("01.01.1970 00:00:00")` 换算
- 收到 `status:"ok"` 才把 `session_id` 写进本地 `Variable`,否则断 socket
- `sig` 字段是预留的 HMAC 签名口子,v2 暂未真正实现 HMAC(Variable 初始值是空串)

### 4.4 回复包统一字段

所有 action 回复都长这样:

```json
{
  "type":      "<echo 原 type>",
  "action_id": "<echo 原 action_id>",
  "result":    "success" | "failed",
  "log":       "<执行日志 / 错误信息>"
}
```

> 把 `action_id` 原样回传是 agent 端做"异步请求-响应对齐"的关键。`action_result` 是被复用的 JSON 容器变量,每个 handler 都要在出口清空。

## 五、关键模式

### 5.1 Scratch Buffer(用一个 Method 当 SimTalk 代码的载体)

```simtalk
-- .SimtalkClaude.main.SimtalkAction.simtalkcode 是一个 Method 对象
&simtalkcode.program := code
var errMsg: string; var errLine: integer
var hasError := &simtalkcode.hasSyntaxError(errMsg, errLine)
executeSilent(&simtalkcode.program)
var errMsg := getExecuteSilentError
```

> `hasSyntaxError` / `executeSilent` 只接受已存在的 Method 对象作为代码宿主。把代码写到 `simtalkcode.Program` 后,语法错误和运行时错误都能结构化回传。

### 5.2 客户端/服务端同构:`Server` boolean 开关

```simtalk
if current.~.server
  current.~.SocketServer.m_send(action_result)
else
  current.~.SocketClient.m_send(action_result)
end
```

> 同一份 `SimtalkAction` 既能跑在服务端模式,也能跑在客户端模式。`Server` 是 Frame 上的 boolean Variable。

### 5.3 ErrorHandler:吞掉已知良性错误

```simtalk
if error = "Division by zero."
  error := ""
  return 1e300
end
error := "error in " + method_path + ": " + error
return 0
```

> 将"除零"这类已知无害的异常替换成 `1e300`,避免中断长跑仿真;其它异常改写前缀后继续抛,由上层决定是否中止。

### 5.4 自动重置:每个 read 之后清理

```simtalk
clearConsole
clearLogFile
openConsole
```

> Plant Simulation 远程控制场景下的卫生措施:每条 agent 指令结束后重置 Console/log,确保下一次指令从完整因果链开始。

## 六、复现 dump 命令

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

# 3) 用单方法 + sleep 的版本,而不是 BATCH=8 的 probe_methods.py
#    把 probe_methods.py 临时改成 BATCH=1 + sleep(1.2),或直接写一段一次性脚本
```

## 经验 Log

> 本节是 **append-only** 时间线——新发现直接追加在末尾。

<!-- 暂无 entry——首个 entry 由下次踩坑时 append -->