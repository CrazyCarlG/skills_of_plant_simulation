#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
get_folder_structure.py — 通过 sibling skill local-simtalk-execution
拉取 Plant Simulation 模型的对象层级结构，写到一棵 JSON 树里。

用法：
    python3 get_folder_structure.py \
        --host host.docker.internal --port 50007 \
        --root .current \
        --out ./model_tree.json \
        --tmp ./ps_snapshots

工作原理：
    1. 维护 BFS 队列，每轮对当前 Frame / Folder 发 simtalk_run；
       simtalk_code 在服务端把当前对象的一层子节点展开成 JSON 并写盘。
    2. 客户端读 JSON snapshot，挑选 InternalClassType ∈ {Frame, Folder}
       的项入队，继续展开，直到队列清空。
    3. 拼出整棵 JSON 树写到 --out。

约束（全部继承自 local-simtalk-execution/references/lifelines.md）：
    - 必须 --resp-mode delimiter --resp-delimiter '||END||'
    - type 必须白名单 {ping, simtalk_syntax, simtalk_run, readlog}
    - Quirk #7：simtalk_run 软失败 (result=='success' + log.startswith('code execute failed'))
"""

import argparse
import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SOCKET_CLIENT = REPO_ROOT / "skills" / "local-simtalk-execution" / "scripts" / "socket_client.py"

END_DEL = "||END||"

# SimTalk 载荷：把当前 Frame / Folder 的一层子节点展开成 JSON 并写盘。
# 注意：__OUT__ 占位符会被替换成实际 outPath；替换时反斜杠需要双重转义。
SIMTALK_TEMPLATE = r"""param outPath: string := "__OUT__"
var root: object := current
var j: json
var arr: json
var child: object
var cj: json
var n: integer
var i: integer
j["path"] := obj_to_str(root)
j["name"] := root.Name
j["type"] := root.InternalClassType
j["numNodes"] := root.numNodes
arr := j.getOrCreateJSON("children")
n := root.numNodes
for i := 1 to n
  child := root.node(i)
  cj["name"] := child.Name
  cj["type"] := child.InternalClassType
  cj["path"] := obj_to_str(child)
  cj["hasChildren"] := false
  if child.InternalClassType = "Frame" or child.InternalClassType = "Folder"
    cj["hasChildren"] := true
  end
  arr[i] := cj
