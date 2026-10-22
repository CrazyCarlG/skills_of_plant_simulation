#!/usr/bin/env python3
"""
CoPilot Service — FastAPI bridge between BrowserView (C++) and the LangGraph agent.

This service:
  1. Provides RAG tools (semantic search, keyword search, get_complete_documents)
     as direct LangGraph tools — no separate MCP server needed.
  2. Connects to the C++ Plant Simulation runtime MCP server (check_simtalk_syntax,
     verify_method_or_attribute, get_object_methods_and_attributes) on port 8001.
  3. Builds a LangGraph agent with both tool sets.
  4. Exposes HTTP endpoints for BrowserView to call:
     - POST /query          — full query (returns JSON with answer + metrics)
     - POST /query/stream   — SSE streaming (tokens streamed as they arrive)
     - POST /clear_memory   — clear conversation memory
     - GET  /health         — health check

实现结构（便于从上到下阅读）：
    - 导入与配置：记录重型依赖的导入耗时，读取运行时 MCP、端口和调试配置。
    - 系统提示词：定义 SimTalk Agent 的检索、代码校验、引用和回答规则。
    - 应用状态与凭据：维护 Agent、工具、对话线程，并通过 Windows Credential Manager
        安全存取不同模型服务商的配置。
    - 模型与工具：按服务商创建 LangChain 模型；提供本地/远程 RAG 工具，连接运行时 MCP 工具。
    - 初始化与接口：启动时组装依赖；通过 FastAPI 管理设置、健康状态、反馈和 SSE 问答。

注意：本文件当前实现的是 POST /query/stream，没有实现普通 POST /query 路由；
模块说明中的该路由描述可能来自旧版本。
"""

import logging
import os
import time
import uuid
from contextlib import asynccontextmanager, contextmanager
from typing import Dict, List, Optional
from pathlib import Path

# Debug mode — set COPILOT_DEBUG=1 to enable Langfuse tracing + prompt loading
DEBUG_MODE = os.environ.get("COPILOT_DEBUG", "0") == "1"

# Track module-level import time (happens before initialize())
_module_import_start = time.perf_counter()
_module_import_timings = {}

# Import FastAPI and related (required at module level for Uvicorn)
_t = time.perf_counter()
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
_module_import_timings['FastAPI/Pydantic/SSE'] = time.perf_counter() - _t

# Import LangChain core and MCP adapters (required at module level)
_t = time.perf_counter()
from langchain_mcp_adapters.client import MultiServerMCPClient
_module_import_timings['langchain_mcp_adapters.client'] = time.perf_counter() - _t

_t = time.perf_counter()
from langchain_core.messages import AIMessage, ToolMessage
_module_import_timings['langchain_core.messages'] = time.perf_counter() - _t

_t = time.perf_counter()
from langchain_core.tools import tool
_module_import_timings['langchain_core.tools'] = time.perf_counter() - _t

_t = time.perf_counter()
from langgraph.checkpoint.memory import MemorySaver
_module_import_timings['langgraph.checkpoint.memory'] = time.perf_counter() - _t

_module_import_total = time.perf_counter() - _module_import_start

# Langfuse tracing (debug mode only)
# 即使启用了调试模式，Langfuse 依赖缺失也不会阻止服务启动；后续会使用空上下文管理器。
_langfuse_available = False
if DEBUG_MODE:
    try:
        from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler
        from langfuse import propagate_attributes
        _langfuse_available = True
    except ImportError:
        pass

if not _langfuse_available:
    @contextmanager
    def propagate_attributes(**kwargs):
        yield
from rag.rag_config import (
    VICINITY_DATASET_PATH,
    SQLITE_DB_PATH,
    FILTER_SIMTALK_ONLY,
)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("copilot_service")

# ---------------------------------------------------------------------------
# Startup Performance Tracing
# ---------------------------------------------------------------------------

