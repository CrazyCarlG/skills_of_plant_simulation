# `copilot_service.py` 脚本说明

本文解释 `copilot_service.py` 的职责、启动与请求流程、模型和检索工具的组织方式，以及维护时需要留意的行为。源码本身也补充了中文行内注释；本文侧重从整体上理解模块之间如何配合。

## 1. 脚本职责

这是一个 FastAPI 服务端，位于命令行问答脚本/BrowserView 与 CoPilot Agent 之间。它负责：

- 暴露 HTTP 接口，接收模型设置、健康检查、反馈和问答请求。
- 读取 Windows Credential Manager 中保存的模型配置，按 provider 创建 LangChain 聊天模型。
- 组装 LangGraph Agent，并给 Agent 配置本地 RAG 工具和 Plant Simulation C++ 运行时 MCP 工具。
- 通过 Server-Sent Events（SSE）逐段发送回答，同时在结束事件里返回最终答案、文档引用和统计数据。
- 维护 LangGraph 对话检查点，并把启动耗时和 Langfuse 调试信息用于诊断。

主要调用关系可以概括为：

```text
BrowserView / ask_copilot.py
        |
        | HTTP + SSE
        v
FastAPI (copilot_service.py)
        |
        +-- LangGraph Agent
        |     +-- 本地 RAG 工具 ----> 本地索引 / 远程 RAG 服务
        |     +-- 运行时工具 ------> Plant Simulation C++ MCP 服务
        |     +-- Chat Model ------> AWS / Azure / Anthropic / Vertex / OpenAI-compatible
        |
        +-- Windows Credential Manager
```

## 2. 文件结构导览

| 区域 | 作用 |
|---|---|
| 模块导入与计时 | 记录关键依赖加载耗时；可选加载 Langfuse。 |
| `StartupTimer` 与启动日志 | 为初始化步骤计时，调试模式下把计时树追加到日志文件。 |
| 配置与 `SYSTEM_PROMPT` | 读取服务地址/端口，并定义 Agent 的回答、检索、引用与代码检查规则。 |
| FastAPI `lifespan` 与全局状态 | 服务启动时调用 `initialize()`；保存当前 Agent、工具、提示词和对话线程。 |
| Pydantic 请求模型 | 校验 HTTP 请求体的字段结构。 |
| Credential Manager 函数 | 通过 Windows Win32 API 读写单个 JSON 凭据项。 |
| 模型工厂函数 | 将选定 provider 的配置转换为相应 LangChain Chat Model。 |
| 检索器与 RAG 工具 | 提供语义检索、关键词检索、全文取回和匿名标识符指导。 |
| MCP 与 Agent 初始化 | 连接 C++ MCP 服务，组合工具并创建 LangGraph Agent。 |
| 引用提取 | 从完整文档工具结果生成前端可用的 Siemens 文档和视频链接。 |
| FastAPI 路由 | 对外提供健康、设置、凭据验证、记忆清除、反馈、关闭和流式问答接口。 |

## 3. 启动流程

FastAPI 创建应用时注册 `lifespan()`。服务启动进入 lifespan 后调用 `initialize()`，其主要步骤如下：

1. 建立根启动计时器，并登记四个本地 RAG 工具。
2. 将内置 `SYSTEM_PROMPT` 保存到 `_system_prompt`。
3. 调用 `_get_retriever()` 初始化检索器。
4. 调用 `_get_mcp_tools()`，最多等待 10 秒获取 C++ MCP 工具。
5. 调用 `_get_model()` 读取凭据并创建模型。
6. 有可用模型时，通过 `create_agent()` 创建 LangGraph Agent；缺少配置时将 `_agent` 设为 `None`，服务仍可启动。
7. 在 `finally` 中收尾计时，并按调试配置决定是否写启动耗时日志。

### 本地或远程 RAG

`COPILOT_RETRIEVAL_URL` 决定检索器类型：

- 设置了该环境变量：创建 `RemoteRetriever`，检索请求交给指定的远程 RAG 服务。
- 未设置：创建 `SimTalkRetriever`，使用 `rag_config.py` 提供的本地数据集路径和 SQLite 路径。

虽然 `_get_retriever()` 的函数说明提到延迟加载，但实际 `initialize()` 会主动调用它。因此本地 SentenceTransformer/PyTorch 及索引初始化会发生在服务启动过程，而不是第一次 RAG 搜索时。远程检索器一般较轻，但仍需检查远程服务可用性。

### MCP 运行时工具

`RUNTIME_MCP_URL` 默认是 `http://localhost:8001/mcp`。MCP 连接超时或失败时，`_get_mcp_tools()` 返回空列表，不会阻止 RAG 问答 Agent 启动。此时 Agent 没有连接 Plant Simulation 运行时的工具，健康接口会显示 `mcp_tools: 0`。

