"""Dump PythonCode from one PythonModule at a time (avoid buffer overflow)."""
import subprocess, sys, json

SIMTALK = r"C:/Users/z004bjuu/Documents/skills_of_plant_simulation/skills/local-simtalk-execution/scripts/simtalk_send.py"


def dump(name, host="127.0.0.1", port=50007):
    code = f'''
var pm: object := str_to_obj(".Models.Example.GA.{name}")
if pm = void
  print "###VOID###"
  return
end
print "###S###"
print "T=" + pm.InternalClassType
print "Len=" + to_str(strlen(pm.PythonCode))
print "ModuleName=" + pm.ModuleName
'''
    r = subprocess.run(
        [sys.executable, SIMTALK, "--host", host, "--port", str(port),
         "--timeout", "15", "run", code],
        capture_output=True, text=True, encoding="utf-8",
    )
    try:
        env = json.loads(r.stdout)
    except json.JSONDecodeError:
        return f"[{name}] envelope not JSON: {r.stdout[:200]}"
    return f"[{name}]\n{env.get('log', '')}"


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "Optimizer"
    print(dump(target))