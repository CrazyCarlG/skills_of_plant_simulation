# Quick Start

一页速查：启动服务 + 三种调用模式 + 退出码。

## 1. 启动 CoPilot 服务

服务监听 `127.0.0.1:8002`，没启动时所有调用都会 fail。

**方法 A：双击启动脚本**（推荐）

```
C:\Users\z004bjuu\Documents\skills_of_plant_simulation\Copilot-using\start_copilot.bat
```

脚本会：
1. 检查 Python 与依赖是否存在
2. 后台拉起 `uvicorn copilot_service:app`
3. 轮询 `/health` 直到返回 200（首次 5–15s，索引加载）
4. 打印 `/health` 的 JSON 内容

**方法 B：手动命令**

```bash
cd "C:\ProgramFiles\Siemens\TecnomatixPlantSimulation2606\Copilot"
"python-3.14.5-embed\pythonw.exe" -m uvicorn copilot_service:app --host 127.0.0.1 --port 8002
```

> `pythonw.exe` 不弹窗；想看实时日志就把 `pythonw` 换成 `python`。

**停止服务**

双击 `Copilot-using\stop_copilot.bat`，或：

```bash
curl -X POST http://localhost:8002/shutdown
```

## 2. 三种调用模式

### 模式 A：纯文本（Agent 默认推荐）

```bash
python3 skills/local-get-rag-knowledge/scripts/rag_ask.py "How do I create a Buffer in SimTalk?"
```

输出：
- 答案正文
- 引文列表（每条带 `tDocLink`）
- 一行 `[metrics]` 摘要

**适用**：直接把答案贴回对话。Agent 上下文里最干净。

### 模式 B：原始 JSON

```bash
python3 skills/local-get-rag-knowledge/scripts/rag_ask.py --json "What is the difference between Buffer and PlaceBuffer?"
```

输出 `{"answer": ..., "citations": [...], "metrics": {...}}`，整段 JSON。

**适用**：Agent 想自行解析引文、剪裁、注入到其他 prompt。

### 模式 C：实时流（调试 / 复制粘贴）

```bash
python3 skills/local-get-rag-knowledge/scripts/rag_ask.py --stream "What is a Drain object?"
```

输出：边收 SSE token 边打印，最后补引文 + 计量。

**适用**：长问题想看 CoPilot 是否卡住，或想把过程贴到 issue 里。

## 3. 健康探测

```bash
python3 skills/local-get-rag-knowledge/scripts/rag_ask.py --health
```

期望输出（节选）：

```json
{
  "status": "ok",
  "agent_ready": true,
  "index_loaded": true
}
```

- `agent_ready: false` → LLM 凭据没配，去 CoPilot 服务目录查启动日志
- `agent_ready: true` 但 `index_loaded: false` → 索引加载中，等几秒重试
- HTTP 无法连接 → 服务没启动，回到 §1

## 4. 作为 Python 模块

```python
import sys
sys.path.insert(0, r"C:\Users\z004bjuu\Documents\skills_of_plant_simulation\skills\local-get-rag-knowledge\scripts")
from rag_ask import ask, health

# 一次性健康检查
h = health()

# 提问
result = ask("How do I create a Buffer in SimTalk?")
print(result["answer"])
for c in result.get("citations", []):
    print(c.get("title", ""), c.get("tDocLink", ""))
```

## 5. 退出码

| 退出码 | 含义 |
|---|---|
| 0 | 成功 |
| 1 | CoPilot 服务不可达（`/health` 探测失败） |
| 2 | CoPilot agent 未就绪（`agent_ready: false`） |
| 非 0/1/2 | ask_copilot.py 自身抛错（极少：JSON 损坏、bug） |

Agent 端可以靠退出码判断调用成败，不必解析 stdout。