注意：当前代码只在 `initialize()` 中获取 MCP 工具；`_reinitialize_agent()` 会复用已有的 `_mcp_tools`，不会重新连接 MCP。若启动时 MCP 不可用，单纯重新验证模型凭据并不会补上 MCP 工具，通常需要重启服务。

## 4. 模型配置和凭据

### 支持的 Provider

| Provider | 关键字段 | 实现函数 |
|---|---|---|
| `aws` | Region、Model ID、认证方式；Bearer 模式需要 token，IAM 模式需要 access/secret key | `_get_model_aws()`、`_get_model_aws_bearer()`、`_get_model_aws_iam()` |
| `azure` | Endpoint、Deployment、API key | `_get_model_azure()` |
| `anthropic` | API key、Model ID；可选私有部署 Base URL | `_get_model_anthropic()` |
| `google_vertex` | Project ID、Region、Model ID；认证依赖 ADC | `_get_model_google_vertex()` |
| `openai_compatible` | Base URL、Model ID；API key 可选 | `_get_model_openai_compatible()` |

`_get_model(creds)` 是 provider 分发入口。传入 `creds` 时使用调用者提供的临时配置，主要供 `/settings` 验证尚未保存的新设置；不传参数时从 Windows Credential Manager 读取已保存配置。

### 凭据存储方式

凭据以 JSON 字符串形式存放在 Windows Credential Manager 的 Generic Credential 项中，目标名为 `PlantSimulation/CoPilot`。底层通过 `ctypes` 调用 `CredReadW`、`CredWriteW`、`CredDeleteW`，不依赖 `keyring`。

`_save_credentials()` 的字段更新约定：

- `None`：不更改已有值。
- 非空值：写入或更新该字段。
- 空字符串：移除该字段。
- 删除全部字段后：删除整个凭据项。

保存接口会先对模型执行一次很小的真实请求，成功后才持久化配置；provider 切换时会清理其他 provider 的字段。`GET /settings` 只返回配置状态、模型名和地址等非敏感信息，不返回密钥原文。

## 5. Agent 工具

### 本地 RAG 工具

- `search_chunks_semantic(query, k, filter_simtalk)`：适用于概念性问题和宽泛探索，返回相关片段及父文档 ID。
- `search_chunks_keyword(query, k, min_score)`：适用于函数名、类名等精确关键词。索引不可用时返回空结果和错误说明。
- `get_complete_documents(parent_document_ids)`：按搜索结果中的文档 ID 获取完整文档；先去重，最多取 20 个。
- `refactor_with_anonymous_identifiers(source_code, context)`：返回 `@`（触发 MU）和 `?`（调用对象）的使用说明，供对象控制代码生成时参考。

前三个工具调用检索器；第四个工具直接返回脚本内置的说明，不访问 RAG 索引。它被提示词限制在对象控制相关问题中使用。

### MCP 工具

`_get_mcp_tools()` 通过 `MultiServerMCPClient` 连接 C++ 服务，并把服务端公开的工具和 RAG 工具一起传给 Agent。运行时 MCP 的具体工具定义不在本 Python 文件中，而由 C++ Plant Simulation 服务提供。

### 系统提示词的作用

`SYSTEM_PROMPT` 要求 Agent 以 SimTalk 文档为依据，先搜索再取回完整文档，生成 SimTalk 代码前调用语法检查工具，并为检索到的文档生成引用。提示词规定的是模型行为；真正能否调用工具还取决于工具已成功注册以及相应服务是否可达。

当前 `_load_system_prompt()` 最终始终返回源文件内置的 `SYSTEM_PROMPT`。函数中保留了从 Langfuse 加载提示词的注释代码，但那段路径目前没有启用。

## 6. HTTP 接口

| 方法与路径 | 作用 | 关键结果 |
|---|---|---|
| `GET /health` | 返回服务状态、Agent 是否就绪、是否存在凭据以及 MCP 工具数量 | `status`、`agent_ready`、`has_credentials`、`local_tools`、`mcp_tools` |
| `GET /settings` | 返回当前 provider 和非敏感配置 | 不包含密钥原文 |
| `POST /settings` | 验证、保存配置并重建 Agent | 成功返回 `status: ok`；失败返回错误信息 |
| `POST /validate` | 对已经保存的凭据做一次模型调用，并刷新 Agent | 可用于完成 ADC 登录或凭据轮换后重新验证 |
| `POST /clear_memory` | 替换当前 `_thread_id`，开始新的对话线程 | 返回 `status: cleared` |
| `POST /feedback` | 将评分写入 Langfuse | 未启用 Langfuse 时返回 HTTP 501 |
| `POST /shutdown` | 发送终止信号，让服务进程退出 | 供本机宿主请求关闭 |
| `POST /query/stream` | 以 SSE 流式回答问题 | 先发 `token` 事件，最后发 `done` 事件 |

本文件当前没有普通 `POST /query` 路由。文件顶部说明中的普通查询端点描述与现有实现不一致；调用方应使用 `/query/stream`，或在后续明确实现普通查询接口。

