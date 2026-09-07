"""Dump PythonCode in safe ASCII chunks."""
import subprocess, sys, json

SIMTALK = r"C:/Users/z004bjuu/Documents/skills_of_plant_simulation/skills/local-simtalk-execution/scripts/simtalk_send.py"


def chunk_dump(name, start, length, host="127.0.0.1", port=50007):
    code = f'''
var pm: object := str_to_obj(".Models.Example.GA.{name}")
if pm = void
  print "###VOID###"
  return
end
var s: string
s := mid(pm.PythonCode, {start}, {length})
print "###C###"
print s
'''
    r = subprocess.run(
        [sys.executable, SIMTALK, "--host", host, "--port", str(port),
         "--timeout", "15", "run", code],
        capture_output=True, text=True, encoding="utf-8",
    )
    try:
        env = json.loads(r.stdout)
    except json.JSONDecodeError:
        return f"envelope not JSON: {r.stdout[:200]}"
    log = env.get("log", "")
    if "###C###" in log:
        return log.split("###C###", 1)[1].rstrip("\n")
    return f"no marker; log_first={log[:200]}"


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "SimHandler"
    CHUNK = 500
    # First get total length
    code = f'''
var pm: object := str_to_obj(".Models.Example.GA.{name}")
print "###LEN###"
print to_str(strlen(pm.PythonCode))
'''
    r = subprocess.run(
        [sys.executable, SIMTALK, "--host", "127.0.0.1", "--port", "50007",
         "--timeout", "15", "run", code],
        capture_output=True, text=True, encoding="utf-8",
    )
    env = json.loads(r.stdout)
    log = env.get("log", "")
    if "###LEN###" not in log:
        print(f"Can't get len: {log}", file=sys.stderr)
        sys.exit(1)
    total = int(log.split("###LEN###")[-1].strip().split()[0])
    print(f"TOTAL={total}", file=sys.stderr)
    # Now chunk-dump
    chunks = []
    pos = 1
    while pos <= total:
        end = min(pos + CHUNK - 1, total)
        c = chunk_dump(name, pos, end - pos + 1)
        chunks.append(c)
        pos = end + 1
    print("".join(chunks), end="")