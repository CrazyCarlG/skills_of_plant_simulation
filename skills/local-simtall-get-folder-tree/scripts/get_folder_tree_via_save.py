#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
get_folder_tree_via_save.py — 调用 saveFolderModel 把当前模型
保存为 .psfm 文件夹结构，然后 walk 这个目录得到模型结构。

用法：
    python3 get_folder_tree_via_save.py \
        --host host.docker.internal --port 50007 \
        --psfm 'D:\\temp\\model_dump.psfm' \
        --out ./ps_folder_tree.json
"""

import argparse
import json
import subprocess
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SOCKET_CLIENT = REPO_ROOT / "skills" / "local-simtalk-execution" / "scripts" / "socket_client.py"

END_DEL = "||END||"


def call_save_folder_model(host, port, timeout, out_path):
    """发 simtalk_run 调用 saveFolderModel。"""
    # JSON 字符串里反斜杠要双重转义
    escaped = out_path.replace("\\", "\\\\")
    code = f'saveFolderModel("{escaped}", true, false)'

    payload = {
        "type": "simtalk_run",
        "action_id": uuid.uuid4().hex,
        "simtalk_code": code,
    }
    proc = subprocess.run(
        [sys.executable, str(SOCKET_CLIENT),
         "--host", host, "--port", str(port), "--timeout", str(timeout),
         "--data", json.dumps(payload) + END_DEL,
         "--resp-mode", "delimiter", "--resp-delimiter", END_DEL],
        capture_output=True, text=True, timeout=timeout + 5,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"socket_client.py exit={proc.returncode}: stdout={proc.stdout.strip()}"
        )
    reply = proc.stdout.rstrip("\n")
    if reply.endswith(END_DEL):
        reply = reply[: -len(END_DEL)]
    resp = json.loads(reply)

    # Quirk #7 双重判据
    if resp.get("result") != "success":
        raise RuntimeError(f"saveFolderModel failed: {resp}")
    if resp.get("log", "").startswith("code execute failed"):
        raise RuntimeError(f"saveFolderModel soft-fail (Quirk #7): {resp}")


def walk_psfm(root: Path):
    """walk .psfm 目录，返回树状 dict。"""
    tree = {"name": root.name, "type": "FolderModel", "path": str(root), "children": []}

    def visit(node: Path, parent: dict):
        for entry in sorted(node.iterdir()):
            child = {"name": entry.name, "path": str(entry)}
            if entry.is_dir():
                child["type"] = "Folder"
                child["children"] = []
                parent["children"].append(child)
                visit(entry, child)
            elif entry.suffix == ".yaml":
                child["type"] = "Yaml"
                parent["children"].append(child)
            elif entry.suffix == ".spp":
                child["type"] = "ModelEntry"
                parent["children"].append(child)
            elif entry.suffix == ".py":
                child["type"] = "PythonModule"
                parent["children"].append(child)
            else:
                child["type"] = "File"
                parent["children"].append(child)

    visit(root, tree)
    return tree


def print_tree(node, indent=0, max_depth=10):
    if indent > max_depth:
        print("  " * indent + "...(depth limit)")
        return
    print("  " * indent + f"{node.get('name','?')} [{node.get('type','?')}]")
    for child in node.get("children", []) or []:
        print_tree(child, indent + 1, max_depth)


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--host", default="host.docker.internal")
    ap.add_argument("--port", type=int, default=50007)
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--psfm", default=r"D:\\temp\\model_dump.psfm",
                    help="服务端要写出的 .psfm 路径（Windows）")
    ap.add_argument("--out", default="./ps_folder_tree.json")
    ap.add_argument("--print", action="store_true")
    ap.add_argument("--max-print-depth", type=int, default=10)
    args = ap.parse_args()

    print(f"→ saveFolderModel → {args.psfm}", file=sys.stderr)
    call_save_folder_model(args.host, args.port, args.timeout, args.psfm)

    root = Path(args.psfm)
    if not root.exists():
        raise RuntimeError(
            f"saveFolderModel 报成功但目录 {root} 不存在 — "
            f"检查路径 / 写权限 / 服务端是否在同一主机"
        )

    tree = walk_psfm(root)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(tree, f, ensure_ascii=False, indent=2)
    print(f"✅ wrote {args.out}  ({len(tree.get('children', []))} top-level entries)")

    if args.print:
        print()
        print_tree(tree, max_depth=args.max_print_depth)


if __name__ == "__main__":
    main()