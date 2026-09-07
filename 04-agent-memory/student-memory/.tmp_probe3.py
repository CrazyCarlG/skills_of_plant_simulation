"""Probe via simtalk_run envelope log field directly (no readlog)."""
import subprocess, sys, json

SIMTALK = r"C:/Users/z004bjuu/Documents/skills_of_plant_simulation/skills/local-simtalk-execution/scripts/simtalk_send.py"


def run_probe(label, code, host="127.0.0.1", port=50007):
    """Use simtalk_run envelope's `log` field directly."""
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
    probes = [
        ("MATRIX_DIMS", '''
var m: object := str_to_obj(".Models.Example.GA.setupMatrix")
print "###M###"
print "T=" + m.InternalClassType
print "YDim=" + to_str(m.YDim)
print "XDim=" + to_str(m.XDim)
print "YDimNames=" + to_str(m.YDimNames)
print "XDimNames=" + to_str(m.XDimNames)
'''),
        ("DELIVERY_DIMS", '''
var m: object := str_to_obj(".Models.Example.GA.Delivery")
print "###M###"
print "T=" + m.InternalClassType
print "YDim=" + to_str(m.YDim)
print "XDim=" + to_str(m.XDim)
print "YDimNames=" + to_str(m.YDimNames)
print "XDimNames=" + to_str(m.XDimNames)
'''),
    ]
    for label, code in probes:
        out = run_probe(label, code)
        print(out)
        print()