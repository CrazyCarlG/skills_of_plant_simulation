"""Dump raw simtalk_run envelope."""
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
    return r.stdout


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "SimHandler"
    raw = dump(target)
    print(f"STDOUT LEN={len(raw)}")
    print(raw[:1000])
    print("---END---")
    print(raw[-500:])