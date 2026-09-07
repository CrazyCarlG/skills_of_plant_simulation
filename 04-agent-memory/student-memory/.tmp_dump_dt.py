"""Probe Input DataTable contents + DropDownList + RunButton state."""
import importlib.util, sys
spec = importlib.util.spec_from_file_location('ts',
    'C:/Users/z004bjuu/Documents/skills_of_plant_simulation/04-agent-memory/student-memory/.tmp_socket2.py')
ts = importlib.util.module_from_spec(spec); spec.loader.exec_module(ts)


def probe(code):
    env = ts.run_code(code)
    return env.get("log", "")


# Check if Input exists
log = probe('''
var m: object := str_to_obj(".Models.Example.GA.Input")
print "###DT###"
print "VOID=" + to_str(m = void)
if m /= void
  print "T=" + m.InternalClassType
  print "YDim=" + to_str(m.YDim)
  print "XDim=" + to_str(m.XDim)
  print "YDimNames=" + to_str(m.YDimNames)
  print "XDimNames=" + to_str(m.XDimNames)
  var i: integer
  var j: integer
  for i := 1 to m.YDim
    var line: string := ""
    for j := 1 to m.XDim
      if j > 1 then line := line + "|" end
      line := line + to_str(m[j,i])
    next
    print "row" + to_str(i) + "=" + line
  next
end
''')
print(log)

# Also probe Solutions DataTable
print("---")
log2 = probe('''
var m: object := str_to_obj(".Models.Example.GA.Solutions")
print "###SOL###"
print "VOID=" + to_str(m = void)
if m /= void
  print "T=" + m.InternalClassType
  print "YDim=" + to_str(m.YDim)
  print "XDim=" + to_str(m.XDim)
end
''')
print(log2)