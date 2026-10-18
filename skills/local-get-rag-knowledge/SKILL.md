---
name: local-get-rag-knowledge
description: 通过本机 CoPilot RAG 服务（http://localhost:8002）获取 Plant Simulation 相关知识——SimTalk 语法、对象方法、属性、API 行为、官方文档引文。Agent 在用户提出 "how to" / 知识查询 / API 行为解释 / 引文检索 类问题（中文或英文）且**不需要在 Plant Simulation 进程里真实执行**时使用本技能。典型触发："Buffer 的 API 怎么用"、"如何用 SimTalk 创建 MUs"、"Create 方法签名是什么"、"Plant Simulation 官方文档里怎么说"、给一段回答附 Plant Simulation 官方引文。**若用户希望真实执行 SimTalk 代码、跑模型、读对象状态，请改用 `local-simtalk-execution`（执行层）。** 本技能是"查"层，`local-simtalk-execution` 是"做"层。
---

# local-get-rag-knowledge

让 Agent 直接复用已部署在 `http://localhost:8002` 的本地 CoPilot RAG 服务，把 Plant Simulation 的官方知识（SimTalk 语法、对象方法、官方文档引文）以结构化结果带回对话。

底层是 `Copilot-using/ask_copilot.py`（一个标准库 urllib 客户端）。本技能在此之上做两件事：

1. **屏蔽 SSE token 流噪音**——Agent 上下文里不需要一长串渐次打印的 token。
2. **结构化返回**——把答案正文、引文、token 计量分开返回，方便 Agent 引用。

## Quick Start

**默认用法（Agent 推荐）**——只输出答案正文 + 引文 + 计量，无 token 流：

```bash
python3 skills/local-get-rag-knowledge/scripts/rag_ask.py "How do I create a Buffer in SimTalk?"
```

**想看 token 实时流出（调试或复制粘贴场景）**：

```bash
python3 skills/local-get-rag-knowledge/scripts/rag_ask.py --stream "What is a Drain object?"
```

**要原始 JSON（方便 Agent 进一步处理）**：

```bash
python3 skills/local-get-rag-knowledge/scripts/rag_ask.py --json "SimTalk 中如何声明一个 table?"
```

**先检查服务在不在**：

```bash
python3 skills/local-get-rag-knowledge/scripts/rag_ask.py --health
```

**作为 Python 模块调用**：

```python
import sys
sys.path.insert(0, r"C:\Users\z004bjuu\Documents\skills_of_plant_simulation\skills\local-get-rag-knowledge\scripts")
from rag_ask import ask

result = ask("How do I create a Buffer in SimTalk?")
print(result["answer"])
for c in result.get("citations", []):
    print(c["title"], c.get("tDocLink", ""))
```

## 工作前提 / Prerequisites

- **CoPilot 服务正在运行**——`http://localhost:8002/health` 返回 200 且 `agent_ready == true`。启动方法见 `references/quick-start.md` §1 或直接跑 `Copilot-using/start_copilot.bat`。
- **LLM 凭据已配置**——`/health` 的 `agent_ready` 字段为 `true` 才算就绪；为 `false` 通常是 LLM API key 没配。
- **本机联网（可选）**——CoPilot 内部依赖官方 Plant Simulation 文档检索；离线时只能答已有索引中的问题。

## 硬规则（必读）

- **不要绕过 `/health` 探测直接问**——`/health` 是唯一的就绪判据，乱序发送 `/query/stream` 会在服务冷启动时撞到连接挂死。
- **不要把 `ask_copilot.py` 的 600s 流式超时当硬上限**——Plant Simulation 文档检索 + LLM 推理是 IO + 推理双重开销，复杂问题 30–90s 是正常的。Agent 端 timeout ≥ 120s。
- **不要在 Agent 上下文里用 `ask_copilot.py` 直接调用**——它会持续 print token 流污染 Agent 输出。**永远走 `scripts/rag_ask.py` 这个 wrapper**。
- **不要把流式响应当一次性 response 处理**——SSE 协议里 token 是多个 `event: token` 帧，最后一条 `event: done` 帧才是含完整 `answer` / `citations` / `metrics` 的 JSON。Agent 只需要最后那条 done 帧。
- **返回的 `answer` 是已 LLM 总结过的自然语言文本**，不是文档原文。引用与论据要去 `citations` 数组里取。

