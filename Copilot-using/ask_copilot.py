"""
Simple Plant Simulation CoPilot client.

向本地 CoPilot 服务发送问题并打印答案。
仅使用标准库（urllib），无需 pip install 任何东西。

主机/端口/安装目录来自仓库根目录的 config/local.properties。

用法:
    python ask_copilot.py "如何用 SimTalk 创建一个 Buffer?"
    python ask_copilot.py                         # 交互输入

启动 CoPilot 服务（独立运行，不需要 PS 窗口）:
    双击 Copilot-using\\start_copilot.bat
"""
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from copilot_config import get as _config_get

# Force UTF-8 stdout so non-ASCII characters (→ ✓ etc.) print on Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

COPILOT_HOST = _config_get("COPILOT_HOST")
COPILOT_PORT = _config_get("COPILOT_PORT")
BASE = f"http://{COPILOT_HOST}:{COPILOT_PORT}"


def _http_post_json(url: str, body: dict, timeout: float = 10.0) -> dict:
    """POST JSON, return parsed response. Raises on error."""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _http_get_json(url: str, timeout: float = 5.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def ask(question: str) -> dict:
    """向 CoPilot 提问，返回 {"answer", "citations", "metrics"}."""

    # 1) 健康检查
    try:
        h = _http_get_json(f"{BASE}/health", timeout=3)
    except (urllib.error.URLError, ConnectionError) as e:
        raise SystemExit(
            f"[error] 连不上 CoPilot 服务 ({BASE}): {e}\n"
            f"        请先启动: Copilot-using\\start_copilot.bat"
        )
    if not h.get("agent_ready"):
        raise SystemExit(
            f"[error] CoPilot agent 未就绪（多半是还没配 LLM 凭据）。/health = {h}"
        )

    # 2) SSE 流式问答：边收 token 边打印，最后一条 done 事件含最终 answer
    collected, final = [], None
    data = json.dumps({"question": question}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}/query/stream", data=data, method="POST",
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        event = None
        for raw in r:
            line = raw.decode("utf-8", "ignore").rstrip("\r\n")
            if not line:
                event = None  # 空行 = SSE 事件边界
                continue
            if line.startswith("event:"):
                event = line[len("event:"):].strip()
            elif line.startswith("data:"):
                payload = line[len("data:"):].strip()
                if event == "token":
                    print(payload, end="", flush=True)
                    collected.append(payload)
                elif event == "done":
                    final = json.loads(payload)
    print()  # 流结束后补个换行
    return final or {"answer": "".join(collected)}


def main():
    question = " ".join(sys.argv[1:]) if len(sys.argv) > 1 \
        else input("Question> ").strip()
    if not question:
        print("No question provided.")
        sys.exit(1)

    print(f"[Q] {question}\n")
    result = ask(question)

    if result.get("citations"):
        print("\n\n[citations]")
        for c in result["citations"]:
            print(f"  - {c.get('title', '')}  {c.get('tDocLink', '')}")
    if result.get("metrics"):
        m = result["metrics"]
        tok = m.get("token_usage", {})
        print(
            f"\n[metrics] {m.get('elapsed_time')}s  "
            f"tools={m.get('tool_calls_count')}  "
            f"tokens_in/out={tok.get('input_tokens', 0)}/{tok.get('output_tokens', 0)}"
        )


if __name__ == "__main__":
    main()
