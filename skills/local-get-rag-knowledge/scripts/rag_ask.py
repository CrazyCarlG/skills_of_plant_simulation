"""
Plant Simulation RAG knowledge fetcher (Agent-friendly wrapper).

Wraps the existing ask_copilot.py client (which prints SSE token stream to
stdout) with a thin shim that:

  1. Suppresses token-stream output by default (Agent context doesn't want
     a 60s stream of "the... buffer... object... in... SimTalk..." in stdout)
  2. Returns the final structured result {answer, citations, metrics}
  3. Exposes --json / --stream / --health CLI flags for different Agent needs

Usage (CLI):
    python rag_ask.py "How do I create a Buffer in SimTalk?"
    python rag_ask.py --json "What is the difference between Buffer and PlaceBuffer?"
    python rag_ask.py --stream "What is a Drain?"           # like ask_copilot.py
    python rag_ask.py --health                              # /health probe

Usage (module):
    from rag_ask import ask
    result = ask("How do I create a Buffer in SimTalk?")
    print(result["answer"])
    for c in result.get("citations", []):
        print(c.get("title", ""), c.get("tDocLink", ""))
"""
import argparse
import contextlib
import importlib.util
import io
import json
import sys
import textwrap
from pathlib import Path

# Force UTF-8 stdout (Windows default is cp936, which breaks non-ASCII)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ASK_COPILOT_PATH = Path(
    r"C:\Users\z004bjuu\Documents\skills_of_plant_simulation\Copilot-using\ask_copilot.py"
)


def _load_ask_copilot():
    """Dynamically load ask_copilot.py as a module.

    We do this instead of copy-pasting its urllib code so that any
    upstream change to ask_copilot.py (new fields, new endpoints) is
    picked up automatically.
    """
    if not ASK_COPILOT_PATH.exists():
        raise FileNotFoundError(
            f"ask_copilot.py not found at:\n  {ASK_COPILOT_PATH}\n"
            "If the Copilot-using folder was moved, edit ASK_COPILOT_PATH "
            "in scripts/rag_ask.py."
        )
    spec = importlib.util.spec_from_file_location("ask_copilot", ASK_COPILOT_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def health() -> dict:
    """Hit /health and return the parsed JSON. Exits the process on failure."""
    mod = _load_ask_copilot()
    try:
        h = mod._http_get_json(f"{mod.BASE}/health", timeout=3)
    except Exception as e:
        raise SystemExit(
            f"[error] Cannot reach CoPilot at {mod.BASE}: {e}\n"
            f"        Start it by double-clicking:\n"
            f"          {ASK_COPILOT_PATH.parent}\\start_copilot.bat\n"
            f"        Or manually:\n"
            f"          cd C:\\ProgramFiles\\Siemens\\TecnomatixPlantSimulation2606\\Copilot\n"
            f"          python-3.14.5-embed\\pythonw.exe -m uvicorn copilot_service:app --port 8002"
        )
    if not h.get("agent_ready"):
        raise SystemExit(
            f"[error] CoPilot agent not ready (LLM credentials missing?):\n"
            f"        {json.dumps(h, ensure_ascii=False, indent=2)}"
        )
    return h


def ask(question: str, *, show_stream: bool = False) -> dict:
    """Ask CoPilot a question.

    Args:
        question: Natural-language question (English or Chinese).
        show_stream: If True, let ask_copilot's SSE token stream print to
                     stdout (like running ask_copilot.py directly). Default
                     False — Agent-friendly: returns final dict only.

    Returns:
        dict with keys:
            - answer (str): final natural-language answer
            - citations (list[dict]): [{title, tDocLink, ...}, ...]
            - metrics (dict): {elapsed_time, tool_calls_count, token_usage}
    """
    mod = _load_ask_copilot()

    # If the user wants the stream, let it through. Otherwise redirect to
    # a StringIO so the 60s of incremental tokens don't pollute stdout.
    if show_stream:
        return mod.ask(question)

    with contextlib.redirect_stdout(io.StringIO()):
        return mod.ask(question)


def _format_human(result: dict) -> str:
    """Render the result dict in a human-friendly form (no streaming tokens)."""
    parts = []
    if answer := result.get("answer", ""):
        parts.append(answer)
    if citations := result.get("citations"):
        parts.append("")
        parts.append("[citations]")
        for c in citations:
            link = c.get("tDocLink", "") or c.get("url", "")
            parts.append(f"  - {c.get('title', '')}  {link}")
    if metrics := result.get("metrics"):
        tok = metrics.get("token_usage", {}) or {}
        parts.append(
            f"\n[metrics] {metrics.get('elapsed_time')}s  "
            f"tools={metrics.get('tool_calls_count')}  "
            f"tokens_in/out={tok.get('input_tokens', 0)}/{tok.get('output_tokens', 0)}"
        )
    return "\n".join(parts)


def main():
    p = argparse.ArgumentParser(
        prog="rag_ask",
        description="Ask the local CoPilot RAG service a Plant Simulation question.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            examples:
              %(prog)s "How do I create a Buffer in SimTalk?"
              %(prog)s --json "What is a Drain object?"
              %(prog)s --stream "What is a Drain object?"
              %(prog)s --health
        """),
    )
    p.add_argument(
        "question",
        nargs="*",
        help="Question to ask. Omit to read from stdin.",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Print the raw result dict as JSON (best for Agent consumption).",
    )
    p.add_argument(
        "--stream",
        action="store_true",
        help="Show the live SSE token stream (like ask_copilot.py). "
             "Default is to suppress tokens and only show the final answer.",
    )
    p.add_argument(
        "--health",
        action="store_true",
        help="Probe /health and exit. Use this to verify the service is up.",
    )
    args = p.parse_args()

    if args.health:
        print(json.dumps(health(), ensure_ascii=False, indent=2))
        return

    question = " ".join(args.question).strip()
    if not question:
        question = sys.stdin.read().strip()
    if not question:
        p.error("No question provided. Pass it as an arg or via stdin.")

    result = ask(question, show_stream=args.stream)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(_format_human(result))


if __name__ == "__main__":
    main()