`SERVICE_PORT` 默认值为 `8002`，但它只在本模块中读取，并未用于启动 Uvicorn。实际监听端口由启动命令/批处理脚本传给 Uvicorn；调整端口时应同时检查启动脚本及客户端配置。

## 7. 一次流式问答如何工作

`POST /query/stream` 的请求体由 `QueryRequest` 校验，格式为：

```json
{"question": "How do I create a Buffer in SimTalk?"}
```

处理过程：

1. 检查 `_agent`。如果 Agent 尚未建立但凭据已经存在，先尝试 `_reinitialize_agent()`；仍未就绪则返回 HTTP 503。
2. 创建 SSE 事件生成器，记录开始时间，并为 LangGraph 配置当前 `thread_id`。
3. 调用 `_agent.astream(..., stream_mode="messages")`，把用户问题交给 Agent。
4. 每收到 AI 文本内容，立即发送 `token` 事件。Agent 为调用工具而生成的中间说明也可能出现在这些增量 token 中。
5. 收集本次运行产生的消息。AI 工具调用或工具返回会清空 `final_turn_answer`，使它最后只保留工具流程之后的最终回答文本。
6. 运行结束后统计工具调用次数、工具名、模型 token 用量，调用 `_extract_citations()` 提取完整文档引用。
7. 发送 `done` 事件，数据为 JSON，包含最终 `answer`、`citations`、Langfuse `trace_id` 和 `metrics`。

前端应把 token 作为实时预览，把 `done.data` 里的 `answer` 作为最终内容。部分模型服务商不提供 token 用量，相关统计可能为 0；这不代表回答没有生成。

## 8. 引用生成

`_extract_citations()` 只扫描 `ToolMessage` 中名称为 `get_complete_documents` 的结果。每篇文档会生成 Siemens 文档链接；如果文档包含视频 URL，还会额外生成一条 YouTube 引用。函数会去重，并将标题开头的 Markdown `#` 标记去掉。

如果 Agent 只进行了片段搜索而没有调用完整文档工具，`citations` 可能为空。引用链接使用源码中固定的 Siemens 文档基础地址，改变文档版本或站点结构时需要一并检查。

## 9. 启动诊断和调试

- `COPILOT_DEBUG=1`：启用 Langfuse 相关路径以及启动性能日志；Langfuse 不可导入时服务仍可运行，但不会产生追踪。
- `RUNTIME_MCP_URL`：覆盖 C++ MCP 服务 URL。
- `COPILOT_SERVICE_PORT`：设置模块变量 `SERVICE_PORT`；实际 Uvicorn 监听端口仍由启动命令决定。
- `COPILOT_RETRIEVAL_URL`：切换为远程 RAG 服务。

调试模式下，启动耗时追加到 `C:/copilot-log/copilot_startup.log`。控制台日志由 Python logging 输出。排查“服务能打开但不能问答”时，优先对照 `/health` 的 `agent_ready`、`has_credentials` 和 `mcp_tools`：

- `agent_ready=false`：通常是 provider 未配置、配置不完整或 Agent 初始化失败。
- `agent_ready=true` 且 `mcp_tools=0`：LLM 问答可能可用，但运行时 MCP 工具没有接入。
- `status=ok`：仅说明 HTTP 服务能响应，不等于 Agent 已就绪。

## 10. 维护时需要注意

1. 修改 Pydantic 请求字段时，同时检查 `/settings` 的字段映射、持久化键名和 `_load_credentials()` 的允许字段列表。
2. 增加 provider 时，更新 `_get_model()` 分发、`_has_credentials()` 判断、`SaveSettingsRequest`、`/settings` 映射及 provider 切换时的清理列表。
3. 增加 RAG 工具时，同时更新 `initialize()` 和 `_reinitialize_agent()` 中的工具列表；两处目前重复维护。
4. 修改 SSE 事件名称或 `done` JSON 字段时，检查 `ask_copilot.py` 和 BrowserView 的消费逻辑。
5. 修改文档引用字段时，保持 `get_complete_documents()` 的输出、`_extract_citations()` 和前端字段结构一致。
6. 修改启动策略时，以实际调用为准：本地检索器当前会在 `initialize()` 内初始化；MCP 当前仅启动时连接一次；Uvicorn 端口由外部启动参数控制。
7. 系统提示词含有大量逐字字符串，编辑时注意 Python 字符串拼接和引号转义；语法检查只能确认文件可解析，不能证明提示词规则在运行中都能被遵守。

## 11. 相关文件

- `start_copilot.bat`：启动服务的批处理入口。
- `stop_copilot.bat`：停止服务的批处理入口。
- `ask_copilot.py`：命令行问答客户端。
- `copilot_config.py`：客户端配置相关代码。
- `../rag/rag_config.py`：检索数据路径和检索选项来源（具体位置以仓库目录为准）。
