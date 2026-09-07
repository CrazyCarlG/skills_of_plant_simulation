"""Dump PythonCode length + name for all PythonModules in GA Frame (fixed)."""
import subprocess, sys, json

SIMTALK = r"C:/Users/z004bjuu/Documents/skills_of_plant_simulation/skills/local-simtalk-execution/scripts/simtalk_send.py"

MODULES = ["CostumMutation", "CostumSampling", "CostumCrossover",
           "SimHandler", "Optimizer", "Problem", "FitnessEvaluator",
           "HTMLHandler", "SolutionHandler"]


def sizes(host="127.0.0.1", port=50007):
    code = 'var pm: object\n'
    code += 'var s: string\n'
    code += 'var n: integer\n'
    code += 'print "###SIZES###"\n'
    for m in MODULES:
        code += f'pm := str_to_obj(".Models.Example.GA.{m}")\n'
        code += f'if pm = void then\n'
        code += f'  s := "VOID"\n'
        code += f'  n := 0\n'
        code += f'else\n'
        code += f'  s := pm.ModuleName\n'
        code += f'  n := strlen(pm.PythonCode)\n'
        code += f'end\n'
        code += f'print "{m}|" + to_str(n) + "|" + s\n'
    r = subprocess.run(
        [sys.executable, SIMTALK, "--host", host, "--port", str(port),
         "--timeout", "20", "run", code],
        capture_output=True, text=True, encoding="utf-8",
    )
    try:
        env = json.loads(r.stdout)
    except json.JSONDecodeError:
        return f"envelope not JSON: {r.stdout[:300]}"
    return env.get("log", "")


if __name__ == "__main__":
    print(sizes())