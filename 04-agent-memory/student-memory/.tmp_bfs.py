"""BFS one level for Python_GA_Demo — bypass bfs_one_level.py cp1252 defect."""
import json, os, subprocess, sys, time

SIMTALK_SEND = r"C:/Users/z004bjuu/Documents/skills_of_plant_simulation/skills/local-simtalk-execution/scripts/simtalk_send.py"

def bfs(path):
    escaped = path.replace("\\", "\\\\").replace("\"", "\\\"")
    code = (
        'var p_path: string := "' + escaped + '"\n'
        'var rootObj: object\n'
        'rootObj := str_to_obj(p_path)\n'
        'if rootObj = void\n'
        '  print "###BFS_MARKER###"\n'
        '  print "ERR: cannot resolve path: " + p_path\n'
        '  return\n'
        'end\n'
        'var ch: object\n'
        'var n: integer\n'
        'n := rootObj.numNodes\n'
        'var buf: string := chr(123) + chr(34) + "root_path" + chr(34) + ":" + chr(34) + obj_to_str(rootObj) + chr(34) + "," + chr(34) + "root_name" + chr(34) + ":" + chr(34) + rootObj.Name + chr(34) + "," + chr(34) + "root_type" + chr(34) + ":" + chr(34) + rootObj.InternalClassType + chr(34) + "," + chr(34) + "root_numNodes" + chr(34) + ":" + to_str(n) + "," + chr(34) + "children" + chr(34) + ":["\n'
        'var sep: string := ""\n'
        'var ln: string\n'
        'var i: integer\n'
        'for i := 1 to n\n'
        '  ch := rootObj.node(i)\n'
        '  ln := chr(123) + chr(34) + "i" + chr(34) + ":" + to_str(i) + "," + chr(34) + "name" + chr(34) + ":" + chr(34) + ch.Name + chr(34) + "," + chr(34) + "type" + chr(34) + ":" + chr(34) + ch.InternalClassType + chr(34) + "," + chr(34) + "path" + chr(34) + ":" + chr(34) + obj_to_str(ch) + chr(34) + chr(125)\n'
        '  buf := buf + sep + ln\n'
        '  sep := ","\n'
        'next\n'
        'buf := buf + "]}"\n'
        'print "###BFS_MARKER###"\n'
        'print buf\n'
    )

    r1 = subprocess.run(
        [sys.executable, SIMTALK_SEND, '--host', '127.0.0.1', '--port', '50007', '--timeout', '15', 'run', code],
        capture_output=True, text=True, encoding='utf-8'
    )
    r2 = subprocess.run(
        [sys.executable, SIMTALK_SEND, '--host', '127.0.0.1', '--port', '50007', '--timeout', '10', 'readlog'],
        capture_output=True, text=True, encoding='utf-8'
    )
    if r2.returncode not in (0, 20):
        return {"err": "readlog fail", "rc": r2.returncode, "stderr": r2.stderr[:500]}
    try:
        env = json.loads(r2.stdout)
    except json.JSONDecodeError:
        return {"err": "envelope not JSON", "raw": r2.stdout[:500]}
    log = env.get("log", "")
    if "###BFS_MARKER###" not in log:
        return {"err": "marker not found", "log_tail": repr(log[-300:])}
    after = log.split("###BFS_MARKER###")[-1]
    idx = after.find("{")
    if idx == -1:
        return {"err": "no JSON start", "tail": repr(after[-300:])}
    depth = 0
    start = end = -1
    for k in range(idx, len(after)):
        c = after[k]
        if c == "{":
            if depth == 0:
                start = k
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                end = k + 1
                break
    if start == -1 or end == -1:
        return {"err": "unbalanced braces", "raw": repr(after)}
    block = after[start:end]
    try:
        return json.loads(block)
    except json.JSONDecodeError:
        return {"err": "block not JSON", "raw": block[:500]}


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else ".Models"
    result = bfs(target)
    print(json.dumps(result, ensure_ascii=False, indent=2))