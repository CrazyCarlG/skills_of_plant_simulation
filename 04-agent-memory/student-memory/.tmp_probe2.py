"""Multi-probe helper for Python_GA_Demo."""
import subprocess, sys, json

SIMTALK = r"C:/Users/z004bjuu/Documents/skills_of_plant_simulation/skills/local-simtalk-execution/scripts/simtalk_send.py"


def probe(label, code, host="127.0.0.1", port=50007, marker="###M###"):
    """Run + immediate readlog. Returns log tail after marker."""
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
        return f"[{label}] readlog rc={r2.returncode} err={r2.stderr[:200]}"
    try:
        env = json.loads(r2.stdout)
    except json.JSONDecodeError:
        return f"[{label}] envelope not JSON: {r2.stdout[:200]}"
    log = env.get("log", "")
    if marker in log:
        after = log.split(marker)[-1]
        return f"[{label}]\n" + after.strip()
    return f"[{label}] marker not found; tail={repr(log[-300:])}"


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
        ("MATRIX_DATA", '''
var m: object := str_to_obj(".Models.Example.GA.setupMatrix")
print "###M###"
var yDim: integer := m.YDim
var xDim: integer := m.XDim
print "Y=" + to_str(yDim) + " X=" + to_str(xDim)
var i: integer
var j: integer
for i := 1 to yDim
  var line: string := ""
  for j := 1 to xDim
    if j > 1 then line := line + "," end
    line := line + to_str(m[i, j])
  next
  print "row" + to_str(i) + "=" + line
next
'''),
    ]
    for label, code in probes:
        out = probe(label, code)
        print(out)
        print()