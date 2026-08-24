# 消息协议 / Message Schema

本文件定义 Claude 通过 `socket_client.py` 与 Plant Simulation TCP 服务端交互的所有 JSON 消息。
所有载荷都以 UTF-8 编码，并以 `||END||` 作为帧分隔符：请求末尾追加 `||END||`，回复以 `||END||` 结尾（读取时用 `--resp-mode delimiter --resp-delimiter '||END||'`）。若服务端按行分帧，改用 `--send-delimiter $'\n'` 追加换行（脚本不会自动加换行）。

> Note: 服务器/客户端方向仅是约定视角——实际传输在客户端 socket ↔ 服务端 socket 之间。

## 通用字段 / Common Fields

| 字段 | 必填 | 说明 |
|---|---|---|
| `type` | 是 | 消息类型（见下表） |
| `action_id` | 是 | 客户端生成的 UUID/字符串，用于把请求与响应配对 |
| `timestamp` | 否 | ISO-8601 时间戳，客户端可选填 |

| 消息类型 | 方向 | 用途 |
|---|---|---|
| `ping` | client → server | 连通性检查（可选时间戳），确认链路可用 |
| `simtalk_syntax` | client → server | 仅做编译/语法检查，不真正执行 |
| `simtalk_run` | client → server | 在 `.current` 上执行一段 SimTalk 表达式并返回结果 |
| `action_result` | server → client | 对 `simtalk_syntax` / `simtalk_run` 的统一回包 |
| `result` | server → client | 对 `ping` 的简单回包 |

---

## `ping` — 连通性检查

请求（client → server）：
```json
{
  "type": "ping",
  "timestamp": "20260824170056"
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `timestamp` | 否 | 客户端时间戳（可选） |

回包为 `{"type":"result","result":"success"}`；网络不通则收不到回复。

---

## `simtalk_syntax` — 仅检查语法

请求（client → server）：
```json
{
  "type": "simtalk_syntax",
  "action_id": "644c86747baa465b8e67b7457a4529f4",
  "simtalk": "->boolean"
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `simtalk` | 是 | SimTalk 源码片段（单行或完整方法体） |
| `target_path` | 否 | 限定到某个对象上做解析（例如 `.Models.Model.m`） |

## `action_result` — 统一回包

响应（server → client）：
```json
{
  "type": "action_result",
  "action_id": "644c86747baa465b8e67b7457a4529f4",
  "result": "failed",
  "log": "2026-08-06 13:15:59: Log file opened! Application Version: 2606.0002, UTC: 2026-08-06 05:15:59\n2026-08-06 14:25:46: print('hello from SimTalk') hasError ： Syntax error near line 1 at '''. (in row :1)"
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `result` | 是 | `success` / `failed` / `timeout` |
| `log` | 否 | 服务器原文日志，可换行 |
| `data` | 否 | 当 `result == "success"` 且请求为查询类时，附带的返回值 |
| `error` | 否 | 当 `result != "success"` 时，机器可读的错误摘要 |
| `duration_ms` | 否 | 服务器端处理耗时（可选） |

> Claude 解读规则：
> - `result == "success"` → 读 `data`（若有）或 `log` 末尾 `OK` 行。
> - `result == "failed"` → 在 `log` 中搜索 `Syntax error near line N` / `hasError` / `(in row :N)` 等关键字，定位代码问题。
> - `result == "timeout"` → 不修改代码，先考虑提高 `--timeout`。

## `simtalk_run` — 执行表达式

请求：
```json
{
  "type": "simtalk_run",
  "action_id": "f1c0...",
  "expression": "print('hello from SimTalk')"
}
```

| 字段 | 必填 | 说明 |
|---|---|---|
| `expression` | 是 | 单条 SimTalk 表达式或语句 |
| `context_path` | 否 | `.current` 之外的执行上下文，例如 `path.to.Machine` |

回包仍是 `action_result`；`data` 字段承载表达式的返回值（`return_value: true` 时存在）。

