"""One-shot probe: each invocation runs ONE small SimTalk + reads log fresh."""
import subprocess, sys, json

SIMTALK = r"C:/Users/z004bjuu/Documents/skills_of_plant_simulation/skills/local-simtalk-execution/scripts/simtalk_send.py"


def probe(label: str, code: str, host: str = "127.0.0.1", port: int = 50007):
    """Run a small SimTalk snippet and capture the latest log output."""
    r1 = subprocess.run(
        [sys.executable, SIMTALK, "--host", host, "--port", str(port),
         "--timeout", "15", "run", code],
        capture_output=True, text=True, encoding="utf-8",
    )
    r2 = subprocess.run(
        [sys.executable, SIMTALK, "--host", host, "--port", str(port),
         "--timeout", "10", "readlog"],
        capture_output=True, text=True, encoding="utf-8",
    )
    if r2.returncode not in (0, 20):
        sys.stderr.write(f"[{label}] readlog rc={r2.returncode}\n")
        return None
    try:
        env = json.loads(r2.stdout)
    except json.JSONDecodeError:
        sys.stderr.write(f"[{label}] envelope not JSON: {r2.stdout[:200]}\n")
        return None
    log = env.get("log", "")
    return log


def run_code(code: str, host: str = "127.0.0.1", port: int = 50007):
    """Run code with no readlog — just confirm execution."""
    r = subprocess.run(
        [sys.executable, SIMTALK, "--host", host, "--port", str(port),
         "--timeout", "15", "run", code],
        capture_output=True, text=True, encoding="utf-8",
    )
    return r.stdout