"""Final probe for Python_GA_Demo model: remaining DataTables + UI controls."""
import importlib.util, sys, time
spec = importlib.util.spec_from_file_location('ts',
    'C:/Users/z004bjuu/Documents/skills_of_plant_simulation/04-agent-memory/student-memory/.tmp_socket2.py')
ts = importlib.util.module_from_spec(spec); spec.loader.exec_module(ts)


def probe_dump(code, marker_start, marker_end="###END###", timeout=0.4):
    ts.run_code(code)
    time.sleep(timeout)
    env = ts.read_log()
    log = env.get("log", "")
    if marker_start in log:
        return log.split(marker_start)[-1].split(marker_end)[0]
    return log[-2000:]


# 1) .Models.Example.setupMatrix contents
print("\n===== setupMatrix =====")
code = '''
print "###SM###"
var sm: object := str_to_obj(".Models.Example.setupMatrix")
if sm = void
  print "VOID"
  return
end
print "YD=" + to_str(sm.YDim) + " XD=" + to_str(sm.XDim)
print "YDnames=" + to_str(sm.YDimNames)
print "XDnames=" + to_str(sm.XDimNames)
var i: integer
var j: integer
for i := 1 to sm.YDim
  var line: string := ""
  for j := 1 to sm.XDim
    if j > 1 then line := line + "|" end
    line := line + to_str(sm[j,i])
  next
  print "r" + to_str(i) + "=" + line
next
print "###END###"
'''
print(probe_dump(code, "###SM###"))


# 2) .Models.Example.Delivery contents
print("\n===== Delivery =====")
code = '''
print "###DL###"
var d: object := str_to_obj(".Models.Example.Delivery")
if d = void
  print "VOID"
  return
end
print "YD=" + to_str(d.YDim) + " XD=" + to_str(d.XDim)
var i: integer
var j: integer
for i := 1 to d.YDim
  var line: string := ""
  for j := 1 to d.XDim
    if j > 1 then line := line + "|" end
    line := line + to_str(d[j,i])
  next
  print "r" + to_str(i) + "=" + line
next
print "###END###"
'''
print(probe_dump(code, "###DL###"))


# 3) .Models.Example.GA children enumeration (to confirm known structure)
print("\n===== .Models.Example.GA children =====")
code = '''
print "###GA###"
var g: object := str_to_obj(".Models.Example.GA")
print "n=" + to_str(g.numNodes)
var i: integer
for i := 1 to g.numNodes
  var ch: object := g.node(i)
  print "name=" + to_str(ch.Name) + " type=" + to_str(ch.InternalClassType)
next
print "###END###"
'''
print(probe_dump(code, "###GA###"))


# 4) Comment texts on .Models.Example.GA
print("\n===== Comment texts =====")
code = '''
print "###CM###"
var g: object := str_to_obj(".Models.Example.GA")
var i: integer
for i := 1 to g.numNodes
  var ch: object := g.node(i)
  if ch.InternalClassType = ".Comment"
    print "name=" + to_str(ch.Name) + " Text=" + to_str(ch.Text)
  end
next
print "###END###"
'''
print(probe_dump(code, "###CM###"))


# 5) UI controls: Checkbox + DropDownList + Button + HtmlReport on .Models.Example.GA
print("\n===== UI controls =====")
code = '''
print "###UI###"
var g: object := str_to_obj(".Models.Example.GA")
var i: integer
for i := 1 to g.numNodes
  var ch: object := g.node(i)
  var t: string := ch.InternalClassType
  if t = ".Checkbox"
    print "Check|name=" + to_str(ch.Name) + " checked=" + to_str(ch.Checked)
  end
  if t = ".DropDownList"
    print "DDL|name=" + to_str(ch.Name) + " itemsYDim=" + to_str(ch.ItemsYDim)
    var k: integer
    for k := 1 to ch.ItemsYDim
      print "  item" + to_str(k) + "=" + to_str(ch[k,1])
    next
    print "  selected=" + to_str(ch.selectedIndex)
  end
  if t = ".Button"
    print "BTN|name=" + to_str(ch.Name) + " Text=" + to_str(ch.Text)
  end
  if t = ".HtmlReport"
    print "HR|name=" + to_str(ch.Name) + " Content_len=" + to_str(length(ch.Content))
    print "  Content_head=" + to_str(mid(ch.Content, 1, 100))
  end
next
print "###END###"
'''
print(probe_dump(code, "###UI###"))