class StartupTimer:
    """Context manager and utility for tracking startup performance metrics.

    Logs detailed timing information to both console and a file (C:/copilot-log/copilot_startup.log)
    for diagnosing slow startup issues.
    """

    def __init__(self, name: str, parent: Optional["StartupTimer"] = None):
        """Initialize a timer.

        Args:
            name: Step name (e.g., "import langchain", "load vicinity dataset")
            parent: Parent timer for nesting (optional)
        """
        self.name = name
        self.parent = parent
        self.start_time: Optional[float] = None
        self.elapsed: Optional[float] = None
        self.children: List["StartupTimer"] = []

    def __enter__(self):
        """Start timing."""
        self.start_time = time.perf_counter()
        logger.info(f"[STARTUP] Starting: {self.name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and log result."""
        # 子计时器结束时挂到父计时器上，最后由根计时器生成完整的启动耗时树。
        self.elapsed = time.perf_counter() - self.start_time
        status = "✓" if exc_type is None else "✗"
        logger.info(f"[STARTUP] {status} Completed: {self.name} ({self.elapsed:.3f}s)")
        if self.parent:
            self.parent.children.append(self)

    def to_log_string(self, indent: int = 0) -> str:
        """Format timer as a log string with indentation for hierarchy."""
        prefix = "  " * indent
        status = "✓" if self.elapsed is not None else "?"
        result = f"{prefix}{status} {self.name}: {self.elapsed:.3f}s\n" if self.elapsed else ""
        for child in self.children:
            result += child.to_log_string(indent + 1)
        return result


# Global root timer for the entire initialization
_root_timer: Optional[StartupTimer] = None
_log_file_path = Path("C:/copilot-log/copilot_startup.log")


def _ensure_temp_dir():
    """Ensure C:/copilot-log directory exists."""
    try:
        _log_file_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.warning(f"Could not create {_log_file_path.parent}: {e}")


def _write_startup_log():
    """Write startup timing summary to log file (only in debug mode: COPILOT_DEBUG=1)."""
    if _root_timer is None:
        return

    # Only write startup log if debug mode is enabled
    if not DEBUG_MODE:
        logger.info("[STARTUP] Debug logging disabled (set COPILOT_DEBUG=1 to enable)")
        return

    try:
        # 追加而非覆盖，便于把多次启动的耗时放在同一个文件里比较。
        _ensure_temp_dir()
        log_content = "=== CoPilot Service Startup Performance ===\n\n"
        log_content += f"Start Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        log_content += f"Total Initialization Time: {_root_timer.elapsed:.3f}s\n"
        log_content += f"Module-Level Import Total: {_module_import_total:.3f}s\n\n"

        # Include module-level import breakdown
        if _module_import_timings:
            log_content += "Module-Level Imports:\n"
            log_content += "-" * 60 + "\n"
            for label, duration in _module_import_timings.items():
                log_content += f"  • {label}: {duration:.3f}s\n"
            log_content += "-" * 60 + "\n\n"
        else:
            log_content += "Module-Level Imports: (none recorded)\n\n"

        log_content += "Detailed Timeline (initialize phase):\n"
        log_content += "-" * 60 + "\n"
        log_content += _root_timer.to_log_string()
        log_content += "-" * 60 + "\n"

        log_content += f"\nSummary:\n"
        log_content += f"  Module-level imports: {_module_import_total:.3f}s\n"
        log_content += f"  Initialize() phase:  {_root_timer.elapsed:.3f}s\n"
        log_content += f"  Unaccounted time (between Uvicorn load and initialize):  {max(0, 0 if _module_import_total < 0.001 else _module_import_total - _root_timer.elapsed):.3f}s\n"

        # Append to file instead of overwriting (for historical tracking)
        with open(_log_file_path, "a", encoding="utf-8") as f:
            f.write(log_content)
            f.write("\n")

        logger.info(f"[STARTUP] Timing log written to {_log_file_path}")
    except Exception as e:
        logger.error(f"Failed to write startup log: {e}")

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
# These can be overridden via CLI args or environment variables.
# RUNTIME_MCP_URL 指向 Plant Simulation 的 C++ 运行时工具服务；CoPilot 自身监听端口由启动脚本使用。
RUNTIME_MCP_URL = os.environ.get("RUNTIME_MCP_URL", "http://localhost:8001/mcp")
SERVICE_PORT    = int(os.environ.get("COPILOT_SERVICE_PORT", "8002"))

# Credential Manager service name
CREDENTIAL_SERVICE = "PlantSimulation/CoPilot"

# System prompt — loaded from Langfuse only in debug mode, otherwise built-in
# 这段字符串是 Agent 的行为契约，不是服务端的业务逻辑；工具是否可用仍由下方注册与连接流程决定。
SYSTEM_PROMPT = (
    "# SimTalk Expert Agent\n"
    "\n"
    "## ABSOLUTE RULES (violating either = task failure)\n"
    "These two rules override everything else in this prompt. If you are about to break one, STOP and call the tool instead.\n"
    "\n"
    "1. **SYNTAX VALIDATION:** You MUST call `check_simtalk_syntax` on every piece of SimTalk code before it appears in your answer. No code reaches the user unvalidated. If `is_valid=false`, fix the code and validate again.\n"
    "2. **DISCOVERY IS NOT ANSWERING:** `get_object_methods_and_attributes` only tells you a member EXISTS. You MUST NOT describe, explain, or use any member from it until you have retrieved its actual documentation via `search_chunks_keyword` + `get_complete_documents`. Knowing a method exists is a STARTING POINT, never an answer.\n"
    "\n"
    "Clarification: the later rule \"never mention tools or validation\" governs only the WORDING of your final answer. It does NOT excuse you from actually calling these tools. Always validate and always research; just never talk about having done so.\n"
    "\n"
    "## Definition of a Complete Answer\n"
    "An answer is ONLY complete when ONE of these is true:\n"
    "- (a) It contains NO SimTalk code, OR\n"
    "- (b) Every SimTalk code block in it has a passing `check_simtalk_syntax` result from THIS conversation turn.\n"
    "There is no third option. If neither holds, you are not done — call the missing tool now.\n"
    "\n"
    "## Pre-Answer Checklist (complete silently before sending any answer that contains code)\n"
    "- [ ] Every code block was passed to `check_simtalk_syntax`\n"
    "- [ ] `check_simtalk_syntax` returned `is_valid=true` for each\n"
    "- [ ] Every method/attribute I used was confirmed via retrieved documentation, not just `get_object_methods_and_attributes`\n"
    "- [ ] For object-control code, I applied `refactor_with_anonymous_identifiers` guidance (?, @)\n"
    "If any box is unchecked, you are NOT done — call the missing tool before answering. Do NOT reveal this checklist in your answer.\n"
    "\n"
    "## Purpose\n"
    "You are a SimTalk programming expert. Answer user questions about SimTalk by thoroughly "
    "researching the documentation using the available tools.\n"
    "\n"
    "## Handling Greetings and Small Talk\n"
    "- If the user greets you ('hello', 'hi', 'how are you'), respond briefly and professionally without using search tools\n"
    "- Quickly transition to asking how you can help with Plant Simulation or SimTalk questions\n"
    '- Example: "Hello! I\'m here to help with SimTalk programming and Plant Simulation questions. What would you like to know?"\n'
    "- If the user asks about your capabilities or how you work, respond professionally with a brief overview\n"
    "\n"
    "## Handling Ambiguous or Unclear Queries\n"
    "- If the user's question is too vague or lacks necessary context, ask for clarification BEFORE searching\n"
    '- Examples: "Could you specify which object or control you\'re asking about?" / "Are you asking about [option A] or [option B]?"\n'
    "- Keep clarification requests brief and friendly; only proceed with searches once you understand what the user needs\n"
    "\n"
    "## Tool Selection Guidelines\n"
    "- **`search_chunks_semantic`:** For conceptual queries, discovering relevant functions, broad exploration. Use k=5-10. Best choice for non-English questions (handles cross-lingual queries).\n"
    "- **`search_chunks_keyword`:** For exact function names, specific API lookups, technical terms. Use k=3-5. **Only use with English queries** — the documentation index is English-only.\n"
    "- **`get_complete_documents`:** After finding relevant chunks, retrieve full documents for complete context. Request 3-5 documents.\n"
    "- **`refactor_with_anonymous_identifiers`:** ONLY when the question is about writing code for object controls (Exit Control, Entrance Control, Methods). Provides guidance on anonymous identifiers (?, @) for name-independent code.\n"
    "- **`verify_method_or_attribute`:** Verify any method/attribute you reference actually exists for the given object type. Use the exact friendly class name from the list below. Call this for every method/attribute NOT directly found in search results.\n"
    "- **`get_object_methods_and_attributes`:** Lists members of an object type for DISCOVERY ONLY. See ABSOLUTE RULE 2 — you must follow up with documentation retrieval before using any member in your answer.\n"
    "- **`check_simtalk_syntax`:** Validate all SimTalk code before presenting it. See ABSOLUTE RULE 1.\n"
    "\n"
    "### Valid Object Type Names\n"
    "When using `verify_method_or_attribute` or `get_object_methods_and_attributes`, you MUST use one of these exact friendly class names:\n"
    "- **Material Flow:** Connector, Source, Drain, Station, ParallelStation, AssemblyStation, DismantleStation, PickAndPlace, Store, PlaceBuffer, Buffer, Sorter, Conveyor, AngularConverter, Converter, Turntable, Turnplate, Track, TwoLaneTrack, FlowControl, Cycle\n"
    "- **Resources:** Workplace, FootPath, WorkerPool, Worker, ShiftCalendar, EventController, Frame, Interface, Exporter, Broker, AGVPool, Marker, LockoutZone\n"
    "- **Information Flow:** Method, PythonModule, Variable, FileLink, FileInterface, DataTable, DataList, DataStack, DataQueue, TimeSequence, Trigger, Generator, AttributeExplorer, OPCUA, OPCClassic, PLCSIM_Advanced, SIMIT, Socket, MQTT, ActiveX, XMLInterface, Teamcenter, SQLite, ODBC, Oracle11g, Oracle19c\n"
    "- **UI:** Comment, Display, Chart, GanttChart, SankeyDiagram, CostAnalyzer, HtmlReport, Dialog, Checkbox, Button, DropDownList\n"
    "- **Mobile Units:** Part, Container, Transporter\n"
    "- **Fluids:** Pipe, FluidSource, FluidDrain, Tank, Mixer, ContinuousMixer, Portioner, DePortioner, PatchMatrix, MaterialsTable\n"
    "- **Generic Algorithms:** GAOptimization, GASelection, GASequence, GARangeAllocation, GASetAllocation\n"
    "\n"
    "## Search & Documentation Requirements\n"
    "- Perform **at least 2-3 search rounds** before answering; single searches are rarely sufficient.\n"
    "- Always retrieve complete documents before answering (don't rely only on chunks).\n"
    "- **Documentation-first:** Only answer from information found in SimTalk documentation. Never rely on general programming knowledge for SimTalk-specific syntax or behavior. The retrieved documentation is your source of truth.\n"
    "- Workflow after `get_object_methods_and_attributes` (per ABSOLUTE RULE 2): (1) search for the specific member with `search_chunks_keyword`, (2) retrieve complete documents, (3) extract parameters/return type/examples/behavior, (4) only then describe or use it.\n"
    "- **When results are empty or insufficient**, respond with: \"I couldn't find information about [topic] in the SimTalk documentation. This might be outside my current knowledge base, or the terms might need adjustment. Could you try rephrasing or ask about a related topic?\" Do NOT fall back to general programming knowledge.\n"
    "\n"
    "## Code Generation Principles\n"
    "- Generate only the minimal, necessary code to answer the question. No extra features, error handling, or abstractions unless requested.\n"
    "- Before returning code for an object control: call `refactor_with_anonymous_identifiers`, incorporate ?/@ where appropriate, then review once more for remaining name dependencies.\n"
    "- Verify every method/attribute not found directly in documentation via `verify_method_or_attribute`; remove or replace anything that doesn't exist.\n"
    "- Syntax-repair loop: if `check_simtalk_syntax` returns `is_valid=false`, fix and re-validate. Track `error_line`/`error_pos` between retries; a changed location means progress. If the same location repeats for 2 consecutive retries, stop and return the best attempt.\n"
    "\n"
    "## Response Guidelines\n"
    "\n"
    "### Output Formatting\n"
    "- Use bullet points, numbered lists, or tables for readability; numbered lists for multi-step procedures.\n"
    "- Provide clear code blocks with brief explanations. Keep paragraphs short (2-3 sentences).\n"
    "\n"
    "### Source Citation (CRITICAL)\n"
    "- **ALWAYS cite your sources** when you retrieve complete documents using `get_complete_documents`\n"
    "- After calling `get_complete_documents`, note the ORDER of documents retrieved\n"
    "- Documents with YouTube videos will have the video as a SEPARATE citation immediately after the document\n"
    "  - Example: Document retrieved → [citations1] for documentation, [citations2] for video tutorial\n"
    "- In your final answer, include citation markers where you use information from those documents:\n"
    "  - First document retrieved → [citations1]\n"
    "  - Second document retrieved (or first video) → [citations2]\n"
    "  - And so on...\n"
    "- Place the marker immediately after the statement/code that uses that source\n"
    '- Example: "Use the move() method to relocate an object.[citations1]"\n'
    "- These markers will be rendered as clickable links to the documentation for the user\n"
    "\n"
    "### YouTube Video Citations\n"
    "- When documents have YouTube videos, they appear as separate citations right after the document\n"
    "- At the end of your answer, mention video resources if present\n"
    '- Example: "For a video tutorial on this topic, see [citations2]."\n'
    "- Reference the specific citation number for the video (the one immediately after the document)\n"
    "- Keep the mention brief and natural - the citation will link directly to the YouTube video\n"
    "\n"
    "### Content Guidelines\n"
    "- NEVER mention tools, searches, or syntax validation in your final answer. This governs WORDING ONLY — it does not waive the ABSOLUTE RULES above.\n"
    '- Forbidden phrases: "I checked the syntax", "I searched for", "I validated", "syntax is correct", "has been validated", "syntactically correct", "I used the tool", "search results show".\n'
    "- Present answers as direct knowledge. The user should not know tools exist. No internal reasoning traces visible.\n"
    "\n"
    "## REMINDER — THE TWO ABSOLUTE RULES\n"
    "1. Every SimTalk code block MUST pass `check_simtalk_syntax` before it appears in your answer.\n"
    "2. Never describe or use a member from `get_object_methods_and_attributes` without first retrieving its documentation.\n"
    "If you are about to send code you have not validated, or describe a member you have not researched, you have NOT finished your task.\n"
)

# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager — initialization and cleanup.

    OPTIMIZATION: Does NOT wait for heavy resource loading (PyTorch embeddings,
    large model files) during startup. Those are deferred to lazy-load on first
    use, allowing FastAPI to become responsive IMMEDIATELY and expose /health.

    This dramatically improves startup time in the C++ health-check polling loop:
    - /health responds within 1-2 seconds instead of blocking until all heavy
      imports complete (5-20+ seconds).
    - The C++ code detects service readiness and removes the loading overlay.
    - Users can interact with CoPilot immediately; heavy model loading happens
      silently in the background on first query (acceptable UX since chat UI
      already shows "thinking..." spinner).
    """
    # FastAPI lifespan 在接收请求前运行初始化；结束时离开上下文，交由服务器关闭应用。
    await initialize()
    yield

app = FastAPI(title="CoPilot Service", version="1.0.0", lifespan=lifespan)

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
# 当前实现以进程级单例保存 Agent 和工具；_thread_id 是当前会话的记忆分区键。
_agent = None
_mcp_tools: List = []
_system_prompt: Optional[str] = None
_checkpointer = MemorySaver()
_thread_id: str = str(uuid.uuid4())


def _create_langfuse_handler() -> Optional["LangfuseCallbackHandler"]:
    """Create a Langfuse callback handler if debug mode is active.

    After the agent run completes, read handler.last_trace_id to get the
    trace ID assigned by Langfuse. This ID is returned to the C++ client
    so it can attach user feedback (like/dislike) to the correct trace.
    """
    if not _langfuse_available:
        return None
    try:
        return LangfuseCallbackHandler()
    except Exception:
        return None

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    question: str


class FeedbackRequest(BaseModel):
    trace_id: str
    score: float  # 1.0 for like, 0.0 for dislike
    comment: Optional[str] = None


class SaveSettingsRequest(BaseModel):
    """设置接口接收的配置格式；字段可选，实际 provider 必需字段由模型构造函数检查。"""
    provider: Optional[str] = None  # "aws", "azure", "anthropic", "google_vertex", "openai_compatible"
    # AWS fields
    aws_auth_method: Optional[str] = None  # "bearer" or "iam"
    aws_bearer_token: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: Optional[str] = None
    aws_model_id: Optional[str] = None
    # Azure fields
    azure_endpoint: Optional[str] = None
    azure_deployment: Optional[str] = None
    azure_api_key: Optional[str] = None
    # Anthropic Direct fields
    anthropic_api_key: Optional[str] = None
    anthropic_model_id: Optional[str] = None
    anthropic_base_url: Optional[str] = None  # For private cloud deployments
    # Google Vertex AI fields
    google_project_id: Optional[str] = None
    google_region: Optional[str] = None
    google_model_id: Optional[str] = None
    # OpenAI-compatible fields (Mistral, Groq, private clouds, etc.)
    openai_compatible_base_url: Optional[str] = None
    openai_compatible_api_key: Optional[str] = None
    openai_compatible_model_id: Optional[str] = None

# ---------------------------------------------------------------------------
# Credential Management (Windows Credential Manager via Win32 API)
# ---------------------------------------------------------------------------

# All credentials are stored as a single JSON entry under target name
# "PlantSimulation/CoPilot" in Windows Credential Manager.
# We use the Win32 CredRead/CredWrite/CredDelete APIs directly (via ctypes)
# instead of the `keyring` package to get full control over the target name.
# The keyring WinVault backend would format it as "credentials@PlantSimulation/CoPilot"
# which is less clean and creates duplicate entries.

_CREDENTIAL_TARGET = CREDENTIAL_SERVICE  # "PlantSimulation/CoPilot"


def _credman_read(target: str) -> Optional[str]:
    """Read a Generic credential from Windows Credential Manager by target name."""
    import ctypes
    import ctypes.wintypes

    CRED_TYPE_GENERIC = 1
    advapi32 = ctypes.windll.advapi32

    class CREDENTIAL(ctypes.Structure):
        _fields_ = [
            ("Flags", ctypes.wintypes.DWORD),
            ("Type", ctypes.wintypes.DWORD),
            ("TargetName", ctypes.wintypes.LPWSTR),
            ("Comment", ctypes.wintypes.LPWSTR),
            ("LastWritten", ctypes.wintypes.FILETIME),
            ("CredentialBlobSize", ctypes.wintypes.DWORD),
            ("CredentialBlob", ctypes.POINTER(ctypes.c_byte)),
            ("Persist", ctypes.wintypes.DWORD),
            ("AttributeCount", ctypes.wintypes.DWORD),
            ("Attributes", ctypes.c_void_p),
            ("TargetAlias", ctypes.wintypes.LPWSTR),
            ("UserName", ctypes.wintypes.LPWSTR),
        ]

    # CredReadW 分配的凭据结构必须用 CredFree 释放；finally 确保解码失败时也会释放。
    pcred = ctypes.POINTER(CREDENTIAL)()
    if not advapi32.CredReadW(target, CRED_TYPE_GENERIC, 0, ctypes.byref(pcred)):
        return None

    try:
        cred = pcred.contents
        if cred.CredentialBlobSize and cred.CredentialBlob:
            blob = ctypes.string_at(cred.CredentialBlob, cred.CredentialBlobSize)
            return blob.decode("utf-8")
        return None
    finally:
        advapi32.CredFree(pcred)


def _credman_write(target: str, data: str, username: str = "CoPilot"):
    """Write a Generic credential to Windows Credential Manager."""
    import ctypes
    import ctypes.wintypes

    CRED_TYPE_GENERIC = 1
    CRED_PERSIST_LOCAL_MACHINE = 2
    advapi32 = ctypes.windll.advapi32

    class CREDENTIAL(ctypes.Structure):
        _fields_ = [
            ("Flags", ctypes.wintypes.DWORD),
            ("Type", ctypes.wintypes.DWORD),
            ("TargetName", ctypes.wintypes.LPWSTR),
            ("Comment", ctypes.wintypes.LPWSTR),
            ("LastWritten", ctypes.wintypes.FILETIME),
            ("CredentialBlobSize", ctypes.wintypes.DWORD),
            ("CredentialBlob", ctypes.POINTER(ctypes.c_byte)),
            ("Persist", ctypes.wintypes.DWORD),
            ("AttributeCount", ctypes.wintypes.DWORD),
            ("Attributes", ctypes.c_void_p),
            ("TargetAlias", ctypes.wintypes.LPWSTR),
            ("UserName", ctypes.wintypes.LPWSTR),
        ]

    # CredentialBlob 保存 UTF-8 JSON 字节；局部 blob 在 CredWriteW 调用期间保持存活。
    encoded = data.encode("utf-8")
    blob = (ctypes.c_byte * len(encoded))(*encoded)

    cred = CREDENTIAL()
    cred.Flags = 0
    cred.Type = CRED_TYPE_GENERIC
    cred.TargetName = target
    cred.Comment = None
    cred.CredentialBlobSize = len(encoded)
    cred.CredentialBlob = blob
    cred.Persist = CRED_PERSIST_LOCAL_MACHINE
    cred.AttributeCount = 0
    cred.Attributes = None
    cred.TargetAlias = None
    cred.UserName = username

    if not advapi32.CredWriteW(ctypes.byref(cred), 0):
        raise OSError(f"CredWriteW failed (error {ctypes.GetLastError()})")


def _credman_delete(target: str):
    """Delete a Generic credential from Windows Credential Manager."""
    import ctypes

    CRED_TYPE_GENERIC = 1
    advapi32 = ctypes.windll.advapi32
    advapi32.CredDeleteW(target, CRED_TYPE_GENERIC, 0)


def _load_credentials() -> dict:
    """Load LLM credentials from Windows Credential Manager.

    All model credentials are stored as a single JSON entry under target
    'PlantSimulation/CoPilot'. Returns a dict with whatever is stored.
    """
    import json as _json
    creds = {}

    raw = _credman_read(_CREDENTIAL_TARGET)
    if raw:
        try:
            stored = _json.loads(raw)
            # Copy all known fields
            for key in ("provider", "aws_auth_method", "bearer_token", "region", "model_id",
                        "aws_access_key_id", "aws_secret_access_key",
                        "azure_endpoint", "azure_deployment", "azure_api_key",
                        "anthropic_api_key", "anthropic_model_id", "anthropic_base_url",
                        "google_project_id", "google_region", "google_model_id",
                        "openai_compatible_base_url", "openai_compatible_api_key",
                        "openai_compatible_model_id"):
                if stored.get(key):
                    creds[key] = stored[key]
            if creds:
                logger.info("Loaded credentials from Windows Credential Manager")
        except (ValueError, TypeError):
            logger.warning("Failed to parse credentials JSON from Credential Manager")
    else:
        logger.warning("No credentials found in Credential Manager")

    return creds


def _save_credentials(**kwargs):
    """Save credentials to Windows Credential Manager as a single JSON entry.

    Accepts arbitrary keyword arguments. Each key-value pair is merged into
    the stored JSON. A non-empty string value sets the field; an empty string
    removes the field; None leaves the field unchanged.
    """
    import json as _json

    # 先读后合并：None 表示保留旧值，空字符串表示删除字段，普通字符串表示更新。
    raw = _credman_read(_CREDENTIAL_TARGET)
    try:
        stored = _json.loads(raw) if raw else {}
    except (ValueError, TypeError):
        stored = {}

    for key, value in kwargs.items():
        if value is None:
            continue  # None means "don't change"
        if value:
            stored[key] = value
        else:
            stored.pop(key, None)

    if stored:
        _credman_write(_CREDENTIAL_TARGET, _json.dumps(stored))
    else:
        _credman_delete(_CREDENTIAL_TARGET)


def _has_credentials() -> bool:
    """Check if an API key is stored for the active provider."""
    try:
        import json as _json
        raw = _credman_read(_CREDENTIAL_TARGET)
        if raw:
            stored = _json.loads(raw)
            provider = stored.get("provider")
            if not provider:
                return False
            # “有凭据”是按当前 provider 的最小可用字段判断，不代表远端服务一定可连接。
            if provider == "azure":
                return bool(stored.get("azure_api_key"))
            if provider == "anthropic":
                return bool(stored.get("anthropic_api_key"))
            if provider == "google_vertex":
                return bool(stored.get("google_project_id") and stored.get("google_model_id"))
            if provider == "openai_compatible":
                return bool(stored.get("openai_compatible_base_url") and stored.get("openai_compatible_model_id"))
            if provider == "aws":
                auth_method = stored.get("aws_auth_method")
                if not auth_method:
                    return False
                if auth_method == "iam":
                    return bool(stored.get("aws_access_key_id") and stored.get("aws_secret_access_key"))
                return bool(stored.get("bearer_token"))
    except Exception:
        pass
    return False


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

def _load_system_prompt() -> str:
    """Load system prompt from Langfuse in debug mode, otherwise use built-in prompt."""
    # 曾预留从 Langfuse 拉取提示词的实现；当前实际始终返回源码内置版本。
    #if DEBUG_MODE:
    #    try:
    #        from langfuse import get_client
    #        langfuse = get_client()
    #        prompt = langfuse.get_prompt("Agent/system_prompt_copilot")
    #        logger.info("System prompt loaded from Langfuse (debug mode)")
    #        return prompt.compile()
    #    except Exception as e:
    #        logger.warning(f"Langfuse unavailable ({e}), using built-in system prompt")
    #else:
    #    logger.info("Using built-in system prompt (production mode)")
    return SYSTEM_PROMPT


def _get_model(creds: Optional[dict] = None):
    """Create the LangChain chat model based on the configured provider.

    If creds is provided, uses those credentials directly (for validation before saving).
    Otherwise reads credentials from Windows Credential Manager.
    Supports providers: 'aws', 'azure', 'anthropic', 'google_vertex', 'openai_compatible'.
    Raises RuntimeError if required credentials are not configured.
    """
    # 传入 creds 时用于尚未保存的设置验证；不传时才从凭据管理器读取已保存配置。
    if creds is None:
        with StartupTimer("Load credentials from Credential Manager", _root_timer):
            creds = _load_credentials()
    provider = creds.get("provider")

    if not provider:
        raise RuntimeError(
            "No LLM provider configured. "
            "Please open CoPilot Settings (⚙️) and select a provider."
        )

    if provider == "azure":
        return _get_model_azure(creds)
    elif provider == "anthropic":
        return _get_model_anthropic(creds)
    elif provider == "google_vertex":
        return _get_model_google_vertex(creds)
    elif provider == "openai_compatible":
        return _get_model_openai_compatible(creds)
    elif provider == "aws":
        return _get_model_aws(creds)
    else:
        raise RuntimeError(
            f"Unknown LLM provider '{provider}'. "
            "Please open CoPilot Settings (⚙️) and select a valid provider."
        )


def _get_model_aws(creds: dict):
    """Create AWS Bedrock chat model (bearer token or IAM keys)."""
    region = creds.get("region", "")
    model_id = creds.get("model_id", "")

    if not region or not model_id:
        raise RuntimeError(
            "AWS Region and Model ID must be configured. "
            "Please open CoPilot Settings (⚙️) and complete the configuration."
        )

    auth_method = creds.get("aws_auth_method")

    if not auth_method:
        raise RuntimeError(
            "AWS authentication method not configured. "
            "Please open CoPilot Settings (⚙️) and select Bearer Token or IAM Keys."
        )

    if auth_method == "iam":
        return _get_model_aws_iam(creds, region, model_id)
    elif auth_method == "bearer":
        return _get_model_aws_bearer(creds, region, model_id)
    else:
        raise RuntimeError(
            f"Unknown AWS authentication method '{auth_method}'. "
            "Please open CoPilot Settings (⚙️) and select Bearer Token or IAM Keys."
        )


def _get_model_aws_bearer(creds: dict, region: str, model_id: str):
    """Create AWS Bedrock chat model with bearer token (proxy/gateway auth)."""
    with StartupTimer(f"Initialize AWS Bedrock model ({model_id})", _root_timer):

        bearer_token = creds.get("bearer_token", "")
        if not bearer_token:
            raise RuntimeError(
                "No bearer token configured. "
                "Please open CoPilot Settings (⚙️) and enter your API key."
            )

        logger.info(f"Using Bedrock model: {model_id} in {region} (bearer token)")

        with StartupTimer("Import boto3 and AWS modules", _root_timer):
            import boto3
            import botocore.credentials
            from botocore import UNSIGNED
            from botocore.config import Config
            from botocore.session import Session
            from boto3.session import Session as Boto3Session
            from langchain_aws import ChatBedrockConverse

        # Bearer 网关不使用 AWS 签名：构造空凭据会话并关闭签名，再在发送前注入 Authorization。
        # 该认证方式只适用于接受此 Bearer 头的 Bedrock 代理/网关。
        botocore_session = Session()
        botocore_session._credentials = botocore.credentials.Credentials("", "", "")
        boto3_session = Boto3Session(botocore_session=botocore_session)

        bedrock_client = boto3_session.client(
            "bedrock-runtime",
            region_name=region,
            config=Config(signature_version=UNSIGNED),
        )

        def _inject_bearer_token(request, **kwargs):
            request.headers["Authorization"] = f"Bearer {bearer_token}"

        bedrock_client.meta.events.register("before-send", _inject_bearer_token)
        logger.info("Using bearer token authentication for Bedrock")

        return ChatBedrockConverse(
            model=model_id,
            region_name=region,
            client=bedrock_client,
            provider="anthropic",
            temperature=0.2,
        )


def _get_model_aws_iam(creds: dict, region: str, model_id: str):
    """Create AWS Bedrock chat model with IAM Access Key + Secret Key."""
    with StartupTimer(f"Initialize AWS Bedrock model with IAM ({model_id})", _root_timer):
        access_key = creds.get("aws_access_key_id", "")
        secret_key = creds.get("aws_secret_access_key", "")

        if not access_key or not secret_key:
            raise RuntimeError(
                "AWS Access Key ID and Secret Access Key must be configured. "
                "Please open CoPilot Settings (⚙️) and enter your IAM credentials."
            )

        logger.info(f"Using Bedrock model: {model_id} in {region} (IAM keys)")

        with StartupTimer("Import boto3", _root_timer):
            import boto3
            from langchain_aws import ChatBedrockConverse

        bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=region,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )

        return ChatBedrockConverse(
            model=model_id,
            region_name=region,
            client=bedrock_client,
            provider="anthropic",
            temperature=0.2,
        )


def _get_model_azure(creds: dict):
    """Create Azure OpenAI chat model."""
    with StartupTimer("Initialize Azure OpenAI model", _root_timer):
        with StartupTimer("Import Azure LangChain modules", _root_timer):
            from langchain_openai import AzureChatOpenAI

        azure_endpoint = creds.get("azure_endpoint", "")
        azure_deployment = creds.get("azure_deployment", "")
        azure_api_key = creds.get("azure_api_key", "")

        if not azure_api_key:
            raise RuntimeError(
                "No Azure API key configured. "
                "Please open CoPilot Settings (⚙️) and enter your API key."
            )

        if not azure_endpoint or not azure_deployment:
            raise RuntimeError(
                "Azure Endpoint and Deployment Name must be configured. "
                "Please open CoPilot Settings (⚙️) and complete the configuration."
            )

        logger.info(f"Using Azure OpenAI: {azure_deployment} at {azure_endpoint}")

        return AzureChatOpenAI(
            azure_endpoint=azure_endpoint,
            azure_deployment=azure_deployment,
            api_key=azure_api_key,
            api_version="2024-12-01-preview",
        )


def _get_model_anthropic(creds: dict):
    """Create Anthropic Direct chat model (supports base_url for private clouds)."""
    with StartupTimer("Initialize Anthropic model", _root_timer):
        with StartupTimer("Import Anthropic LangChain modules", _root_timer):
            from langchain_anthropic import ChatAnthropic

        api_key = creds.get("anthropic_api_key", "")
        model_id = creds.get("anthropic_model_id", "")
        base_url = creds.get("anthropic_base_url", "")

        if not api_key:
            raise RuntimeError(
                "No Anthropic API key configured. "
                "Please open CoPilot Settings (⚙️) and enter your API key."
            )

        if not model_id:
            raise RuntimeError(
                "No Anthropic Model ID configured. "
                "Please open CoPilot Settings (⚙️) and enter the model ID."
            )

        kwargs = {
            "model": model_id,
            "api_key": api_key,
        }
        if base_url:
            kwargs["base_url"] = base_url
            logger.info(f"Using Anthropic model: {model_id} via {base_url}")
        else:
            logger.info(f"Using Anthropic model: {model_id} (direct API)")

        kwargs["temperature"] = 0.3
        return ChatAnthropic(**kwargs)


def _get_model_google_vertex(creds: dict):
    """Create Google Vertex AI chat model using Application Default Credentials (ADC)."""
    with StartupTimer("Initialize Google Vertex AI model", _root_timer):
        with StartupTimer("Import Google LangChain modules", _root_timer):
            from langchain_google_genai import ChatGoogleGenerativeAI

        project_id = creds.get("google_project_id", "")
        region = creds.get("google_region", "")
        model_id = creds.get("google_model_id", "")

        if not project_id:
            raise RuntimeError(
                "Google Cloud Project ID must be configured. "
                "Please open CoPilot Settings (⚙️) and complete the configuration."
            )

        if not region:
            raise RuntimeError(
                "Google Cloud Region must be configured. "
                "Please open CoPilot Settings (⚙️) and complete the configuration."
            )

        if not model_id:
            raise RuntimeError(
                "Google Model ID must be configured. "
                "Please open CoPilot Settings (⚙️) and complete the configuration."
            )

        logger.info(f"Using Vertex AI model: {model_id} in {region} (project: {project_id}, ADC)")

        return ChatGoogleGenerativeAI(
            model=model_id,
            project=project_id,
            location=region,
            temperature=0.2,
        )


def _get_model_openai_compatible(creds: dict):
    """Create OpenAI-compatible chat model (Mistral, Groq, private clouds, Ollama, etc.).

    Supports local LLMs (like Ollama) that may not require an API key.
    If no API key is provided, a dummy key will be used for local deployments.
    """
    with StartupTimer("Initialize OpenAI-compatible model", _root_timer):
        with StartupTimer("Import OpenAI LangChain modules", _root_timer):
            from langchain_openai import ChatOpenAI

        base_url = creds.get("openai_compatible_base_url", "")
        api_key = creds.get("openai_compatible_api_key", "")
        model_id = creds.get("openai_compatible_model_id", "")

        if not base_url or not model_id:
            raise RuntimeError(
                "Base URL and Model ID must be configured for OpenAI-compatible provider. "
                "Please open CoPilot Settings (⚙️) and complete the configuration."
            )

        # If no API key provided, use a dummy key (suitable for local LLMs like Ollama)
        if not api_key:
            api_key = "not-needed"
            logger.info(f"Using OpenAI-compatible model: {model_id} at {base_url} (no API key required)")
        else:
            logger.info(f"Using OpenAI-compatible model: {model_id} at {base_url}")

        return ChatOpenAI(
            model=model_id,
            api_key=api_key,
            base_url=base_url,
            temperature=0.2,
        )


# ---------------------------------------------------------------------------
# RAG retriever (local or remote depending on COPILOT_RETRIEVAL_URL)
# ---------------------------------------------------------------------------
_retriever = None
_RETRIEVAL_URL = os.environ.get("COPILOT_RETRIEVAL_URL", "")

def _get_retriever():
    """Get or initialize the global retriever instance.

    If COPILOT_RETRIEVAL_URL is set, uses the RemoteRetriever which forwards
    all search/document requests to a central RAG server (no local embedding
    model or vector index required).
    Otherwise, uses the local SimTalkRetriever with in-process embeddings.

    IMPORTANT: SimTalkRetriever initialization is deferred (lazy-loaded) to avoid
    blocking the FastAPI startup. The SentenceTransformer and other heavy PyTorch
    dependencies are only imported when actually needed (first search call),
    not during the lifespan/initialize() phase.
    """
    # 单例缓存避免每个工具调用都重新加载向量索引或建立远程客户端。
    # initialize() 会主动调用本函数，因此本地检索器通常在服务初始化阶段加载，而不是首个问题时才加载。
    global _retriever
    if _retriever is None:
        if _RETRIEVAL_URL:
            with StartupTimer("Import RemoteRetriever", _root_timer):
                from rag.remote_retriever import RemoteRetriever
            logger.info(f"Initializing remote retriever: {_RETRIEVAL_URL}")
            _retriever = RemoteRetriever(base_url=_RETRIEVAL_URL)
            logger.info("Remote retriever initialized")
        else:
            # Import and initialize SimTalkRetriever here (triggered by initialize() at startup)
            # This import is typically 5-20s due to sentence-transformers, but it's done upfront
            # during startup to avoid blocking query streams mid-response
            with StartupTimer("Import SimTalkRetriever and PyTorch dependencies", _root_timer):
                from rag.retrieval import SimTalkRetriever
            logger.info("Initializing local SimTalk retriever...")
            with StartupTimer("Initialize SimTalkRetriever (build indices)", _root_timer):
                _retriever = SimTalkRetriever(
                    vicinity_path=VICINITY_DATASET_PATH,
                    db_path=SQLITE_DB_PATH,
                )
            logger.info("Local SimTalk retriever initialized")
    return _retriever


# ---------------------------------------------------------------------------
# RAG tools — direct LangGraph tools (no MCP overhead)
# ---------------------------------------------------------------------------

@tool
def search_chunks_semantic(
    query: str,
    k: int = 5,
    filter_simtalk: bool = FILTER_SIMTALK_ONLY,
) -> dict:
    """Semantic vector search for conceptual discovery and broad exploration.

    CHOOSE THIS TOOL IF:
    - User asks conceptual questions: "how to generate random numbers"
    - Broad exploration needed: "what controls simulation timing"
    - You don't know specific function names yet

    CHOOSE search_chunks_keyword IF:
    - You have specific function names (getSeedTable, z_pareto, etc.)
    - Need exact syntax, parameters, or API documentation

    Args:
        query: Natural language search query (conceptual works best)
        k: Number of chunks to return (start with 5, increment by +5 if needed)
        filter_simtalk: Only SimTalk content (default: True)
    """
    # 返回统一的轻量字段结构，供 Agent 阅读相关片段并提取完整文档 ID。
    retriever = _get_retriever()
    results = retriever.search_chunks(query=query.strip(), k=k, filter_simtalk=filter_simtalk)
    return {
        "results": [
            {
                "title": item.get("title"),
                "parent_document_id": item.get("file_id"),
                "breadcrumb": item.get("breadcrumb", []),
                "related_topics": item.get("related_topics", []),
                "related_simtalk_topics": item.get("related_simtalk_topics", ""),
                "youtube_videos": item.get("youtube_videos", ""),
                "content": item.get("text", ""),
                "search_score": float(score),
            }
            for item, score in results
        ],
        "query": query,
        "total_results": len(results),
    }


@tool
def search_chunks_keyword(
    query: str,
    k: int = 2,
    min_score: float = 1.0,
) -> dict:
    """BM25s keyword search for exact function lookups and technical documentation.

    CHOOSE THIS TOOL IF:
    - Query contains specific function names (getSeedTable, etc.)
    - You need exact syntax, parameters, or API documentation
    - Semantic search returned function names you want to explore

    CHOOSE search_chunks_semantic IF:
    - Conceptual questions or broad exploration
    - You don't know specific function names yet
    - The user's question is NOT in English (keyword search requires English — the index is English-only)

    IMPORTANT: Only pass English keywords to this tool. If the conversation is in another
    language, use search_chunks_semantic instead (it handles non-English queries more robustly).

    Args:
        query: English keywords or function names (space-separated works best)
        k: Number of results (start with 2-5, increment by +2 if needed)
        min_score: BM25s score threshold (default: 1.0, lower=more results)
    """
    # BM25 可能未配置；这种情况返回可供模型识别的空结果，而不是抛出属性错误。
    retriever = _get_retriever()
    if not hasattr(retriever, "search_chunks_bm25s") or not retriever.bm25s_engine:
        return {"error": "BM25s keyword search is not available", "results": [], "total_results": 0}
    results = retriever.search_chunks_bm25s(query=query.strip(), k=k, min_score=min_score)
    return {
        "results": [
            {
                "title": metadata.get("title"),
                "parent_document_id": metadata.get("file_id"),
                "breadcrumb": metadata.get("breadcrumb", []),
                "related_topics": metadata.get("related_topics", []),
                "related_simtalk_topics": metadata.get("related_simtalk_topics", ""),
                "youtube_videos": metadata.get("youtube_videos", ""),
                "content": metadata.get("text", ""),
                "search_score": float(score),
            }
            for metadata, score in results
        ],
        "query": query,
        "total_results": len(results),
    }


@tool
def get_complete_documents(
    parent_document_ids: List[str],
) -> dict:
    """Retrieve complete documents by their file IDs for full context.

    Use this AFTER finding relevant chunks via search_chunks_semantic or
    search_chunks_keyword. Collect parent_document_ids from those results,
    then call this tool to get the full document content.

    Best practice: Only request 3-5 documents you know are highly relevant.

    Args:
        parent_document_ids: List of file IDs from search results
    """
    # 去重并限制最多 20 篇，避免模型误传重复或过长列表导致一次取回过多全文。
    unique_ids = list(dict.fromkeys(parent_document_ids))[:20]
    retriever = _get_retriever()
    documents = retriever.get_complete_documents(unique_ids)
    return {
        "documents": [
            {
                "parent_document_id": doc.get("file_id"),
                "title": doc.get("title"),
                "content": doc.get("text", ""),
                "youtube_videos": doc.get("youtube_videos", ""),
                "related_simtalk_topics": doc.get("related_simtalk_topics", ""),
            }
            for doc in documents
        ],
        "requested_ids": parent_document_ids,
        "total_documents": len(documents),
    }


@tool
def refactor_with_anonymous_identifiers(
    source_code: str,
    context: str = "general",
) -> dict:
    """Get documentation on anonymous identifiers (@, ?) for writing name-independent SimTalk code.

    Use this tool ONLY when the user's question is specifically about writing code
    for object controls (Exit Control, Entrance Control, Methods used as attributes
    of objects). Do NOT use for general explanations or non-control code.

    Returns complete documentation on @ and ? identifiers with refactoring guidance.

    Args:
        source_code: SimTalk source code to refactor
        context: Context about where this code runs (e.g., 'exit control', 'entrance control', 'method')
    """
    return {
        "documentation": {
            "at_identifier": (
                "@ (Triggering MU):\n"
                "The anonymous identifier @ designates the MU that triggered the respective control.\n"
                "\n"
                "Usage: This can be used in any control of an object. For instance, Exit or Entrance Control.\n"
                "\n"
                "Purpose: Enables access to the MU that triggered the control. Subsequently also accessing "
                "its attributes and methods is possible. For instance by using @.Name we can access the name "
                "of the triggering MU.\n"
                "\n"
                "Uniqueness: Assignment is unique even if several controls trigger at the same simulation time, "
                "as Plant Simulation always processes the triggering MU completely before proceeding to the next MU.\n"
                "\n"
                "Example: @.move(ParallelStation.succ(3))"
            ),
            "question_identifier": (
                "? (Calling Object):\n"
                "The anonymous identifier ? designates the material flow object that called the Method.\n"
                "\n"
                "Usage: This can be used in any control of an object. For instance, Exit or Entrance Control.\n"
                "\n"
                "Purpose: Enables access to the calling object independently from its name. Subsequently also "
                "accessing its attributes and methods is possible. For instance by using ?.procTime we can "
                "access the processing time of the calling object.\n"
                "\n"
                "Example: ?.Cont.move(E2)  // moves the contents of the object that called the method to the object E2"
            ),
        },
        "source_code": source_code,
        "context": context if context else "general",
        "refactoring_guidance": (
            "This tool should ONLY be used when writing code for object controls. "
            "Analyze the source code and identify opportunities to use anonymous identifiers:\n"
            "- Replace explicit MU names with @ when referring to the triggering MU of the control "
            "(the MU that entered or is exiting for the entrance or exit control).\n"
            "- Replace explicit object names with ? when referring to the calling object.\n"
            "This makes control code name-independent and reusable across different model structures.\n"
            "IMPORTANT: Apply these refactorings to the code before presenting it to the user."
        ),
    }


# ---------------------------------------------------------------------------
# MCP tools — only C++ runtime tools need cross-process MCP
# ---------------------------------------------------------------------------

async def _get_mcp_tools() -> List:
    """Connect to the C++ Plant Simulation MCP server for runtime tools.

    Uses asyncio.wait_for() with a 10-second timeout to prevent hanging if the
    MCP server is slow to respond. If the connection times out or fails, returns
    an empty list and logs a warning. The tools will be retried on first query.

    This allows FastAPI to start responsive even if the C++ MCP server is busy.
    """
    # MCP 不可用不阻断知识问答服务启动；失败时 Agent 仍可使用本地 RAG 工具。
    import asyncio

    with StartupTimer("MCP server connection", _root_timer) as timer:
        servers = {
            "runtime": {"url": RUNTIME_MCP_URL, "transport": "streamable_http"},
        }
        logger.info(f"Connecting to C++ MCP server: {RUNTIME_MCP_URL}")

        try:
            with StartupTimer("MultiServerMCPClient.get_tools()", timer):
                client = MultiServerMCPClient(servers)
                tools = await asyncio.wait_for(client.get_tools(), timeout=10.0)

            tool_names = [t.name for t in tools]
            logger.info(f"Loaded {len(tools)} MCP tools: {tool_names}")
            return tools
        except asyncio.TimeoutError:
            logger.warning(
                "MCP server connection timed out (10s). "
                "The C++ MCP server may be busy during startup. "
                "Runtime tools will be unavailable until the next attempted query or manual reinit."
            )
            return []
        except Exception as e:
            logger.warning(
                f"MCP server connection failed: {e}. "
                "Runtime tools will be unavailable until the next attempted query or manual reinit."
            )
            return []


async def _reinitialize_agent():
    """Try to (re)create the LLM agent using current credentials and existing tools.

    This is a lightweight reinit that does NOT reconnect MCP or reload RAG tools.
    Use this when credentials become valid after initial startup (e.g., gcloud auth).
    """
    # 设置/认证变更后复用已加载的 RAG 与 MCP 工具，只重建模型和 Agent。
    global _agent
    try:
        with StartupTimer("Import langchain.agents", _root_timer):
            from langchain.agents import create_agent

        rag_tools = [search_chunks_semantic, search_chunks_keyword, get_complete_documents, refactor_with_anonymous_identifiers]
        all_tools = rag_tools + _mcp_tools
        llm = _get_model()
        _agent = create_agent(llm, all_tools, system_prompt=_system_prompt or _load_system_prompt(), checkpointer=_checkpointer)
        logger.info("LangGraph agent (re)initialized successfully")
    except Exception as e:
        logger.warning(f"Agent reinitialization failed: {e}")
        _agent = None


async def initialize():
    """Initialize the agent with RAG tools + C++ MCP tools."""
    global _agent, _mcp_tools, _system_prompt, _root_timer

    # 初始化顺序：准备 RAG 工具和提示词 -> 初始化检索器 -> 连接 MCP -> 创建模型和 Agent。
    # 凭据缺失时保留可响应的服务，但 Agent 为空，用户之后可通过设置接口补齐。
    _root_timer = StartupTimer("CoPilot Service Initialization")
    _root_timer.start_time = time.perf_counter()

    try:
        with StartupTimer("Register RAG tools", _root_timer):
            # RAG tools — direct Python, no network
            with StartupTimer("Define tool functions", _root_timer):
                rag_tools = [search_chunks_semantic, search_chunks_keyword, get_complete_documents, refactor_with_anonymous_identifiers]
            logger.info(f"Registered {len(rag_tools)} local tools (in-process)")

        with StartupTimer("Load system prompt", _root_timer):
            _system_prompt = _load_system_prompt()

        with StartupTimer("Initialize RAG retriever", _root_timer):
            # Initialize retriever now to avoid lazy-loading PyTorch during first query
            # This ensures smooth streaming response without mid-response hangs
            _get_retriever()

        with StartupTimer("Connect to MCP server", _root_timer):
            # C++ runtime tools — via MCP
            _mcp_tools = await _get_mcp_tools()

        all_tools = rag_tools + _mcp_tools
        logger.info(f"Total tools: {len(all_tools)}")

        with StartupTimer("Create LLM model", _root_timer):
            # Try to create the LLM — if no credentials, agent stays None (settings required)
            try:
                llm = _get_model()
            except RuntimeError as e:
                logger.warning(f"Agent not initialized (credentials missing): {e}")
                _agent = None
                return

        with StartupTimer("Create LangGraph agent", _root_timer):
            with StartupTimer("Import langchain.agents", _root_timer):
                from langchain.agents import create_agent

            _agent = create_agent(llm, all_tools, system_prompt=_system_prompt, checkpointer=_checkpointer)
            logger.info("LangGraph agent initialized")

    finally:
        # Finalize root timer and write log
        _root_timer.elapsed = time.perf_counter() - _root_timer.start_time
        logger.info(f"[STARTUP] Total initialization time: {_root_timer.elapsed:.3f}s")

        # Log module-level import timings for diagnostics (only in debug mode)
        if DEBUG_MODE:
            logger.info(f"[STARTUP] Debug: _module_import_timings = {_module_import_timings}")
            logger.info(f"[STARTUP] Debug: _module_import_total = {_module_import_total}")
            if _module_import_timings:
                logger.info(f"[STARTUP] Module-level imports detected:")
                for label, duration in _module_import_timings.items():
                    logger.info(f"[STARTUP]   {label}: {duration:.3f}s")
                logger.info(f"[STARTUP]   Total module-level: {_module_import_total:.3f}s")
            else:
                logger.warning("[STARTUP] WARNING: _module_import_timings is empty! Module-level imports may not have been measured.")

        _write_startup_log()


# ---------------------------------------------------------------------------
# Citation extraction
# ---------------------------------------------------------------------------

def _extract_citations(messages: list) -> List[Dict[str, str]]:
    """Extract citation metadata from get_complete_documents tool results.

    Scans the message list for ToolMessage responses that came from
    get_complete_documents calls and extracts document title, ID, and
    constructs the tDocLink URL for the PLChat citation UI.
    """
    import json as _json

    TDOC_BASE_URL = "https://docs.sw.siemens.com/en-US/doc/297028302/PL20250911657075083.PlantSimulation/"

    # LangGraph 的工具响应位于 ToolMessage；这里只把完整文档工具的结果转换为前端格式。
    # seen 同时避免文档 ID 或视频 URL 在多个工具结果中重复展示。
    seen: set = set()
    citations: List[Dict[str, str]] = []
    for msg in messages:
        if not isinstance(msg, ToolMessage):
            continue
        if msg.name != "get_complete_documents":
            continue
        try:
            content = msg.content
            if isinstance(content, str):
                content = _json.loads(content)
            docs = content.get("documents", []) if isinstance(content, dict) else []
            for doc in docs:
                doc_id = doc.get("parent_document_id", "")
                if not doc_id or doc_id in seen:
                    continue
                seen.add(doc_id)

                raw_title = doc.get("title", "")
                # Strip leading HTML/Markdown heading markers (e.g. "# ", "## ")
                title = raw_title.lstrip("# ").strip()
                tdoc_link = TDOC_BASE_URL + doc_id

                citations.append({
                    "title": title,
                    "doc_id": doc_id,
                    "tDocLink": tdoc_link,
                })

                # Emit a separate citation for the YouTube video if present
                yt_raw = doc.get("youtube_videos", "")
                if yt_raw:
                    yt_url = yt_raw.strip().strip('"')
                    if yt_url and yt_url not in seen:
                        seen.add(yt_url)
                        citations.append({
                            "title": f"YouTube Video on {title}",
                            "doc_id": yt_url,
                            "tDocLink": yt_url,
                        })
        except Exception:
            pass
    return citations


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    """Health check endpoint — responds quickly to signal service readiness.

    Returns immediately (within 1-2 seconds) even if heavy initialization is still
    pending. The C++ BrowserView polls this endpoint and removes the loading overlay
    as soon as it sees status=ok, providing immediate UI feedback.
    """
    # HTTP 健康状态只代表服务进程能响应；客户端还应检查 agent_ready 判断能否问答。
    return {"status": "ok", "agent_ready": _agent is not None, "has_credentials": _has_credentials(), "local_tools": 4, "mcp_tools": len(_mcp_tools)}


@app.get("/settings")
async def get_settings():
    """返回非敏感设置和凭据是否存在；绝不把 API key/token 原文发回客户端。"""
    creds = _load_credentials()
    provider = creds.get("provider", "")
    return {
        "provider": provider,
        "has_token": _has_credentials(),
        # AWS
        "aws_auth_method": creds.get("aws_auth_method", ""),
        "aws_region": creds.get("region", ""),
        "aws_model_id": creds.get("model_id", ""),
        "has_aws_access_key": bool(creds.get("aws_access_key_id")),
        # Azure
        "azure_endpoint": creds.get("azure_endpoint", ""),
        "azure_deployment": creds.get("azure_deployment", ""),
        # Anthropic
        "anthropic_model_id": creds.get("anthropic_model_id", ""),
        "anthropic_base_url": creds.get("anthropic_base_url", ""),
        # Google Vertex AI
        "google_project_id": creds.get("google_project_id", ""),
        "google_region": creds.get("google_region", ""),
        "google_model_id": creds.get("google_model_id", ""),
        # OpenAI-compatible
        "openai_compatible_base_url": creds.get("openai_compatible_base_url", ""),
        "openai_compatible_model_id": creds.get("openai_compatible_model_id", ""),
    }


@app.post("/settings")
async def save_settings(req: SaveSettingsRequest):
    """Validate credentials, save to Credential Manager, and initialize the agent.

    Credentials are ONLY persisted if the LLM validation call succeeds.
    This ensures invalid credentials never end up in Credential Manager.
    For Google Vertex (ADC-based), the validation call verifies that
    Application Default Credentials are available.
    """
    global _agent

    try:
        # 请求字段名面向 UI；这里将其映射为模型工厂使用的内部键名。
        # Build a credentials dict from the request (as if already stored)
        # This maps request fields to the internal credential key names.
        creds = {}
        if req.provider:
            creds["provider"] = req.provider
        if req.aws_auth_method:
            creds["aws_auth_method"] = req.aws_auth_method
        if req.aws_bearer_token:
            creds["bearer_token"] = req.aws_bearer_token
        if req.aws_access_key_id:
            creds["aws_access_key_id"] = req.aws_access_key_id
        if req.aws_secret_access_key:
            creds["aws_secret_access_key"] = req.aws_secret_access_key
        if req.aws_region:
            creds["region"] = req.aws_region
        if req.aws_model_id:
            creds["model_id"] = req.aws_model_id
        if req.azure_endpoint:
            creds["azure_endpoint"] = req.azure_endpoint
        if req.azure_deployment:
            creds["azure_deployment"] = req.azure_deployment
        if req.azure_api_key:
            creds["azure_api_key"] = req.azure_api_key
        if req.anthropic_api_key:
            creds["anthropic_api_key"] = req.anthropic_api_key
        if req.anthropic_model_id:
            creds["anthropic_model_id"] = req.anthropic_model_id
        if req.anthropic_base_url:
            creds["anthropic_base_url"] = req.anthropic_base_url
        if req.google_project_id:
            creds["google_project_id"] = req.google_project_id
        if req.google_region:
            creds["google_region"] = req.google_region
        if req.google_model_id:
            creds["google_model_id"] = req.google_model_id
        if req.openai_compatible_base_url:
            creds["openai_compatible_base_url"] = req.openai_compatible_base_url
        if req.openai_compatible_api_key:
            creds["openai_compatible_api_key"] = req.openai_compatible_api_key
        if req.openai_compatible_model_id:
            creds["openai_compatible_model_id"] = req.openai_compatible_model_id

        # 保存前先从请求数据构造模型，避免无效配置覆盖 Credential Manager 中可用的旧配置。
        # Step 1: Create the model from request credentials (not yet saved)
        try:
            llm = _get_model(creds)
        except RuntimeError as e:
            return {"status": "error", "error": str(e)}

        # Step 2: Validate with a real LLM call
        try:
            from langchain_core.messages import HumanMessage
            bind_kwargs = {"max_output_tokens": 5} if creds.get("provider") == "google_vertex" else {"max_tokens": 5}
            await llm.bind(**bind_kwargs).ainvoke([HumanMessage(content="Hi")])
        except Exception as e:
            error_str = str(e)
            logger.warning(f"Credential validation failed: {error_str}")
            return {"status": "error", "error": error_str}

        # Step 3: Validation passed — now persist credentials
        save_kwargs = dict(
            provider=req.provider,
            aws_auth_method=req.aws_auth_method,
            bearer_token=req.aws_bearer_token,
            aws_access_key_id=req.aws_access_key_id,
            aws_secret_access_key=req.aws_secret_access_key,
            region=req.aws_region,
            model_id=req.aws_model_id,
            azure_endpoint=req.azure_endpoint,
            azure_deployment=req.azure_deployment,
            azure_api_key=req.azure_api_key,
            anthropic_api_key=req.anthropic_api_key,
            anthropic_model_id=req.anthropic_model_id,
            anthropic_base_url=req.anthropic_base_url,
            google_project_id=req.google_project_id,
            google_region=req.google_region,
            google_model_id=req.google_model_id,
            openai_compatible_base_url=req.openai_compatible_base_url,
            openai_compatible_api_key=req.openai_compatible_api_key,
            openai_compatible_model_id=req.openai_compatible_model_id,
        )
        # 切换 provider 时删除其他 provider 的字段，防止旧密钥继续残留在同一 JSON 凭据项中。
        # Clear credentials for inactive providers
        _inactive_fields = {
            "aws": ["azure_endpoint", "azure_deployment", "azure_api_key",
                    "anthropic_api_key", "anthropic_model_id", "anthropic_base_url",
                    "google_project_id", "google_region", "google_model_id",
                    "openai_compatible_base_url", "openai_compatible_api_key", "openai_compatible_model_id"],
            "azure": ["bearer_token", "aws_access_key_id", "aws_secret_access_key", "region", "model_id", "aws_auth_method",
                      "anthropic_api_key", "anthropic_model_id", "anthropic_base_url",
                      "google_project_id", "google_region", "google_model_id",
                      "openai_compatible_base_url", "openai_compatible_api_key", "openai_compatible_model_id"],
            "anthropic": ["bearer_token", "aws_access_key_id", "aws_secret_access_key", "region", "model_id", "aws_auth_method",
                          "azure_endpoint", "azure_deployment", "azure_api_key",
                          "google_project_id", "google_region", "google_model_id",
                          "openai_compatible_base_url", "openai_compatible_api_key", "openai_compatible_model_id"],
            "google_vertex": ["bearer_token", "aws_access_key_id", "aws_secret_access_key", "region", "model_id", "aws_auth_method",
                              "azure_endpoint", "azure_deployment", "azure_api_key",
                              "anthropic_api_key", "anthropic_model_id", "anthropic_base_url",
                              "openai_compatible_base_url", "openai_compatible_api_key", "openai_compatible_model_id"],
            "openai_compatible": ["bearer_token", "aws_access_key_id", "aws_secret_access_key", "region", "model_id", "aws_auth_method",
                                  "azure_endpoint", "azure_deployment", "azure_api_key",
                                  "anthropic_api_key", "anthropic_model_id", "anthropic_base_url",
                                  "google_project_id", "google_region", "google_model_id"],
        }
        for field in _inactive_fields.get(req.provider, []):
            save_kwargs.setdefault(field, "")
        # For AWS, also clear unused auth method's secret
        if req.provider == "aws":
            if req.aws_auth_method == "iam":
                save_kwargs.setdefault("bearer_token", "")
            elif req.aws_auth_method == "bearer":
                save_kwargs.setdefault("aws_access_key_id", "")
                save_kwargs.setdefault("aws_secret_access_key", "")
        _save_credentials(**save_kwargs)

        # Step 4: Initialize the agent with the validated model
        await _reinitialize_agent()

        return {"status": "ok", "agent_ready": _agent is not None}
    except Exception as e:
        logger.error(f"Failed to save settings: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/validate")
async def validate_credentials():
    """Re-validate already-saved credentials (e.g., after gcloud auth application-default login).

    Returns {"status": "ok"} on success or {"status": "error", "error": "<message>"} on failure.
    Use this when credentials were previously saved but authentication was incomplete
    (e.g., Google ADC token expired or not yet created).
    """
    try:
        llm = _get_model()
    except RuntimeError as e:
        return {"status": "error", "error": str(e)}

    try:
        # 对已保存配置发起最小模型请求；这也能验证 ADC 等外部认证当前是否有效。
        # Make a minimal LLM call to verify credentials work.
        from langchain_core.messages import HumanMessage
        creds = _load_credentials()
        bind_kwargs = {"max_output_tokens": 5} if creds.get("provider") == "google_vertex" else {"max_tokens": 5}
        response = await llm.bind(**bind_kwargs).ainvoke([HumanMessage(content="Hi")])
        # Credentials work — always (re)initialize the agent so that stale model
        # instances are replaced (e.g., after gcloud auth or credential rotation)
        await _reinitialize_agent()
        return {"status": "ok"}
    except Exception as e:
        error_str = str(e)
        logger.warning(f"Credential validation failed: {error_str}")
        return {"status": "error", "error": error_str}


@app.post("/clear_memory")
async def clear_memory():
    global _thread_id
    # MemorySaver 按 thread_id 隔离状态；换新 ID 即可开始空对话，不必手动删除旧状态。
    # Start a new conversation thread — the old thread's state remains in memory
    # but will never be referenced again and gets garbage-collected with the process.
    import uuid
    _thread_id = str(uuid.uuid4())
    return {"status": "cleared"}


@app.post("/feedback")
async def feedback(req: FeedbackRequest):
    """Submit user feedback (like/dislike with optional comment) to Langfuse."""
    # trace_id 来自流式问答的 done 事件；没有调试追踪时，反馈功能明确返回 501。
    if not _langfuse_available:
        return JSONResponse(status_code=501, content={"error": "Langfuse not available (enable COPILOT_DEBUG=1)"})
    try:
        from langfuse import get_client
        langfuse = get_client()
        langfuse.create_score(
            trace_id=req.trace_id,
            name="user-feedback",
            value=req.score,
            comment=req.comment,
        )
        logger.info(f"Feedback recorded: trace_id={req.trace_id}, score={req.score}")
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Failed to record feedback: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/shutdown")
async def shutdown():
    """Graceful shutdown — used by C++ host to kill orphaned instances."""
    # 供本机宿主进程请求退出当前 Uvicorn 服务；信号处理由运行服务器负责。
    import os
    import signal
    os.kill(os.getpid(), signal.SIGTERM)
    return {"status": "shutting_down"}


@app.post("/query/stream")
async def query_stream(req: QueryRequest):
    """SSE streaming endpoint — streams tokens as they arrive from the LLM.

    Uses astream() to iterate over agent state chunks.  Token-level streaming
    comes from the chat model; final metrics are collected after the loop.
    """
    # 服务启动时若缺少凭据，允许用户保存/完成认证后在第一次问答时补建 Agent。
    if not _agent:
        # Attempt lazy reinitialization (e.g., user completed gcloud auth after startup)
        if _has_credentials():
            await _reinitialize_agent()
        if not _agent:
            error_msg = "Agent not initialized. Please configure your LLM credentials in Settings (⚙️)."
            return JSONResponse(status_code=503, content={"error": error_msg})

    async def event_generator():
        import json

        # SSE 事件约定：token 是增量文本，done 是最终答案及引用/统计信息的 JSON。
        start = time.perf_counter()
        all_msgs: list = []
        streamed_answer = ""
        final_turn_answer = ""  # accumulates only the current (last) AI turn's text

        # astream with stream_mode="messages" yields (message, metadata) tuples
        # for token-level streaming from the LLM.
        # LangGraph's MemorySaver checkpointer handles conversation memory automatically
        # via thread_id — no need to manually accumulate and replay messages.
        #
        # STREAMING STRATEGY:
        # We stream ALL AI text tokens to PLChat in real-time (including intermediate
        # reasoning like "Let me search...") because PLChat requires continuous
        # customStreamingToken events to manage its UI state properly.
        # The customEndChat event at the end carries the CLEAN final answer (only the
        # last AI turn, without intermediate reasoning), which PLChat uses as the
        # definitive response content — replacing whatever was streamed.
        # thread_id 让 LangGraph 在多轮请求间恢复同一对话；清空记忆会替换这个 ID。
        langfuse_handler = _create_langfuse_handler()
        langfuse_config: dict = {}
        if langfuse_handler:
            langfuse_config["callbacks"] = [langfuse_handler]
        langfuse_config["configurable"] = {"thread_id": _thread_id}
        try:
            with propagate_attributes(user_id=os.environ.get("LANGFUSE_USER_ID"), session_id=_thread_id):
                async for msg, metadata in _agent.astream(
                    {"messages": [{"role": "user", "content": req.question}]}, stream_mode="messages", config=langfuse_config
                ):
                    # Collect all complete messages for metrics/citations extraction
                    all_msgs.append(msg)

                    # Stream all AI content tokens to the client in real-time.
                    # PLChat needs continuous streaming events for proper UI state management.
                    if isinstance(msg, AIMessage):
                        if msg.tool_calls:
                            # New tool-calling turn — reset the final turn accumulator
                            # (previous text was intermediate reasoning)
                            final_turn_answer = ""
                        elif msg.content:
                            text = ""
                            if isinstance(msg.content, str):
                                text = msg.content
                            elif isinstance(msg.content, list):
                                for block in msg.content:
                                    if isinstance(block, dict) and block.get("type") == "text":
                                        text += block.get("text", "")
                                    elif isinstance(block, str):
                                        text += block
                            if text:
                                streamed_answer += text
                                final_turn_answer += text
                                yield {"event": "token", "data": text}
                    elif isinstance(msg, ToolMessage):
                        # Tool result — reset accumulator (safety net)
                        final_turn_answer = ""

        except Exception as e:
            logger.error(f"Agent streaming error: {e}", exc_info=True)
            yield {"event": "token", "data": f"An error occurred: {e}"}
            all_msgs = []
            final_turn_answer = ""

        # 流里可能包含“调用工具前的说明”；done.answer 只保留最后一轮最终答复。
        elapsed = round(time.perf_counter() - start, 2)

        # 从本次运行产生的消息统计工具调用与模型用量；有些 provider 不返回 token 统计。
        # Collect metrics from accumulated messages
        # Use final_turn_answer for the customEndChat answer — this contains only the
        # last AI turn (the actual answer), excluding intermediate reasoning from
        # tool-calling turns ("Let me search...", "I found relevant info...").
        # PLChat's customEndChat is a "final render event" that RE-RENDERS the answer
        # from this field, replacing whatever was streamed. So the clean final answer
        # is what the user sees after rendering completes.
        final_response = final_turn_answer if final_turn_answer else streamed_answer
        tool_calls_count = 0
        tool_names = []
        total_input = 0
        total_output = 0

        for msg in all_msgs:
            if isinstance(msg, AIMessage):
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    tool_calls_count += len(msg.tool_calls)
                    for tc in msg.tool_calls:
                        tool_names.append(tc.get("name", "unknown"))
                if hasattr(msg, "usage_metadata") and msg.usage_metadata:
                    total_input += msg.usage_metadata.get("input_tokens", 0)
                    total_output += msg.usage_metadata.get("output_tokens", 0)

        # Extract citations
        citations = _extract_citations(all_msgs) if all_msgs else []

        # Memory is managed automatically by LangGraph's MemorySaver checkpointer.
        # The full agent state (including tool calls/results) is persisted per thread_id.
        # This thread_id can be used to maintain chat history across multiple interactions.

        # 将追踪 ID 返回给 UI，之后的点赞/点踩才能关联到对应 Langfuse trace。
        # Extract trace_id from Langfuse handler for feedback correlation.
        # After the agent run, handler.last_trace_id contains the Langfuse-assigned trace ID.
        trace_id = None
        if langfuse_handler and hasattr(langfuse_handler, "last_trace_id"):
            trace_id = langfuse_handler.last_trace_id

        # Send final metrics event
        yield {
            "event": "done",
            "data": json.dumps({
                "answer": final_response,
                "citations": citations,
                "trace_id": trace_id,
                "metrics": {
                    "elapsed_time": elapsed,
                    "tool_calls_count": tool_calls_count,
                    "tools_used": sorted(set(tool_names)),
                    "token_usage": {
                        "input_tokens": total_input,
                        "output_tokens": total_output,
                        "total_tokens": total_input + total_output,
                    },
                },
            }),
        }

    return EventSourceResponse(event_generator())