next
j.writeFile(outPath)
"""


def send_simtalk_run(host, port, timeout, simtalk_code, context_path=None):
    """发一次 simtalk_run，按 lifelines §6 双重判据判定。"""
    payload = {
        "type": "simtalk_run",
        "action_id": uuid.uuid4().hex,
        "simtalk_code": simtalk_code,
    }
    if context_path:
        payload["context_path"] = context_path

    proc = subprocess.run(
        [
            sys.executable, str(SOCKET_CLIENT),
            "--host", host, "--port", str(port), "--timeout", str(timeout),
            "--data", json.dumps(payload) + END_DEL,
            "--resp-mode", "delimiter", "--resp-delimiter", END_DEL,
        ],
        capture_output=True, text=True, timeout=timeout + 5,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"socket_client.py exit={proc.returncode}: stdout={proc.stdout.strip()} stderr={proc.stderr.strip()}"
        )

    reply = proc.stdout.rstrip("\n")
    if reply.endswith(END_DEL):
        reply = reply[: -len(END_DEL)]

    try:
        resp = json.loads(reply)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"服务端回包非 JSON ({e}): {reply[:200]!r}")

    # Quirk #7 双重判据（lifelines.md §6）
    if resp.get("result") != "success":
        raise RuntimeError(f"simtalk_run failed: {resp}")
    if resp.get("log", "").startswith("code execute failed"):
        raise RuntimeError(f"simtalk_run soft-fail (Quirk #7): {resp}")
    return resp


def expand_one(host, port, timeout, path, out_file):
    """对单个 Frame / Folder 发 simtalk_run，展开一层。"""
    # JSON 内的反斜杠需要双倍转义；Linux 路径不需要
    safe_out = out_file.replace("\\", "\\\\")
    code = SIMTALK_TEMPLATE.replace("__OUT__", safe_out)
    return send_simtalk_run(host, port, timeout, code, context_path=path)


def safe_filename(path: str) -> str:
    """把绝对路径变成可作为文件名的字符串。"""
    return path.replace(".", "_").replace("/", "_").replace("\\", "_") + ".json"


def walk(host, port, timeout, root_path, tmp_dir):
    """BFS 遍历，返回拼好的树（dict）。"""
    tmp_dir = Path(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)

    queue = [(root_path, 0)]  # (path, depth)
    visited = set()
    snapshots = {}  # path -> snapshot dict

    while queue:
        path, depth = queue.pop(0)
        if path in visited:
            continue
        visited.add(path)

        snap_file = tmp_dir / safe_filename(path)
        print(f"[depth={depth}] expand {path} → {snap_file}", file=sys.stderr)
        expand_one(host, port, timeout, path, str(snap_file))

        try:
            with snap_file.open("r", encoding="utf-8") as f:
                snap_data = json.load(f)
        except FileNotFoundError:
            raise RuntimeError(
                f"服务端写了 simtalk_run 成功但文件 {snap_file} 不存在 — "
                f"检查 outPath 是否可达、是否可写"
            )

        snapshots[path] = snap_data
        for child in snap_data.get("children", []):
            if child.get("hasChildren"):
                queue.append((child["path"], depth + 1))

    return assemble_tree(snapshots, root_path)


def assemble_tree(snapshots, root_path):
    """把所有单层 snapshot 拼成一棵嵌套树。"""
    if root_path not in snapshots:
        raise RuntimeError(f"root {root_path} 没在 snapshots 里")

    root = dict(snapshots[root_path])

    def fill(node):
        new_children = []
        for child in node.get("children", []):
            child_path = child["path"]
            if child_path in snapshots:
                # 用更深的 snapshot 覆盖占位字段
                deeper = snapshots[child_path]
                merged = {**child, **{k: v for k, v in deeper.items() if k != "children"}}
                merged["children"] = deeper.get("children", [])
                fill(merged)
                new_children.append(merged)
            else:
                new_children.append(child)
        node["children"] = new_children

    fill(root)
    return root


def print_tree(node, indent=0, max_depth=10):
    """控制台打印简单树状图。"""
    if indent > max_depth:
        print("  " * indent + "...(depth limit)")
        return
    head = f"{node.get('name','?')} [{node.get('type','?')}] ({node.get('path','?')})"
    print("  " * indent + head)
    for child in node.get("children", []) or []:
        print_tree(child, indent + 1, max_depth)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--host", default="host.docker.internal",
                    help="Plant Simulation TCP 服务端 host（WSL2 默认 host.docker.internal）")
    ap.add_argument("--port", type=int, default=50007,
                    help="Plant Simulation TCP 服务端 port")
    ap.add_argument("--timeout", type=float, default=30.0,
                    help="单次 simtalk_run 超时（秒）")
    ap.add_argument("--root", default=".current",
                    help="要展开的根绝对路径，默认 .current")
    ap.add_argument("--out", default="./ps_folder_structure.json",
                    help="最终 JSON 树的输出文件")
    ap.add_argument("--tmp", default="./ps_snapshots",
                    help="中间单层 snapshot 落盘目录（服务端写到 tmp 目录后客户端来读）")
    ap.add_argument("--print", action="store_true",
                    help="同时在控制台打印树状图")
    ap.add_argument("--max-print-depth", type=int, default=10)
    args = ap.parse_args()

    tree = walk(args.host, args.port, args.timeout, args.root, args.tmp)

    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(tree, f, ensure_ascii=False, indent=2)
    print(f"✅ wrote {args.out}  ({len(tree.get('children', []))} top-level children)")

    if args.print:
        print()
        print_tree(tree, max_depth=args.max_print_depth)


if __name__ == "__main__":
    main()