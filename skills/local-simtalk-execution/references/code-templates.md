# 载荷模板 / Payload Templates

下列模板可以直接复制后填充变量。**所有模板都需要替换 `<action_id>`**——用 uuid4/hex 等唯一字符串即可。

当前协议消息：`ping`（连通性检查）、`simtalk_syntax`（仅语法检查）、`simtalk_run`（执行表达式）；后两者回包统一为 `action_result`。字段定义见 `message-schema.md`。

消息以 `||END||` 作为帧分隔符：请求末尾追加 `||END||`，回复以 `||END||` 结尾（见 `example/example.md`）。统一发送命令（`<json>` 换成下面的具体载荷）：

```bash
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host <host> --port <port> \
  --data '<json>||END||' \
  --resp-mode delimiter --resp-delimiter '||END||' \
  [--timeout <秒>]
```

> 若服务端按行分帧，则改用 `--send-delimiter $'\n' --resp-mode line --resp-delimiter $'\n'`（见 `socket_client.md`）。

## 模板 0：连通性检查（ping）

```bash
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host 127.0.0.1 --port 9000 \
  --data '{"type":"ping","timestamp":"20260824170056"}||END||'
```

回包 `{"type":"result","result":"success"}` 表示链路正常；网络不通则收不到回复。

## 模板 A：语法检查

```bash
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host 127.0.0.1 --port 9000 \
  --data '{"type":"simtalk_syntax","action_id":"<id>","simtalk":"<simtalk code>"}||END||'
```

可选字段 `target_path` 把解析限定到某个对象上（例如 `.Models.Model.m`）。

如果 SimTalk 跨多行，用 Python 拼 JSON 最稳妥（避免 shell 转义）：

```bash
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host 127.0.0.1 --port 9000 \
  --data "$(python3 -c 'import json; print(json.dumps({"type":"simtalk_syntax","action_id":"abc123","simtalk":"print(\"hi\")\nreturn 1"}))')||END||"
```

> 注意：JSON 内的换行必须写成 `\n`，不能直接放真换行。

## 模板 B：执行表达式

载荷：

```json
{
  "type": "simtalk_run",
  "action_id": "<id>",
  "expression": "print('hello from SimTalk')",
  "return_value": true
}
```

- `expression`（必填）：单条 SimTalk 表达式或语句。
- `context_path`（可选）：`.current` 之外的执行上下文，例如 `path.to.Machine`。
- `return_value: true` 时，回包 `data` 字段承载表达式求值结果；类型由 SimTalk 自动 JSON 化（数字/字符串/布尔/数组）。

## 实用 Bash 助手 / Helper Snippets

用 Python 生成单行 JSON 再交给 `--data`（自动生成唯一 `action_id`）：

```bash
python3 skills/local-simtalk-execution/scripts/socket_client.py \
  --host 127.0.0.1 --port 9000 --timeout 30 \
  --data "$(python3 - <<'PY'
import json, uuid
payload = {
    "type": "simtalk_syntax",
    "action_id": uuid.uuid4().hex,
    "simtalk": "print('hello from SimTalk')",
}
print(json.dumps(payload))
PY
)||END||"
```

> `$(...)` 命令替换会把 Python 输出的单行 JSON 作为 `--data` 参数传入，避免手工转义。

---

## 字段命名备忘 / Field Naming Cheatsheet

- `type`：snake_case 字符串，当前为 `ping` / `simtalk_syntax` / `simtalk_run`
- `action_id`：32 字符 hex 推荐（`uuid.uuid4().hex`）
- `timestamp`（`ping` 可选）：时间戳，例如 `20260824170056`
- `simtalk`（`simtalk_syntax`）/ `expression`（`simtalk_run`）：使用真实换行需转义为 `\n`
- `target_path`（`simtalk_syntax` 可选）：限定到某个对象上做解析，例如 `.Models.Model.m`
- `context_path`（`simtalk_run` 可选）：`.current` 之外的执行上下文，例如 `path.to.Machine`

## 常见反模式 / Common Anti-patterns

1. **❌** 在 shell 里直接写未转义的真换行——JSON 会被拆成多段。
   **✅** 全部使用 `\n` 转义或 Python 拼 JSON。
2. **❌** 同一 `action_id` 复用多次——服务端无法区分请求。
   **✅** 每次发送都生成新 id。
3. **❌** 默认 10 秒 `--timeout` 用于运行仿真。
   **✅** 长任务显式 `--timeout 600` 之类。
4. **❌** 失败后立刻把同一 payload 再发一遍。
   **✅** 看 `log` 字段、定位行号、改代码再发。
5. **❌** 请求末尾漏掉 `||END||`，或读回包时未指定 `--resp-delimiter '||END||'`。
   **✅** 请求末尾追加 `||END||`，并用 `--resp-mode delimiter --resp-delimiter '||END||'` 读取回包。
