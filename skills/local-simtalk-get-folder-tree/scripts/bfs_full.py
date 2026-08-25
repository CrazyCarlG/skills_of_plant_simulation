#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BFS full tree: enumerate every Folder/Frame descendant of basis (or a path) up to depth N.

Usage:
  python3 scripts/bfs_full.py [--no-infobox] <path> <max_depth> <output.json>
  # e.g. python3 scripts/bfs_full.py --no-infobox . 4 /tmp/basis_tree.json

Output JSON:
  {
    "root_path": ..., "root_name": ..., "root_type": ..., "root_numNodes": N,
    "children": [
      { "i": N, "name": ..., "type": ..., "path": ...,
        "children": [ ...recursively if depth < max_depth and type is Folder/Frame ]
      }
    ]
  }

Skill convention (matches local-simtalk-execution v18→v19):
  - On entry, open a non-modal infoBox on the Plant Simulation GUI describing
    what is being done (`infoBox(text, false)`).
  - Update the infoBox at meaningful milestones (top-level Folder changes)
    so the operator can see progress.
  - On exit (success OR failure), close the infoBox defensively — call
    `infoBox("", false)` twice to be safe (idempotent if no box is up).
  - Pass `--no-infobox` to suppress the open/close/update cycle for batch /
    headless runs where nobody is watching the GUI.
"""
import json
import subprocess
import sys

SIMTALK_SEND = "/root/skills_of_plant_simulation/skills/local-simtalk-execution/scripts/simtalk_send.py"

# SimTalk: enumerate direct children of a path passed as a string literal.
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
    safe = text.replace("\\", "\\\\").replace("\"", "\\\"")
    _run_simtalk(f'infoBox("{safe}", false)', timeout=10)


def infobox_close() -> None:
    """Close the infoBox. Call twice defensively — idempotent if no box is up."""
    _run_simtalk('infoBox("", false)', timeout=10)
    _run_simtalk('infoBox("", false)', timeout=10)


def call_one_level(path: str, timeout: float = 15.0) -> dict:
    """Send SimTalk + readlog, return the parsed dict for one level."""
    code = make_code(path)
    cmd_run = [
        sys.executable, SIMTALK_SEND,
        "--timeout", str(timeout),
        "run", code,
    ]
    subprocess.run(cmd_run, capture_output=True, text=True)
    cmd_rl = [
        sys.executable, SIMTALK_SEND,
        "--timeout", str(timeout),
        "readlog",
    ]
    r2 = subprocess.run(cmd_rl, capture_output=True, text=True)
    try:
        env = json.loads(r2.stdout)
    except json.JSONDecodeError:
        print(f"ERR: readlog envelope not JSON for path={path}", file=sys.stderr)
        print(r2.stdout, file=sys.stderr)
        raise
    log_field = env.get("log", "")
    marker = "###BFS_MARKER###"
    if marker not in log_field:
        print(f"ERR: marker not found in log for path={path}", file=sys.stderr)
        print(repr(log_field[-300:]), file=sys.stderr)
        raise RuntimeError("marker missing")
    after = log_field.split(marker)[-1]
    idx = after.find("{")
    if idx == -1:
        raise RuntimeError(f"no JSON start after marker for path={path}")
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
    block = after[start:end]
    return json.loads(block)


def expand_recursive(path: str, depth: int, max_depth: int, stats: dict,
                     on_progress=None) -> dict:
    """Recursively expand a node up to max_depth. Folders and Frames get recursed."""
    if on_progress is not None:
        on_progress(path, depth, stats)
    stats["calls"] += 1
    stats["paths"].append(path)
    level = call_one_level(path)
    if depth >= max_depth:
        return level
    # Recurse into Folder/Frame children
    for ch in level.get("children", []):
        if ch["type"] in ("Folder", "Frame"):
            try:
                sub = expand_recursive(ch["path"], depth + 1, max_depth, stats,
                                       on_progress=on_progress)
                ch["children"] = sub.get("children", [])
            except Exception as e:
                ch["error"] = str(e)
        else:
            ch["children"] = []
    return level


def main():
    args = sys.argv[1:]
    no_infobox = False
    if "--no-infobox" in args:
        no_infobox = True
        args.remove("--no-infobox")
    if len(args) < 3:
        print("usage: bfs_full.py [--no-infobox] <path> <max_depth> <output.json>",
              file=sys.stderr)
        sys.exit(2)
    path = args[0]
    max_depth = int(args[1])
    out_path = args[2]

    def on_progress(current_path: str, current_depth: int, stats: dict) -> None:
        # Update infoBox at every top-level Folder boundary and at the root
        # so the operator can see progress without spamming the GUI.
        if not no_infobox and (current_depth == 0 or current_depth == 1):
            infobox(
                f"[bfs_full] progress: calls={stats['calls']} "
                f"depth={current_depth} path={current_path}"
            )

    try:
        if not no_infobox:
            infobox(
                f"[bfs_full] start: path={path} depth={max_depth} -> {out_path}"
            )

        stats = {"calls": 0, "paths": []}
        tree = expand_recursive(path, 0, max_depth, stats, on_progress=on_progress)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(tree, f, ensure_ascii=False, indent=2)
        print(f"Wrote {out_path}  calls={stats['calls']}", file=sys.stderr)

        if not no_infobox:
            infobox(
                f"[bfs_full] done: calls={stats['calls']} -> {out_path}"
            )
    finally:
        if not no_infobox:
            infobox_close()


if __name__ == "__main__":
    main()