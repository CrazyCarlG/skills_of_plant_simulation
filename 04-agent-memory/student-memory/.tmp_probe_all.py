"""Probe Input/Solutions paths + other comments/controls via direct socket."""
import importlib.util
spec = importlib.util.spec_from_file_location('ts',
    'C:/Users/z004bjuu/Documents/skills_of_plant_simulation/04-agent-memory/student-memory/.tmp_socket2.py')
ts = importlib.util.module_from_spec(spec); spec.loader.exec_module(ts)


def probe(code):
    env = ts.run_code(code)
    return env.get("log", "")


def section(title):
    print("\n========== " + title + " ==========")


# 1) Find Input + Solutions: search under .Models and .Models.Example
section("Search Input under .Models")
log = probe('''
var root_obj: object := str_to_obj(".Models")
print "###SEARCH###"
if root_obj /= void
  var i: integer
  for i := 1 to root_obj.nrofChildren
    var ch: object := root_obj.getChild(i)
    print "child:" + to_str(ch) + " name=" + to_str(ch.Name) + " class=" + ch.InternalClassType
  next
end
''')
print(log)

section("Search Input under .Models.Example")
log = probe('''
var root_obj: object := str_to_obj(".Models.Example")
print "###SEARCH###"
if root_obj /= void
  var i: integer
  for i := 1 to root_obj.nrofChildren
    var ch: object := root_obj.getChild(i)
    print "child:" + to_str(ch) + " name=" + to_str(ch.Name) + " class=" + ch.InternalClassType
  next
end
''')
print(log)

# 2) Probe other Comments (Comment2..Comment5, Comment22) on .Models.Example.GA
section("Comment texts on .Models.Example.GA")
log = probe('''
var i: integer
var ch: object
for i := 1 to str_to_obj(".Models.Example.GA").nrofChildren
  ch := str_to_obj(".Models.Example.GA").getChild(i)
  if ch.InternalClassType = ".Comment"
    print "name=" + to_str(ch.Name) + " Text=" + to_str(ch.Text)
  end
next
''')
print(log)

# 3) Probe Checkbox + DropDownList + Button + HtmlReport
section("Checkbox/DropDownList/Button/HtmlReport")
log = probe('''
var i: integer
var ch: object
for i := 1 to str_to_obj(".Models.Example.GA").nrofChildren
  ch := str_to_obj(".Models.Example.GA").getChild(i)
  var t: string := ch.InternalClassType
  if t = ".Checkbox" or t = ".DropDownList" or t = ".Button" or t = ".HtmlReport"
    print "--- " + to_str(ch.Name) + " (" + t + ")"
    if t = ".Checkbox"
      print "  checked=" + to_str(ch.Checked)
    end
    if t = ".DropDownList"
      print "  ItemsYDim=" + to_str(ch.ItemsYDim)
      var k: integer
      for k := 1 to ch.ItemsYDim
        print "  item" + to_str(k) + "=" + to_str(ch[k,1])
      next
      print "  selected=" + to_str(ch.selectedIndex)
    end
    if t = ".Button"
      print "  Text=" + to_str(ch.Text)
    end
    if t = ".HtmlReport"
      print "  Content_len=" + to_str(length(ch.Content))
    end
  end
next
''')
print(log)