"""Re-scan .Models.Example.GA children via single-run probe."""
import subprocess, sys, json

SIMTALK = r"C:/Users/z004bjuu/Documents/skills_of_plant_simulation/skills/local-simtalk-execution/scripts/simtalk_send.py"


def run_probe(label, code, host="127.0.0.1", port=50007):
    r = subprocess.run(
        [sys.executable, SIMTALK, "--host", host, "--port", str(port),
         "--timeout", "15", "run", code],
        capture_output=True, text=True, encoding="utf-8",
    )
    try:
        env = json.loads(r.stdout)
    except json.JSONDecodeError:
        return f"[{label}] envelope not JSON: {r.stdout[:200]}"
    log = env.get("log", "")
    return f"[{label}] result={env.get('result')}\nlog={log}"


if __name__ == "__main__":
    code = '''
var rootObj: object
rootObj := str_to_obj(".Models.Example.GA")
if rootObj = void
  print "###E###"
  print "ROOT_VOID"
  return
end
var n: integer
n := rootObj.numNodes
print "###N###"
print "N=" + to_str(n)
var i: integer
for i := 1 to n
  var ch: object
  ch := rootObj.node(i)
  print "i" + to_str(i) + ":" + ch.Name + " [" + ch.InternalClassType + "]"
next
'''
    out = run_probe("LIST_GA", code)
    print(out)
    print()