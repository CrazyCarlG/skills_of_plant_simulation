#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
attr_modify.py — read / write / readback / restore attributes on a Plant
Simulation object via the local-simtalk-execution transport.

Usage:
  # Read current value (no change)
  python3 scripts/attr_modify.py --path .Models.Model.EventController \\
      --attr SkipLongEventIntervals --read-only

  # Write + verify, then auto-restore on exit
  python3 scripts/attr_modify.py --path .Models.Model.EventController \\
      --attr SkipLongEventIntervals --value false --type boolean --restore

  # Batch: write three attrs, restore all on exit
  python3 scripts/attr_modify.py \\
      --path .Models.Model.EventController \\
      --batch SkipLongEventIntervals=false:boolean RealtimeScale=5:real RandomNumbersVariant=7:integer \\
      --restore

This script depends on the sibling skill:
  skills/local-simtalk-execution/scripts/simtalk_send.py
  (resolved relative to this file via os.path.realpath(__file__), so it
  works from any cwd and through symlinks.)

Hard rules — see local-simtalk-execution/references/lifelines.md
"""
import argparse
import json
import os
import re
import subprocess
import sys
import uuid

SIMTALK_SEND = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))),
    "skills", "local-simtalk-execution", "scripts", "simtalk_send.py",
)

# ---- SimTalk templates ---------------------------------------------------

# Escape a string literal for SimTalk (which uses double quotes)
def _esc(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\"", "\\\"")


def _build_code(attr: str, new_value: str, attr_type: str, path: str, read_only: bool = False) -> str:
    """Build the SimTalk snippet for: read before, write, read after, print markers.

    When read_only is True, the write line is omitted and attr_type is ignored.
    """
    p = _esc(path)
    a = _esc(attr)

    if read_only:
        # Read-only: don't write, don't require a type. Just print the value.
        return f"""var obj: object := str_to_obj("{p}")
if obj = void
  print "###MARKER###"
  print "ERR: str_to_obj returned void for path={p}"
  print "###END###"
  return
end
print "###MARKER###"
print "{a}: " + to_str(obj.{a})
print "###END###"
"""

    if attr_type == "boolean":
        before_decl = "var before: boolean"
        after_decl = "var after: boolean"
        new_lit = "true" if new_value.lower() in ("true", "1", "yes") else "false"
        setter = f"{attr} := {new_lit}"
    elif attr_type in ("integer", "real", "length"):
        before_decl = f"var before: {attr_type}"
        after_decl = f"var after: {attr_type}"
        setter = f"{attr} := {new_value}"
    elif attr_type in ("string",):
        before_decl = "var before: string"
        after_decl = "var after: string"
        setter = f'{attr} := "{_esc(new_value)}"'
    elif attr_type == "dateTime":
        before_decl = "var before: dateTime"
        after_decl = "var after: dateTime"
        setter = f'{attr} := str_to_dateTime("{_esc(new_value)}")'
    elif attr_type == "time":
        before_decl = "var before: time"
        after_decl = "var after: time"
        setter = f'{attr} := str_to_time("{_esc(new_value)}")'
    elif attr_type in ("object", "method"):
        before_decl = "var before: object"
        after_decl = "var after: object"
        setter = f'{attr} := str_to_obj("{_esc(new_value)}")'
    else:
        raise ValueError(f"Unsupported attribute type: {attr_type}")

    return f"""var obj: object := str_to_obj("{p}")
if obj = void
  print "###MARKER###"
  print "ERR: str_to_obj returned void for path={p}"
  print "###END###"
  return
