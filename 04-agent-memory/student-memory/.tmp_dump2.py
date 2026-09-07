"""Dump PythonCode via simtalk_run envelope only (skip readlog cp1252 trap)."""
import subprocess, sys, json

SIMTALK = r"C:/Users/z004bjuu/Documents/skills_of_plant_simulation/skills/local-simtalk-execution/scripts/simtalk_send.py"


def dump(name, host="127.0.0.1", port=50007):
    code = f'''
var pm: object := str_to_obj(".Models.Example.GA.{name}")
if pm = void
  print "###VOID###"
  return
end
print "###CODE###"
print pm.PythonCode
'''
    r = subprocess.run(
        [sys.executable, SIMTALK, "--host", host, "--port", str(port),
         "--timeout", "30", "run", code],
        capture_output=True, text=True, encoding="utf-8",
    )
    try:
        env = json.loads(r.stdout)
    except json.JSONDecodeError:
        return None, f"envelope not JSON: {r.stdout[:300]}"
    log = env.get("log", "")
    if "###CODE###" in log:
        return log.split("###CODE###", 1)[1], None
    return None, f"no marker; log_first={log[:200]}"


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "SimHandler"
    body, err = dump(target)
    if err:
        print(f"ERR: {err}", file=sys.stderr)
        sys.exit(1)
    print(body, end="")