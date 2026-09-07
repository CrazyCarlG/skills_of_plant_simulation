"""Dump multiple PythonModules via direct socket (bypass cp1252 trap)."""
import importlib.util, sys, os

spec = importlib.util.spec_from_file_location('ts',
    'C:/Users/z004bjuu/Documents/skills_of_plant_simulation/04-agent-memory/student-memory/.tmp_socket2.py')
ts = importlib.util.module_from_spec(spec); spec.loader.exec_module(ts)

OUT_DIR = 'C:/Users/z004bjuu/Documents/skills_of_plant_simulation/04-agent-memory/student-memory'

TARGETS = sys.argv[1:] if len(sys.argv) > 1 else [
    "HTMLHandler", "CostumCrossover", "CostumMutation",
    "CostumSampling", "SolutionHandler"
]

for name in TARGETS:
    code = f'''
var pm: object := str_to_obj(".Models.Example.GA.{name}")
if pm = void
  print "###VOID###"
  return
end
print "###CODE###"
print pm.PythonCode
'''
    env = ts.run_code(code)
    log = env.get("log", "")
    if "###CODE###" in log:
        body = log.split("###CODE###", 1)[1]
        path = f"{OUT_DIR}/.tmp_dump_{name}.txt"
        with open(path, "wb") as f:
            f.write(body.encode("utf-8", errors="replace"))
        print(f"[{name}] dumped {len(body)} chars -> {path}")
    else:
        print(f"[{name}] NO MARKER; log={log[:200]}")

# Then readlog once to get the cached output
env = ts.read_log()
log = env.get("log", "")
# Save the raw log too
with open(f"{OUT_DIR}/.tmp_last_readlog.txt", "wb") as f:
    f.write(log.encode("utf-8", errors="replace"))
print(f"readlog wrote {len(log)} chars -> .tmp_last_readlog.txt")