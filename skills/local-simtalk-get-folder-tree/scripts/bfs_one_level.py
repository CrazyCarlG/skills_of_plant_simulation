#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BFS one level: enumerate direct children of a given object path on the PS server.

Usage:
  python3 scripts/bfs_one_level.py [--no-infobox] <path>
  # e.g. python3 scripts/bfs_one_level.py .
  #      python3 scripts/bfs_one_level.py --no-infobox .SimtalkClaude

Output:
  Pretty-printed JSON on stdout with keys:
    root_path: absolute path string (resolved by server)
    root_name: short name
    root_type: InternalClassType
    root_numNodes: count of direct children (Folder/Frame.numNodes)
    children: list of {i, name, type, path}

Skill convention (matches local-simtalk-execution v18→v19):
  - On entry, open a non-modal infoBox on the Plant Simulation GUI describing
    what is being done (`infoBox(text, false)`).
  - On exit (success OR failure), close the infoBox defensively — call
    `infoBox("", false)` twice to be safe (idempotent if no box is up).
  - Pass `--no-infobox` to suppress the open/close cycle for batch / headless
    runs where nobody is watching the GUI.
"""
import json
import os
import subprocess
import sys

SIMTALK_SEND = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))), "skills", "local-simtalk-execution", "scripts", "simtalk_send.py")

# SimTalk that takes a path baked in as a string literal, navigates to it
# using str_to_obj, then enumerates its children. We bake the path into the
# code rather than passing via `param` because simtalk_run silently accepts
# `param` declarations as local vars and never binds external arguments.
SIMTALK_TEMPLATE = """var p_path: string := "__PATH__"
var rootObj: object
rootObj := str_to_obj(p_path)
if rootObj = void
  print "###BFS_MARKER###"
  print "ERR: cannot resolve path: " + p_path
  return
end
var ch: object
var n: integer
n := rootObj.numNodes
var buf: string := chr(123) + chr(34) + "root_path" + chr(34) + ":" + chr(34) + obj_to_str(rootObj) + chr(34) + "," + chr(34) + "root_name" + chr(34) + ":" + chr(34) + rootObj.Name + chr(34) + "," + chr(34) + "root_type" + chr(34) + ":" + chr(34) + rootObj.InternalClassType + chr(34) + "," + chr(34) + "root_numNodes" + chr(34) + ":" + to_str(n) + "," + chr(34) + "children" + chr(34) + ":["
var sep: string := ""
var ln: string
var i: integer
for i := 1 to n
  ch := rootObj.node(i)
  ln := chr(123) + chr(34) + "i" + chr(34) + ":" + to_str(i) + "," + chr(34) + "name" + chr(34) + ":" + chr(34) + ch.Name + chr(34) + "," + chr(34) + "type" + chr(34) + ":" + chr(34) + ch.InternalClassType + chr(34) + "," + chr(34) + "path" + chr(34) + ":" + chr(34) + obj_to_str(ch) + chr(34) + chr(125)
  buf := buf + sep + ln
  sep := ","
next
buf := buf + "]}"
print "###BFS_MARKER###"
print buf
"""


def make_code(path: str) -> str:
    # SimTalk strings use double quotes; escape literal " and \
    escaped = path.replace("\\", "\\\\").replace("\"", "\\\"")
    return SIMTALK_TEMPLATE.replace("__PATH__", escaped)


def _run_simtalk(code: str, timeout: int = 10) -> None:
    """Send a one-shot SimTalk snippet via the simtalk_send helper. Fire-and-forget."""
    subprocess.run(
        [sys.executable, SIMTALK_SEND, "--timeout", str(timeout), "run", code],
        capture_output=True,
        text=True,
    )


def infobox(text: str) -> None:
    """Open or update a non-modal infoBox on the Plant Simulation GUI."""
    # Escape for SimTalk string literal: \" and \\
    safe = text.replace("\\", "\\\\").replace("\"", "\\\"")
    _run_simtalk(f'infoBox("{safe}", false)', timeout=10)


def infobox_close() -> None:
    """Close the infoBox. Call twice defensively — idempotent if no box is up."""
    _run_simtalk('infoBox("", false)', timeout=10)
    _run_simtalk('infoBox("", false)', timeout=10)


def main():
    args = sys.argv[1:]
    no_infobox = False
    if "--no-infobox" in args:
        no_infobox = True
        args.remove("--no-infobox")
    if len(args) != 1:
        print("usage: bfs_one_level.py [--no-infobox] <path>", file=sys.stderr)
        sys.exit(2)
    p = args[0]
    code = make_code(p)

    if not no_infobox:
        infobox(f"[bfs_one_level] start: path={p}")

    try:
        cmd = [
            sys.executable, SIMTALK_SEND,
            "--timeout", "15",
            "run", code,
        ]
        subprocess.run(cmd, capture_output=True, text=True)

        cmd_rl = [
            sys.executable, SIMTALK_SEND,
            "--timeout", "10",
            "readlog",
        ]
        r2 = subprocess.run(cmd_rl, capture_output=True, text=True)

        # readlog stdout is a JSON envelope: { "type":..., "log": "..." }
        # Parse the envelope, then look at `log`.
        try:
            env = json.loads(r2.stdout)
        except json.JSONDecodeError:
            print("ERR: readlog envelope not JSON", file=sys.stderr)
            print(r2.stdout, file=sys.stderr)
            sys.exit(1)

        log_field = env.get("log", "")
        marker = "###BFS_MARKER###"
        if marker not in log_field:
            print("ERR: marker not found in log field", file=sys.stderr)
            print(repr(log_field[-300:]), file=sys.stderr)
            sys.exit(1)
        after = log_field.split(marker)[-1]

        # Walk braces from first `{` to find the JSON object.
        idx = after.find("{")
        if idx == -1:
            print("ERR: no JSON start after marker", file=sys.stderr)
            print(repr(after[-300:]), file=sys.stderr)
            sys.exit(1)
        depth = 0
        start = -1
        end = -1
        for i in range(idx, len(after)):
            c = after[i]
            if c == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        if start == -1 or end == -1:
            print("ERR: unbalanced braces after marker", file=sys.stderr)
            print(repr(after), file=sys.stderr)
            sys.exit(1)
        block = after[start:end]
        try:
            parsed = json.loads(block)
        except json.JSONDecodeError:
            print("ERR: block not valid JSON", file=sys.stderr)
            print(block, file=sys.stderr)
            sys.exit(1)
        print(json.dumps(parsed, ensure_ascii=False, indent=2))
    finally:
        if not no_infobox:
            infobox_close()


if __name__ == "__main__":
    main()