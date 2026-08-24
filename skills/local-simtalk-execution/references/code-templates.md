# 载荷模板 / Payload Templates

下列模板可以直接复制后填充变量。**所有模板都需要替换 `<action_id>`**——用 uuid4/hex 等唯一字符串即可。

## 模板 A：语法检查

```bash
python3 scripts/connector.py send "$(cat <<'EOF'
{"type":"simtalk_syntax","action_id":"<id>","simtalk":"<simtalk code>"}
EOF
)"
```

如果 SimTalk 跨多行，用 `$'...\n...'` 或外部 here-doc 写文件再发送：

```bash
cat > /tmp/payload.json <<'EOF'
{"type":"simtalk_syntax","action_id":"abc123","simtalk":"print('hello from SimTalk')\nreturn 1"}
EOF
python3 scripts/connector.py send "$(cat /tmp/payload.json)"
```

> 注意：JSON 内换行必须写成 `\n`，不能直接放真换行；否则会被 connector 当成两行发送。

## 模板 B：执行表达式

```json
{
  "type": "simtalk_run",
  "action_id": "<id>",
  "expression": "print('hello from SimTalk')",
  "return_value": true
}
```

如果 `return_value: true`，回包 `data` 字段为表达式求值结果；类型由 SimTalk 自动 JSON 化（数字/字符串/布尔/数组）。

## 模板 C：调用方法

```json
{
  "type": "execute_method",
  "action_id": "<id>",
  "object_path": ".Models.Model.M",
  "method": "doSomething",
  "args": [1, "abc", true]
}
```

`args` 是位置参数数组，按方法签名顺序传入。无参方法可省略 `args`。

## 模板 D：查询属性

读取单个属性：

```json
{
  "type": "query_object",
  "action_id": "<id>",
  "object_path": ".Models.Model.Source",
  "attributes": ["name"]
}
```

读取多个属性：

```json
{
  "type": "query_object",
  "action_id": "<id>",
  "object_path": ".Models.Model.Source",
  "attributes": ["name", "length", "statMeanThroughput"]
}
```

读取全部属性：

```json
{
  "type": "query_object",
  "action_id": "<id>",
  "object_path": ".Models.Model.Source"
}
```

回包 `data` 为对象：

```json
{
  "name": "Source",
  "length": 17,
  "statMeanThroughput": 12.34
}
```

## 模板 E：拉取日志

```json
{
  "type": "pull_log",
  "action_id": "<id>",
  "since_timestamp": "2026-08-06T14:00:00Z",
  "max_lines": 200
}
```

`since_timestamp` 缺省时表示从最近一次 `pull_log` 之后继续；`max_lines` 缺省时由服务端默认（通常 100）。

## 模板 F：心跳

```json
{"type":"ping","action_id":"<id>"}
```

`result == "success"` + `data == "pong"`。

## 实用 Bash 助手 / Helper Snippets

把 JSON 单行化再交给 `send`：

```bash
python3 - <<'PY' | python3 scripts/connector.py send --timeout 30
import json, sys, uuid
payload = {
    "type": "simtalk_syntax",
    "action_id": uuid.uuid4().hex,
    "simtalk": "print('hello from SimTalk')",
}
sys.stdout.write(json.dumps(payload))
PY
```

> 上面例子把 Python 的 stdout 直接喂给 `connector.py send`——后者会自动从 stdin 读取，无需 `--data`。

---

## 字段命名备忘 / Field Naming Cheatsheet

- `type`：snake_case 字符串
- `action_id`：32 字符 hex 推荐（`uuid.uuid4().hex`）
- `simtalk` / `expression`：使用真实换行需转义为 `\n`
- `object_path`：以 `.` 开头表示相对 `.current`；以 `~` 开头表示绝对根路径（按 Plant Simulation 约定）
- `args`：JSON 数组，按位置
- `attributes`：JSON 数组，元素为字符串属性名

## 常见反模式 / Common Anti-patterns

1. **❌** 在 shell heredoc 里写未转义的真换行——connector 会当作多条消息发送。
   **✅** 全部使用 `\n` 转义或 Python 拼 JSON。
2. **❌** 同一 `action_id` 复用多次——服务端无法区分请求。
   **✅** 每次 send 都生成新 id。
3. **❌** 默认 10 秒 `--timeout` 用于运行仿真。
   **✅** 长任务显式 `--timeout 600` 之类。
4. **❌** 失败后立刻把同一 payload 再发一遍。
   **✅** 看 `log` 字段、定位行号、改代码再发。