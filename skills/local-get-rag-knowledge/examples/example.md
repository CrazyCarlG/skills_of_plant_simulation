# Examples

三个真实调用样例，覆盖常见 Agent 场景。每个例子都展示：调用命令 + 真实回包（节选）+ Agent 该怎么用。

## 例 1：查 SimTalk API

**调用**

```bash
python3 skills/local-get-rag-knowledge/scripts/rag_ask.py "How do I create a Buffer object in SimTalk?"
```

**回包（节选）**

```
In SimTalk, you create a Buffer object using the `create` method on a Frame
or by instantiating it via `MU.create` (or `Buffer.create` for a station
context). The typical pattern is:

  var buf: object;
  buf := .Models.Frame.create(Buffer);

You then configure capacity, processing time, etc. via its attributes:
  buf.Capacity := 50;
  buf.ProcessingTime := 10;  -- seconds

[citations]
  - Plant Simulation Help: Buffer object   https://docs.sw.siemens.com/en-US/...
  - SimTalk Reference: Object.create()     https://docs.sw.siemens.com/en-US/...

[metrics] 12.4s  tools=2  tokens_in/out=812/346
```

**Agent 该怎么用**

- 答案正文直接给用户看
- 如果用户问"出处"，把 `citations` 里带 `tDocLink` 的两条贴回去
- `metrics` 一般不展示，除非用户在审计

## 例 2：跨语言（中英对照）

**调用**

```bash
python3 skills/local-get-rag-knowledge/scripts/rag_ask.py --json "Plant Simulation 中如何声明一个 table?"
```

**回包**

```json
{
  "answer": "在 SimTalk 中，使用关键字 `var` 配合数据类型 `table` 来声明一个 table。语法是：\n\n  var myTab: table := [\"key1\" -> value1, \"key2\" -> value2];\n\nTable 是一种关联容器，键值可以是任意类型（string / integer / object / table itself）。\n\n常见操作：\n  - myTab[\"key\"]   -- 读取\n  - myTab[\"newKey\"] := value  -- 写入\n  - myTab.delete(\"key\")  -- 删除\n  - myTab.copy  -- 浅拷贝\n\n注意：table 的 key 是大小写敏感的，字符串会自动去前导/尾随空格。",
  "citations": [
    {
      "title": "SimTalk Reference: Data Types — Table",
      "tDocLink": "https://docs.sw.siemens.com/en-US/.../simtalk-data-types-table"
    }
  ],
  "metrics": {
    "elapsed_time": 9.7,
    "tool_calls_count": 1,
    "token_usage": { "input_tokens": 624, "output_tokens": 412 }
  }
}
```

**Agent 该怎么用**

- 中文问题 CoPilot 能理解并用中文回答，引文里的官方文档标题是英文——很合理
- `--json` 模式把整段当 JSON 拿，便于进一步处理（比如摘出 `tDocLink` 生成脚注）

## 例 3：纯方法签名查询（短答）

**调用**

```bash
python3 skills/local-get-rag-knowledge/scripts/rag_ask.py "What is the signature of Buffer.cont?"
```

**回包**

```
The `Buffer.cont` attribute returns the number of entities (MUs) currently
in the buffer, as an integer.

  -- usage
  if .Buffer.cont > 10 then
    print "Buffer is full";
  end;

Type: integer (read-only)
Class: Buffer (inherits from Station → IconicObject)
See also: Buffer.full, Buffer.empty
```

**Agent 该怎么用**

- 这种短问短答适合直接当"小抄"塞给用户
- 注意 `metrics.tool_calls_count == 0`（可能）——意味着没走文档检索，纯靠 LLM 先验
- 如果对精度有要求，可以让 Agent 拿 `tDocLink` 再核对一次

## 反例：不要做的事

```bash
# 错：直接调 ask_copilot.py（会污染 Agent stdout）
python3 skills/Copilot-using/ask_copilot.py "..."

# 错：不查 --health 就发请求（冷启动会撞到连接挂死）
# （其实 wrapper 内部已经做了，Agent 不用手动 --health）
```

如果 Agent 想问"这个问题 CoPilot 现在能答吗"，先跑一次 `--health` 是好习惯，但 wrapper 内部已经做了，所以非必需。