## 任务流程 / Workflow

1. **健康检查**（Agent 通常跳过；wrapper 内部已做）——`GET /health`，确认 `agent_ready: true`。
2. **构造问题**——把用户的中/英文问题原样发到 `/query/stream`，CoPilot 内部会做意图理解 + 文档检索。
3. **SSE 流式收包**——`POST /query/stream`（body: `{"question": "..."}`），按事件类型分帧：
   - `event: token` → 增量 token（wrapper 默认丢弃）
   - `event: done` → 最终 JSON：`{answer, citations, metrics}`（wrapper 解析并返回）
4. **解读**：
   - `answer`——给用户看的总结文本
   - `citations`——`[{title, tDocLink, ...}, ...]`，每条都对应一篇官方文档；引用时优先用 `tDocLink`
   - `metrics`——`{elapsed_time, tool_calls_count, token_usage: {input_tokens, output_tokens}}`，用于审计 / 计量
5. **失败处理**——见 `references/troubleshooting.md`。

## 关键文件 / Key Files

- `scripts/rag_ask.py`——本技能的 wrapper；屏蔽 token 流、支持 `--json` / `--stream` / `--health`、可作为模块 import。
- `../Copilot-using/ask_copilot.py`——被 wrapper 加载的原始客户端；不要直接改它。
- `../Copilot-using/start_copilot.bat` / `stop_copilot.bat`——服务的启停脚本（不在本技能目录）。
- `references/quick-start.md`——一页速查（启动服务 + 三种调用模式 + 退出码）。
- `references/troubleshooting.md`——服务连不上 / `agent_ready=false` / 答案空 / 超时 的处置表。
- `examples/example.md`——几个常见问题的实际调用与回包样例。

## 与 `local-simtalk-execution` 的边界

| 场景 | 用谁 |
|---|---|
| "Buffer 的 .create 方法签名是什么" | `local-get-rag-knowledge`（查文档） |
| "在跑着的 PS 模型上跑一段 SimTalk 看返回值" | `local-simtalk-execution`（执行） |
| "查文档 + 在模型上验证" | 串行：先本技能查，再执行技能验证 |
| "Plant Simulation 官方文档原话" | `local-get-rag-knowledge` 的 `citations` 字段（带 `tDocLink`） |

## 故障排查 / Troubleshooting

| 现象 | 可能原因 | 处理 |
|---|---|---|
| `[error] Cannot reach CoPilot at http://localhost:8002` | 服务没启动 | 双击 `Copilot-using/start_copilot.bat`；或 `cd C:\ProgramFiles\Siemens\TecnomatixPlantSimulation2606\Copilot && python-3.14.5-embed\pythonw.exe -m uvicorn copilot_service:app --port 8002` |
| `[error] CoPilot agent not ready ...` | LLM 凭据缺失 | 配置 LLM API key（参考 Copilot 服务启动日志），重启服务 |
| 答案很短 / 完全是泛泛而谈 | 文档索引未命中 | 换英文问法（CoPilot 内部以英文文档为主）；细化问题（加对象名 / 方法名） |
| 长时间无响应（> 2 min） | LLM 推理慢 / 文档检索阻塞 | 调高 Agent 端 timeout；如必要，重启服务 |
| `citations` 是空数组 | 答案来自 LLM 先验，未走 RAG 检索 | 一般可接受；如果必须给引文，把问题改得更具体 |
| `--json` 输出乱码 | stdout 编码 | 在 Windows 跑 `set PYTHONIOENCODING=utf-8`；或用 `python -X utf8` |