end
{before_decl} := obj.{a}
obj.{setter}
{after_decl} := obj.{a}
print "###MARKER###"
print "{a}: " + to_str(before) + " -> " + to_str(after)
print "###END###"
"""


def _build_restore_code(records: list) -> str:
    """Build a SimTalk snippet that restores a list of attributes to their original values.

    records: list of (path, attr, attr_type, original_value_str)
    """
    lines = ["var obj: object", "obj := str_to_obj(\"\")"]
    # Resolve each path independently — they may differ in batch mode.
    # Each restore must use a unique variable name (o_0, o_1, ...) because
    # SimTalk forbids redeclaring the same local in one scope.
    restore_lines = []
    for idx, (path, attr, attr_type, original) in enumerate(records):
        p = _esc(path)
        a = _esc(attr)
        v = f"o_{idx}"
        if attr_type == "boolean":
            lit = "true" if original.lower() in ("true", "1", "yes") else "false"
            restore_lines.append(f'var {v}: object := str_to_obj("{p}")')
            restore_lines.append(f"{v}.{a} := {lit}")
        elif attr_type in ("integer", "real", "length"):
            restore_lines.append(f'var {v}: object := str_to_obj("{p}")')
            restore_lines.append(f"{v}.{a} := {original}")
        elif attr_type == "string":
            restore_lines.append(f'var {v}: object := str_to_obj("{p}")')
            restore_lines.append(f'{v}.{a} := "{_esc(original)}"')
        elif attr_type == "dateTime":
            restore_lines.append(f'var {v}: object := str_to_obj("{p}")')
            restore_lines.append(f'{v}.{a} := str_to_dateTime("{_esc(original)}")')
        elif attr_type == "time":
            restore_lines.append(f'var {v}: object := str_to_obj("{p}")')
            restore_lines.append(f'{v}.{a} := str_to_time("{_esc(original)}")')
        else:
            raise ValueError(f"Unsupported restore type: {attr_type}")
        restore_lines.append(f'print "restored: {p}.{a} := " + to_str({v}.{a})')
    body = "\n".join(restore_lines)
    return f"""var obj: object := void
{body}
"""


def _send_run(code: str, timeout: float = 15.0) -> dict:
    """Send a simtalk_run via simtalk_send.py; return parsed JSON envelope."""
    proc = subprocess.run(
        [sys.executable, SIMTALK_SEND, "--timeout", str(int(timeout)), "run", code],
        capture_output=True, text=True,
    )
    if proc.returncode not in (0, 10, 11):
        raise RuntimeError(f"simtalk_send.py exit {proc.returncode}: {proc.stderr}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        raise RuntimeError(f"non-JSON reply: {proc.stdout[:200]}")


def _send_readlog(timeout: float = 10.0) -> str:
    """Send readlog and return the raw log field (may be empty / degraded)."""
    proc = subprocess.run(
        [sys.executable, SIMTALK_SEND, "--timeout", str(int(timeout)), "readlog"],
        capture_output=True, text=True,
    )
    try:
        env = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return ""
    return env.get("log", "")


# Parse the ###MARKER### block out of a log string
_MARKER_RE = re.compile(r"###MARKER###(.*?)###END###", re.DOTALL)


def _extract_markers(log: str) -> str:
    m = _MARKER_RE.search(log)
    return m.group(1).strip() if m else ""


# ---- Main ----------------------------------------------------------------


def _parse_batch(items: list) -> list:
    """Parse --batch values like ['Attr=val:type', ...] into tuples."""
    out = []
    for item in items:
        if ":" not in item:
            raise ValueError(f"--batch item must be 'ATTR=VAL:TYPE', got: {item}")
        lhs, rhs = item.rsplit(":", 1)
        if "=" not in lhs:
            raise ValueError(f"--batch item must be 'ATTR=VAL:TYPE', got: {item}")
        attr, value = lhs.split("=", 1)
        out.append((attr.strip(), value, rhs.strip()))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--path", required=True, help="Plant Simulation path, e.g. .Models.Model.EventController")
    ap.add_argument("--attr", help="Attribute name (single-attribute mode)")
    ap.add_argument("--value", help="New value (single-attribute mode)")
    ap.add_argument("--type", help="Attribute type: boolean / integer / real / string / dateTime / time / object / method / length")
    ap.add_argument("--read-only", action="store_true", help="Just read, don't write")
    ap.add_argument("--restore", action="store_true", help="After writing, restore original value on exit")
    ap.add_argument("--batch", nargs="+", metavar="ATTR=VAL:TYPE",
                    help="Batch mode: one or more 'ATTR=VAL:TYPE' pairs")
    ap.add_argument("--timeout", type=float, default=15.0, help="simtalk_send timeout (default 15s)")
    args = ap.parse_args()

    # Refuse SimtalkClaude writes
    if ".SimtalkClaude" in args.path or ".simtalkclaude" in args.path.lower():
        print("REFUSED: this skill does not write inside .SimtalkClaude.*", file=sys.stderr)
        sys.exit(2)

    if args.batch:
        items = _parse_batch(args.batch)
    else:
        if not args.attr:
            ap.error("--attr is required (or use --batch)")
        if not args.read_only and (args.value is None or not args.type):
            ap.error("--value and --type are required unless --read-only")
        items = [(args.attr, args.value, args.type)]

    records = []  # for --restore
    try:
        for attr, value, attr_type in items:
            print(f"\n=== {args.path}.{attr} ({attr_type}) ===")
            if args.read_only:
                code = _build_code(attr, value, attr_type, args.path, read_only=True)
            else:
                code = _build_code(attr, value, attr_type, args.path, read_only=False)

            resp = _send_run(code, timeout=args.timeout)
            result = resp.get("result", "")
            log = resp.get("log", "")
            if result != "success" or log.startswith("code execute failed"):
                print(f"  EXEC FAIL: result={result!r} log={log!r}", file=sys.stderr)
                sys.exit(11)

            # Capture log field for marker extraction
            capture_log = log
            # Always also pull readlog — the value print may be there, not in `log`
            capture_log += "\n" + _send_readlog(timeout=10.0)

            markers = _extract_markers(capture_log)
            if not markers:
                print(f"  WARN: marker not found in log/readlog — value not captured.")
                print(f"  raw log: {log[:200]!r}")
                continue

            # If restore requested, parse before->after to grab the before value
            if args.restore and not args.read_only:
                # markers look like: "2026-08-26 13:13:39: Attr: <before> -> <after>"
                # (Plant Simulation prefixes a timestamp), so use search, not match.
                m = re.search(rf"{re.escape(attr)}:\s*(.*?)\s*->\s*(.*)", markers)
                if m:
                    before_str = m.group(1).strip()
                    records.append((args.path, attr, attr_type, before_str))

            # Echo what we got
            for line in markers.splitlines():
                print(f"  {line.strip()}")

    finally:
        if args.restore and records:
            print("\n=== restoring ===")
            restore_code = _build_restore_code(records)
            resp = _send_run(restore_code, timeout=args.timeout)
            result = resp.get("result", "")
            log = resp.get("log", "")
            if result == "success" and not log.startswith("code execute failed"):
                print("  restore OK")
            else:
                print(f"  RESTORE FAIL: result={result!r} log={log!r}", file=sys.stderr)


if __name__ == "__main__":
    main()