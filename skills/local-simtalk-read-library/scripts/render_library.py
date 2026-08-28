#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Render a library dump from the probe output of `probe_methods.py`.

Inputs:
  <raw.tsv>    tab-separated output produced by probe_methods.py
                (8 fields per row: path, name, type, encrypted,
                has_syntax_error, num_in_execution, program_len, program)

Outputs:
  <out.json>   structured library dump (default: data/library_dump.json)
  stdout       human-readable summary

Usage:
  python3 scripts/render_library.py [--show-source] <raw.tsv> [out.json]
"""
import json
import os
import sys
import time


def parse_tsv(path):
    """Yield row dicts from the 8-field TSV.

    The `program` field (field 7) may span multiple physical lines because
    `probe_methods.py` writes literal newlines inside multi-line Method
    bodies. Naïve per-line parsing splits each such body into phantom rows.
    Recovery heuristic (LIB-7): a real record starts at a line whose first
    field begins with `.` (Plant Simulation path) and has >= 8 tab-separated
    fields. Lines after a record start until the next record start are
    appended to that record's `program`.
    """
    rows = []
    with open(path, encoding="utf-8") as f:
        raw_lines = f.readlines()

    i = 0
    while i < len(raw_lines):
        ln = raw_lines[i].rstrip("\n")
        if not ln:
            i += 1
            continue
        parts = ln.split("\t")
        # A record header: first field starts with '.', >= 8 tab fields.
        if not (parts and parts[0].startswith(".") and len(parts) >= 8):
            # Stray continuation outside any record — skip.
            i += 1
            continue
        prog_lines = ["\t".join(parts[7:])]
        i += 1
        # Accumulate continuation lines until next record header or EOF.
        while i < len(raw_lines):
            nxt = raw_lines[i].rstrip("\n")
            if nxt:
                nxt_parts = nxt.split("\t")
                if nxt_parts and nxt_parts[0].startswith(".") and len(nxt_parts) >= 8:
                    break  # next record starts here
            prog_lines.append(nxt)
            i += 1
        prog = "\n".join(prog_lines)
        rows.append({
            "path": parts[0],
            "name": parts[1],
            "type": parts[2],
            "encrypted": parts[3].lower() == "true",
            "has_syntax_error": parts[4].lower() == "true",
            "num_in_execution": parts[5],
            "program_len": int(parts[6]) if parts[6].isdigit() else 0,
            "program": prog,
        })
    return rows


def render(rows, out_path, show_source=False):
    """Partition rows, render the summary, write JSON."""
    total = len(rows)
    encrypted = [r for r in rows if r["encrypted"]]
    syntax_errors = [r for r in rows if r["has_syntax_error"]]
    empty = [r for r in rows if r["program_len"] == 0 and not r["encrypted"]]
    void_rows = [r for r in rows if not r["name"] and not r["type"]]

    print(f"Total Methods captured: {total}")
    print(f"  Encrypted:             {len(encrypted)}")
    print(f"  Has syntax error:      {len(syntax_errors)}")
    print(f"  Empty (no source):     {len(empty)}")
    print(f"  VOID / unresolved:     {len(void_rows)}")

    # Per-method one-line summary
    print()
    print("=" * 80)
    print("METHOD SUMMARY (path | type | size | status)")
    print("=" * 80)
    for r in rows:
        status = "ok"
        if r["encrypted"]:
            status = "ENCRYPTED"
        elif r["has_syntax_error"]:
            status = "SYNTAX ERROR"
        elif r["program_len"] == 0:
            status = "empty"
        elif not r["name"]:
            status = "VOID"
        size = f"{r['program_len']:>5} B"
        print(f"  {r['path']:<55} {r['type']:<12} {size}   {status}")

    if show_source:
        print()
        print("=" * 80)
        print("FULL SOURCE (verbatim)")
        print("=" * 80)
        for r in rows:
            print()
            print(f"--- {r['path']} ---")
            if r["encrypted"]:
                print("<encrypted>")
            else:
                print(r["program"])

    # Structured output
    out = {
        "captured_at": None,
        "total_methods": total,
        "encrypted_methods": [r["path"] for r in encrypted],
        "syntax_error_methods": [r["path"] for r in syntax_errors],
        "empty_methods": [r["path"] for r in empty],
        "void_methods": [r["path"] for r in void_rows],
        "methods": [
            {
                "path": r["path"],
                "name": r["name"],
                "type": r["type"],
                "encrypted": r["encrypted"],
                "has_syntax_error": r["has_syntax_error"],
                "num_in_execution": r["num_in_execution"],
                "program_len": r["program_len"],
                "program": r["program"],
            }
            for r in rows
        ],
    }
    out["captured_at"] = time.strftime("%Y-%m-%d")

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {out_path}")


def main():
    args = sys.argv[1:]
    show_source = False
    if "--show-source" in args:
        show_source = True
        args.remove("--show-source")
    if len(args) < 1:
        print("usage: render_library.py [--show-source] <raw.tsv> [out.json]",
              file=sys.stderr)
        sys.exit(2)
    in_path = args[0]
    if len(args) >= 2:
        out_path = args[1]
    else:
        out_path = os.path.join(
            os.path.dirname(os.path.abspath(in_path)),
            "library_dump.json",
        )
    rows = parse_tsv(in_path)
    if not rows:
        print(f"No rows parsed from {in_path}", file=sys.stderr)
        sys.exit(1)
    render(rows, out_path, show_source=show_source)


if __name__ == "__main__":
    main()