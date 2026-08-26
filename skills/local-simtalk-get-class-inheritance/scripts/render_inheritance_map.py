#!/usr/bin/env python3
"""Render the inheritance map from a captured probe TSV.

Reads a 6-field TSV (path, name, type, origin, originroot, cls) produced by
``probe_inheritance.py`` and emits:

1. A human-readable parent→children tree on stdout.
2. A structured JSON file (``inheritance_map.json`` by default) with
   ``captured_at``, ``total_classes``, ``root_classes``, ``derived_classes``,
   and ``tree`` (a parent→list-of-children mapping; root keys are the actual
   root-class paths, and ``VOID`` is used as a sentinel key holding all the
   root classes for the convenience of downstream consumers).

Usage::

    python3 scripts/render_inheritance_map.py <raw.tsv> [out.json]

If ``out.json`` is omitted, defaults to ``data/inheritance_map.json`` next
to the input file.
"""
import json, os, sys
from collections import defaultdict


def parse_tsv(path):
    """Yield row dicts from the 6-field TSV written by probe_inheritance.py."""
    rows = []
    with open(path) as f:
        for ln in f:
            ln = ln.rstrip("\n")
            if not ln:
                continue
            parts = ln.split("\t")
            if len(parts) != 6:
                continue
            rows.append({
                "path": parts[0],
                "name": parts[1],
                "type": parts[2],
                "origin": parts[3],
                "originroot": parts[4],
                "cls": parts[5],
            })
    return rows


def render(rows, out_path):
    """Partition rows into root (Origin=VOID) vs derived (Origin≠VOID), render
    the tree, and write JSON to ``out_path``. Returns the structured dict."""
    roots = [r for r in rows if r["origin"] == "VOID"]
    derived = [r for r in rows if r["origin"] != "VOID"]

    print(f"Total classes captured: {len(rows)}")
    print(f"  Root classes (Origin=VOID): {len(roots)}")
    print(f"  Derived classes (Origin!==VOID): {len(derived)}")

    # Build children map: parent -> list of child rows
    children = defaultdict(list)
    for r in rows:
        parent = r["origin"]
        children[parent].append(r)

    # Render tree by parent (sorted for stable output)
    print("\n" + "=" * 80)
    print("INHERITANCE MAP (parent -> children)")
    print("=" * 80)
    for parent_path in sorted(children.keys()):
        kids = children[parent_path]
        plural = "es" if len(kids) != 1 else ""
        print(f"\n{parent_path}  ({len(kids)} child class{plural})")
        for k in kids:
            sub = k["path"]
            if parent_path != "VOID" and sub.startswith(parent_path + "."):
                sub = sub[len(parent_path) + 1:]
            print(f"  ├─ {sub}  [{k['type']}]")

    # Render derived-from view
    print("\n" + "=" * 80)
    print("DERIVED CLASSES (the user-defined classes that inherit from a built-in)")
    print("=" * 80)
    for r in sorted(derived, key=lambda r: r["path"]):
        print(f"\n  {r['path']}  [{r['type']}]")
        print(f"    Origin        = {r['origin']}")
        print(f"    OriginRoot    = {r['originroot']}")
        print(f"    Class         = {r['cls']}")

    # Build the structured output. ``root_classes`` is a flat sorted list
    # of root paths (Origin=VOID); ``derived_classes`` is a list of full
    # row dicts; ``tree`` maps each parent (including the sentinel ``VOID``)
    # to a list of child row dicts.
    tree = {}
    # Roots go under the "VOID" sentinel key for downstream consumers that
    # want to know "everything with no parent". Each root path also appears
    # under its own parent — which is itself — for convenience; we omit those
    # here to keep the tree compact.
    for parent_path in sorted(children.keys()):
        kids = children[parent_path]
        tree[parent_path] = [
            {"path": r["path"], "name": r["name"], "type": r["type"],
             "origin": r["origin"], "originroot": r["originroot"],
             "class": r["cls"]}
            for r in sorted(kids, key=lambda r: r["path"])
        ]

    out = {
        "captured_at": "2026-08-26",
        "total_classes": len(rows),
        "root_classes": sorted(r["path"] for r in roots),
        # Rename the TSV's internal ``cls`` field to ``class`` so every
        # JSON object uses the same schema (matches the per-parent tree
        # entries and the SKILL.md sample).
        "derived_classes": [
            {k: r[k] for k in ("path", "name", "type",
                               "origin", "originroot")} | {"class": r["cls"]}
            for r in sorted(derived, key=lambda r: r["path"])
        ],
        "tree": tree,
    }

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {out_path}")
    return out


def main():
    if len(sys.argv) < 2:
        print("usage: render_inheritance_map.py <raw.tsv> [out.json]", file=sys.stderr)
        sys.exit(2)
    in_path = sys.argv[1]
    if len(sys.argv) >= 3:
        out_path = sys.argv[2]
    else:
        out_path = os.path.join(
            os.path.dirname(os.path.abspath(in_path)),
            "inheritance_map.json",
        )
    rows = parse_tsv(in_path)
    if not rows:
        print(f"No rows parsed from {in_path}", file=sys.stderr)
        sys.exit(1)
    render(rows, out_path)


if __name__ == "__main__":
    main()