#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
End-to-end driver: BFS the folder tree → filter Methods → probe source
→ render the library dump.

This composes three sibling skills:

  1. `local-simtalk-get-folder-tree` — BFS to enumerate every object
     in the model down to a given depth (produces a tree JSON).
  2. (filter) — extract `type == "Method"` nodes → candidate paths.
  3. `probe_methods.py` (this skill) — probe every Method.
  4. `render_library.py` (this skill) — render the library dump.

Usage:
  python3 scripts/read_library.py [--no-infobox] \
      [--tree-depth 5] \
      [--tree-in data/tree.json] \
      [--out data/library_dump.json]

If `--tree-in` is provided, the BFS step is skipped and the existing
tree JSON is used. Otherwise `bfs_full.py` is invoked first.
"""
import json
import os
import subprocess
import sys


SELF_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_ROOT = os.path.dirname(SELF_DIR)
TREE_SKILL = "/root/skills_of_plant_simulation/skills/local-simtalk-get-folder-tree"
BFS_FULL = os.path.join(TREE_SKILL, "scripts", "bfs_full.py")
PROBE = os.path.join(SELF_DIR, "probe_methods.py")
RENDER = os.path.join(SELF_DIR, "render_library.py")


def collect_method_paths(tree):
    """Walk the tree and collect `type == "Method"` node paths."""
    paths = []
    def walk(n):
        if n.get("type") == "Method":
            paths.append(n["path"])
        for c in n.get("children", []) or []:
            walk(c)
    walk(tree)
    return sorted(set(paths))


def main():
    args = sys.argv[1:]
    no_infobox = False
    if "--no-infobox" in args:
        no_infobox = True
        args.remove("--no-infobox")

    tree_depth = 5
    if "--tree-depth" in args:
        i = args.index("--tree-depth")
        tree_depth = int(args[i + 1])
        del args[i:i + 2]

    tree_in = None
    if "--tree-in" in args:
        i = args.index("--tree-in")
        tree_in = args[i + 1]
        del args[i:i + 2]

    out_json = "data/library_dump.json"
    if "--out" in args:
        i = args.index("--out")
        out_json = args[i + 1]
        del args[i:i + 2]

    # Decide where to put intermediates
    workdir = os.path.dirname(os.path.abspath(out_json))
    os.makedirs(workdir, exist_ok=True)
    tree_path = tree_in or os.path.join(workdir, "tree.json")
    paths_file = os.path.join(workdir, "method_paths.txt")
    tsv_path = os.path.join(workdir, "methods_raw.tsv")

    # Step 1 — BFS (or reuse)
    if tree_in and os.path.exists(tree_in):
        print(f"reusing tree: {tree_in}", file=sys.stderr)
    else:
        print(f"running BFS: depth={tree_depth} -> {tree_path}", file=sys.stderr)
        cmd = [sys.executable, BFS_FULL]
        if no_infobox:
            cmd.append("--no-infobox")
        cmd += [".", str(tree_depth), tree_path]
        subprocess.run(cmd, check=True)

    # Step 2 — filter Methods
    tree = json.load(open(tree_path, encoding="utf-8"))
    methods = collect_method_paths(tree)
    print(f"found {len(methods)} Method paths in tree", file=sys.stderr)
    with open(paths_file, "w", encoding="utf-8") as f:
        for p in methods:
            f.write(p + "\n")

    if not methods:
        print("no Method objects in tree — nothing to probe", file=sys.stderr)
        # Still write an empty dump for downstream tools
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump({
                "captured_at": "n/a",
                "total_methods": 0,
                "encrypted_methods": [],
                "syntax_error_methods": [],
                "empty_methods": [],
                "void_methods": [],
                "methods": [],
            }, f, ensure_ascii=False, indent=2)
        sys.exit(0)

    # Step 3 — probe
    print(f"probing {len(methods)} methods -> {tsv_path}", file=sys.stderr)
    cmd = [sys.executable, PROBE]
    if no_infobox:
        cmd.append("--no-infobox")
    cmd += [paths_file, tsv_path]
    subprocess.run(cmd, check=True)

    # Step 4 — render
    print(f"rendering -> {out_json}", file=sys.stderr)
    cmd = [sys.executable, RENDER, tsv_path, out_json]
    subprocess.run(cmd, check=True)

    print(f"\nDONE. Library dump: {out_json}", file=sys.stderr)


if __name__ == "__main__":
    main()