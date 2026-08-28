#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
class_ops.py — Plant Simulation Class Library mutating operations.

Sends one SimTalk snippet per call through `local-simtalk-execution`'s
`simtalk_send.py run` helper, parses the marker-delimited `KEY:VALUE`
output printed back via the `log` field, and emits a JSON envelope on
stdout describing the before/after state.

Usage:
  class_ops.py [--no-infobox] <subcommand> <args...>

Subcommands (each wraps ONE SimTalk call):
  list           <folder>
  inspect        <path>
  derive         <parent> [dest] [name]
  duplicate      <source> [dest] [name]
  rename         <path> <new_name>
  delete         <path>
  move           <path> <folder>
  add-attr       <path> <name> <type>
  del-attr       <path> <name>
  set-attr       <path> <name> <value>
  inherit-attr   <path> <name>

Skill convention (matches local-simtalk-execution v18→v19):
  - On entry, open a non-modal infoBox on the Plant Simulation GUI
    describing the op.
  - On exit (success OR failure), close the infoBox defensively — call
    `infoBox("", false)` twice to be safe (idempotent if no box is up).
  - Pass `--no-infobox` as the first argument to suppress the open/close
    cycle for batch / headless runs where nobody is watching the GUI.
"""
import argparse
import json
import os
import re
import subprocess
import sys

SIMTALK_SEND = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))),
    "skills", "local-simtalk-execution", "scripts", "simtalk_send.py",
)

MARKER_START = "###CLASS_OP###"
MARKER_END = "###CLASS_OP_END###"

# SimTalk-side escape rules for embedding inside a SimTalk double-quoted
# string literal: \\ -> \\\\, " -> \\"
def esc_str(s: str) -> str:
    return s.replace("\\", "\\\\").replace("\"", "\\\"")


def send_simtalk(code: str, timeout: float = 30.0) -> tuple:
    """Send SimTalk code via simtalk_send.py run; return (exit_code, reply_json_or_text).

    Exit codes per simtalk_send.py:
      0  = semantic success (print output is in `log` field)
      10 = result != "success" (compile error / server failure)
      11 = Quirk #7 soft failure (runtime exception; result=success but log starts with "code execute failed")
      12 = bad JSON from server
      1/2/3 = socket-level failure
    """
    proc = subprocess.run(
        [sys.executable, SIMTALK_SEND, "--timeout", str(int(timeout)), "run", code],
        capture_output=True,
        text=True,
        timeout=timeout + 10.0,
    )
    return proc.returncode, proc.stdout


def parse_marker_block(log_text: str) -> tuple:
    """Extract the data dict + error string from the server's log field.

    Returns (data_dict, err_or_none). The marker block in the log looks like:

      ...
      ###CLASS_OP###
      BEFORE_PATH:.Foo.Bar
      BEFORE_NAME:Bar
      AFTER_PATH:.UserObjects.Baz
      ...
      ###CLASS_OP_END###
      ...

    Lines outside the markers are noise (server-side log framing,
    timestamps). Lines inside that start with `ERR:` mark a runtime
    failure and abort the parse.
    """
    # SimTalk's log field uses literal two-char "\n" (escaped newlines)
    chunks = log_text.replace("\\n", "\n").split("\n")
    in_block = False
    data = {}
    err = None
    ts_re = re.compile(r"^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}:\s+(.*)$")
    for raw in chunks:
        # Drop server-side timestamp prefix if present
        m_ts = ts_re.match(raw)
        payload = m_ts.group(1) if m_ts else raw
        payload = payload.rstrip().rstrip('"').rstrip()
        if MARKER_START in payload:
            in_block = True
            data = {}
            err = None
            continue
        if MARKER_END in payload:
            in_block = False
            continue
        if not in_block:
            continue
        if payload.startswith("ERR:"):
            err = payload[4:].strip()
            continue
        # KEY:VALUE format. Split on first ':' only (values can contain ':').
        if ":" in payload:
            k, v = payload.split(":", 1)
            data[k.strip()] = v.strip()
    return data, err


def infobox(text: str) -> None:
    """Open or update a non-modal infoBox on the Plant Simulation GUI."""
    safe = esc_str(text)
    send_simtalk(f'infoBox("{safe}", false)', timeout=10.0)


def infobox_close() -> None:
    """Close the infoBox. Call twice defensively — idempotent if no box is up."""
    send_simtalk('infoBox("", false)', timeout=10.0)
    send_simtalk('infoBox("", false)', timeout=10.0)


# ----------------------------------------------------------------------------
# SimTalk templates
# ----------------------------------------------------------------------------

# Header emitted by every snippet so we can locate our block in the log even
# after cumulative-buffer noise.
T_HEADER = f'print "{MARKER_START}"\n'
T_FOOTER = f'print "{MARKER_END}"\n'


def snippet_resolve(path: str, var_name: str = "o") -> str:
    """Emit SimTalk that resolves <path> into <var_name>, or prints ERR."""
    e = esc_str(path)
    return (
        f'var {var_name}: object\n'
        f'{var_name} := str_to_obj("{e}")\n'
        f'if {var_name} = void\n'
        f'  print "{MARKER_START}"\n'
        f'  print "ERR:path_does_not_resolve:{e}"\n'
        f'  return\n'
        f'end\n'
    )


def snippet_list(folder: str) -> str:
    e = esc_str(folder)
    return (
        'var folderObj: object\n'
        f'folderObj := str_to_obj("{e}")\n'
        'if folderObj = void\n'
        f'  print "{MARKER_START}"\n'
        f'  print "ERR:folder_does_not_resolve:{e}"\n'
        '  return\n'
        'end\n'
        'var n: integer := folderObj.numNodes\n'
        f'print "{MARKER_START}"\n'
        'print "FOLDER:" + obj_to_str(folderObj)\n'
        'print "COUNT:" + to_str(n)\n'
        'var ch: object\n'
        'var i: integer\n'
        'for i := 1 to n\n'
        '  ch := folderObj.node(i)\n'
        '  print "CHILD:" + to_str(i) + ":" + ch.Name + ":" + ch.InternalClassType + ":" + obj_to_str(ch)\n'
        'next\n'
        f'print "{MARKER_END}"\n'
    )


def snippet_inspect(path: str) -> str:
    e = esc_str(path)
    return (
        snippet_resolve(path, "o")
        + T_HEADER
        + 'print "PATH:" + obj_to_str(o)\n'
        + 'print "NAME:" + o.Name\n'
        + 'print "TYPE:" + o.InternalClassType\n'
        + 'print "ORIGIN:" + obj_to_str(o.Origin)\n'
        + 'print "ORIGINROOT:" + obj_to_str(o.OriginRoot)\n'
        + 'print "CLASS:" + obj_to_str(o.Class)\n'
        + 'print "NUMATTRIBUTES:" + to_str(o.NumAttr)\n'
        + 'print "NUMCHILDREN:" + to_str(o.NumChildren)\n'
        + T_FOOTER
    )


def snippet_derive(parent: str, dest: str | None, name: str | None) -> str:
    """Build a derive() call with the optional dest/name args filled in.

    SimTalk lets us call derive() with no args; with dest only; with name
    only; or with both. We generate the call form based on what's given.
    """
    e_parent = esc_str(parent)
    parts = ["parentObj.derive"]
    args = []
    if dest:
        args.append(f'str_to_obj("{esc_str(dest)}")')
    if name:
        args.append(f'"{esc_str(name)}"')
    if args:
        parts[-1] = "parentObj.derive(" + ", ".join(args) + ")"
    call = parts[-1]
    return (
        'var parentObj: object\n'
        f'parentObj := str_to_obj("{e_parent}")\n'
        'if parentObj = void\n'
        f'  print "{MARKER_START}"\n'
        f'  print "ERR:parent_does_not_resolve:{e_parent}"\n'
        '  return\n'
        'end\n'
        f'print "{MARKER_START}"\n'
        'print "BEFORE_PATH:" + obj_to_str(parentObj)\n'
        'print "BEFORE_NAME:" + parentObj.Name\n'
        'print "BEFORE_TYPE:" + parentObj.InternalClassType\n'
        f'var newObj: object := {call}\n'
        'if newObj = void\n'
        '  print "ERR:derive_returned_void:name_collision_or_folder_full"\n'
        '  return\n'
        'end\n'
        'print "AFTER_PATH:" + obj_to_str(newObj)\n'
        'print "AFTER_NAME:" + newObj.Name\n'
        'print "AFTER_TYPE:" + newObj.InternalClassType\n'
        'print "AFTER_ORIGIN:" + obj_to_str(newObj.Origin)\n'
        'print "AFTER_ORIGINROOT:" + obj_to_str(newObj.OriginRoot)\n'
        'print "AFTER_CLASS:" + obj_to_str(newObj.Class)\n'
        + T_FOOTER
    )


def snippet_duplicate(source: str, dest: str | None, name: str | None) -> str:
    e_source = esc_str(source)
    args = []
    if dest:
        args.append(f'str_to_obj("{esc_str(dest)}")')
    if name:
        args.append(f'"{esc_str(name)}"')
    call = "srcObj.duplicate(" + ", ".join(args) + ")" if args else "srcObj.duplicate"
    return (
        'var srcObj: object\n'
        f'srcObj := str_to_obj("{e_source}")\n'
        'if srcObj = void\n'
        f'  print "{MARKER_START}"\n'
        f'  print "ERR:source_does_not_resolve:{e_source}"\n'
        '  return\n'
        'end\n'
        f'print "{MARKER_START}"\n'
        'print "BEFORE_PATH:" + obj_to_str(srcObj)\n'
        'print "BEFORE_NAME:" + srcObj.Name\n'
        'print "BEFORE_TYPE:" + srcObj.InternalClassType\n'
        f'var newObj: object := {call}\n'
        'if newObj = void\n'
        '  print "ERR:duplicate_returned_void:name_collision"\n'
        '  return\n'
        'end\n'
        'print "AFTER_PATH:" + obj_to_str(newObj)\n'
        'print "AFTER_NAME:" + newObj.Name\n'
        'print "AFTER_TYPE:" + newObj.InternalClassType\n'
        'print "AFTER_ORIGIN:" + obj_to_str(newObj.Origin)\n'
        'print "AFTER_ORIGINROOT:" + obj_to_str(newObj.OriginRoot)\n'
        'print "AFTER_CLASS:" + obj_to_str(newObj.Class)\n'
        + T_FOOTER
    )


def snippet_rename(path: str, new_name: str) -> str:
    e_path = esc_str(path)
    e_new = esc_str(new_name)
    return (
        snippet_resolve(path, "o")
        + T_HEADER
        + 'print "BEFORE_PATH:" + obj_to_str(o)\n'
        + 'print "BEFORE_NAME:" + o.Name\n'
        + f'var ok: boolean := o.setName("{e_new}")\n'
        + 'if not ok\n'
        + '  print "ERR:setName_returned_false:name_not_unique_or_reserved"\n'
        + '  return\n'
        + 'end\n'
        + 'print "AFTER_PATH:" + obj_to_str(o)\n'
        + 'print "AFTER_NAME:" + o.Name\n'
        + T_FOOTER
    )


def snippet_delete(path: str) -> str:
    return (
        snippet_resolve(path, "o")
        + T_HEADER
        + 'print "BEFORE_PATH:" + obj_to_str(o)\n'
        + 'print "BEFORE_NAME:" + o.Name\n'
        + 'print "BEFORE_TYPE:" + o.InternalClassType\n'
        + 'var ok: boolean := o.deleteObject\n'
        + 'if not ok\n'
        + '  print "ERR:deleteObject_returned_false:live_instances_may_exist"\n'
        + '  return\n'
        + 'end\n'
        + 'print "RESULT:deleted"\n'
        + T_FOOTER
    )


def snippet_move(path: str, folder: str) -> str:
    e_path = esc_str(path)
    e_folder = esc_str(folder)
    return (
        snippet_resolve(path, "o")
        + 'var folderObj: object\n'
        + f'folderObj := str_to_obj("{e_folder}")\n'
        + 'if folderObj = void\n'
        + f'  print "{MARKER_START}"\n'
        + f'  print "ERR:dest_folder_does_not_resolve:{e_folder}"\n'
        + '  return\n'
        + 'end\n'
        + T_HEADER
        + 'print "BEFORE_PATH:" + obj_to_str(o)\n'
        + 'print "BEFORE_NAME:" + o.Name\n'
        + 'var res: object := o.moveToFolder(folderObj)\n'
        + 'if res = void\n'
        + '  print "ERR:moveToFolder_returned_void"\n'
        + '  return\n'
        + 'end\n'
        + 'print "AFTER_PATH:" + obj_to_str(o)\n'
        + 'print "AFTER_NAME:" + o.Name\n'
        + T_FOOTER
    )


def snippet_add_attr(path: str, name: str, atype: str) -> str:
    e_path = esc_str(path)
    e_name = esc_str(name)
    e_type = esc_str(atype)
    return (
        snippet_resolve(path, "o")
        + T_HEADER
        + 'print "BEFORE_PATH:" + obj_to_str(o)\n'
        + f'var ok: boolean := o.createAttr("{e_name}", "{e_type}")\n'
        + 'if not ok\n'
        + '  print "ERR:createAttr_returned_false:name_collision_or_invalid_type"\n'
        + '  return\n'
        + 'end\n'
        + 'print "AFTER_PATH:" + obj_to_str(o)\n'
        + f'print "ATTR_NAME:{e_name}"\n'
        + f'print "ATTR_TYPE:{e_type}"\n'
        + T_FOOTER
    )


def snippet_del_attr(path: str, name: str) -> str:
    e_path = esc_str(path)
    e_name = esc_str(name)
    return (
        snippet_resolve(path, "o")
        + T_HEADER
        + 'print "BEFORE_PATH:" + obj_to_str(o)\n'
        + f'var ok: boolean := o.deleteAttr("{e_name}")\n'
        + 'if not ok\n'
        + '  print "ERR:deleteAttr_returned_false:attr_inherited_or_not_found"\n'
        + '  return\n'
        + 'end\n'
        + 'print "ATTR_NAME:' + e_name + '"\n'
        + 'print "RESULT:deleted"\n'
        + T_FOOTER
    )


def _coerce_value_literal(value: str) -> tuple:
    """Detect a simple SimTalk type for the value and return (literal, type_tag).

    Heuristic only — covers integer / real / boolean / string. For complex
    types (list, table, object) we leave them as string and tell the user to
    use local-simtalk-execution directly.
    """
    v = value.strip()
    low = v.lower()
    if low == "true":
        return "true", "boolean"
    if low == "false":
        return "false", "boolean"
    # Integer: optional sign + digits only
    if re.fullmatch(r"[+-]?\d+", v):
        return v, "integer"
    # Real: digits with optional decimal point + optional exponent
    if re.fullmatch(r"[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?", v):
        return v, "real"
    # String: wrap in escaped SimTalk double-quoted literal
    return '"' + esc_str(v) + '"', "string"


def snippet_set_attr(path: str, name: str, value: str) -> str:
    e_path = esc_str(path)
    e_name = esc_str(name)
    literal, vtype = _coerce_value_literal(value)
    return (
        snippet_resolve(path, "o")
        + T_HEADER
        + 'print "BEFORE_PATH:" + obj_to_str(o)\n'
        + f'var attrRef: any := o.{e_name}\n'
        + f'if attrRef = void\n'
        + f'  print "ERR:uda_not_found:{e_name}"\n'
        + f'  return\n'
        + f'end\n'
        + f'attrRef.setAttribute("InitValue", {literal})\n'
        + 'print "AFTER_PATH:" + obj_to_str(o)\n'
        + f'print "ATTR_NAME:{e_name}"\n'
        + f'print "ATTR_VALUE_TYPE:{vtype}"\n'
        + f'print "ATTR_VALUE_RAW:{esc_str(value)}"\n'
        + T_FOOTER
    )


def snippet_inherit_attr(path: str, name: str) -> str:
    e_path = esc_str(path)
    e_name = esc_str(name)
    return (
        snippet_resolve(path, "o")
        + T_HEADER
        + 'print "BEFORE_PATH:" + obj_to_str(o)\n'
        + f'var attrRef: any := o.{e_name}\n'
        + f'if attrRef = void\n'
        + f'  print "ERR:uda_not_found:{e_name}"\n'
        + f'  return\n'
        + f'end\n'
        + f'attrRef.inheritAttribute("InitValue")\n'
        + 'print "AFTER_PATH:" + obj_to_str(o)\n'
        + f'print "ATTR_NAME:{e_name}"\n'
        + 'print "RESULT:inheritance_restored"\n'
        + T_FOOTER
    )


# ----------------------------------------------------------------------------
# Dispatcher
# ----------------------------------------------------------------------------

# Operations that mutate the model (skip list / inspect for the infoBox dance)
MUTATING = {
    "derive", "duplicate", "rename", "delete", "move",
    "add-attr", "del-attr", "set-attr", "inherit-attr",
}


def run_op(args) -> dict:
    """Compose the SimTalk snippet for the requested op and send it."""
    sub = args.subcommand

    if sub == "list":
        folder = args.path
        code = snippet_list(folder)
    elif sub == "inspect":
        code = snippet_inspect(args.path)
    elif sub == "derive":
        code = snippet_derive(args.path, args.dest, args.name)
    elif sub == "duplicate":
        code = snippet_duplicate(args.path, args.dest, args.name)
    elif sub == "rename":
        code = snippet_rename(args.path, args.new_name)
    elif sub == "delete":
        code = snippet_delete(args.path)
    elif sub == "move":
        code = snippet_move(args.path, args.folder)
    elif sub == "add-attr":
        code = snippet_add_attr(args.path, args.name, args.atype)
    elif sub == "del-attr":
        code = snippet_del_attr(args.path, args.name)
    elif sub == "set-attr":
        code = snippet_set_attr(args.path, args.name, args.value)
    elif sub == "inherit-attr":
        code = snippet_inherit_attr(args.path, args.name)
    else:
        return {"ok": False, "subcommand": sub, "error": f"unknown_subcommand:{sub}"}

    # infoBox (skill convention)
    if not args.no_infobox:
        info_text = f"[class_ops] start: {sub} " + " ".join(
            getattr(args, f) for f in (
                ["path", "dest", "name", "new_name", "folder", "atype", "value"]
                if hasattr(args, "path") else []
            ) if getattr(args, f, None)
        )
        try:
            infobox(info_text[:200])
        except Exception as exc:  # pragma: no cover - GUI side failure is non-fatal
            print(f"[infoBox] warning: {exc}", file=sys.stderr)

    rc, reply = send_simtalk(code)

    # infoBox close (defensive double)
    if not args.no_infobox:
        try:
            infobox_close()
        except Exception:
            pass

    envelope = {"ok": False, "subcommand": sub, "exit_code": rc}

    if rc not in (0,):
        # 10 = semantic fail, 11 = Quirk #7, 12 = bad JSON, 1/2/3 = socket
        envelope["error"] = {
            1: "socket_timeout",
            2: "socket_connect_fail",
            3: "socket_disconnect",
            10: "simtalk_compile_or_runtime_fail",
            11: "simtalk_runtime_exception",  # Quirk #7
            12: "bad_json_from_server",
        }.get(rc, f"unknown_exit_code_{rc}")
        envelope["raw_reply_tail"] = reply[-400:] if reply else ""
        return envelope

    # rc == 0: parse the JSON envelope from simtalk_send.py
    try:
        resp = json.loads(reply)
    except json.JSONDecodeError:
        envelope["error"] = "reply_not_json"
        envelope["raw_reply_tail"] = reply[-400:] if reply else ""
        return envelope

    # v15+ quirk: simtalk_run.log is empty — the actual print output is only
    # retrievable via a follow-up readlog call. Recover it before parsing.
    # simtalk_send.py readlog returns exit 20 (readlog_unreliable_warning) on
    # v15+ but still ships the log content on stdout — treat 20 as success.
    rl_proc = subprocess.run(
        [sys.executable, SIMTALK_SEND, "readlog"],
        capture_output=True, text=True, timeout=20.0,
    )
    if rl_proc.returncode not in (0, 20):
        envelope["error"] = "readlog_fetch_failed"
        envelope["raw_reply_tail"] = (rl_proc.stdout or "")[-400:]
        return envelope
    try:
        rl_resp = json.loads(rl_proc.stdout)
    except json.JSONDecodeError:
        envelope["error"] = "readlog_not_json"
        envelope["raw_reply_tail"] = (rl_proc.stdout or "")[-400:]
        return envelope

    log_text = rl_resp.get("log", "") or ""
    data, err = parse_marker_block(log_text)
    envelope["log_tail"] = log_text[-400:]

    if err is not None:
        envelope["error"] = err
        envelope["data"] = data  # partial state if we got any
        return envelope

    if not data:
        # No markers found at all — the SimTalk code may have failed silently
        # or the server's log field was truncated.
        envelope["error"] = "no_marker_block_in_log"
        return envelope

    # For list/inspect, surface the parsed data directly
    if sub == "list":
        children = []
        # CHILD lines have 4 colon-separated fields: i, name, type, path
        # We re-parse them since they don't fit the simple K:V format.
        ts_re = re.compile(r"^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}:\s+(.*)$")
        for line in log_text.replace("\\n", "\n").split("\n"):
            m_ts = ts_re.match(line)
            payload = m_ts.group(1) if m_ts else line
            if payload.startswith("CHILD:"):
                parts = payload[len("CHILD:"):].split(":")
                if len(parts) == 4:
                    children.append({
                        "i": int(parts[0]),
                        "name": parts[1],
                        "type": parts[2],
                        "path": parts[3],
                    })
        envelope["ok"] = True
        envelope["folder"] = data.get("FOLDER", "")
        envelope["count"] = int(data.get("COUNT", "0"))
        envelope["children"] = children
    else:
        envelope["ok"] = True
        envelope["data"] = data

    return envelope


def main():
    ap = argparse.ArgumentParser(
        prog="class_ops.py",
        description=(
            "Plant Simulation Class Library mutating operations. "
            "Each invocation runs ONE SimTalk snippet via local-simtalk-execution's "
            "simtalk_send.py helper and returns a JSON envelope on stdout."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--no-infobox", action="store_true",
                    help="Suppress the infoBox open/close cycle for headless runs.")
    sub = ap.add_subparsers(dest="subcommand", required=True)

    # list
    p = sub.add_parser("list", help="List children of a Class Library folder")
    p.add_argument("path", help="Folder path (e.g. .UserObjects)")

    # inspect
    p = sub.add_parser("inspect", help="Read Origin/OriginRoot/Class + sizes for one class")
    p.add_argument("path", help="Class path (e.g. .MaterialFlow.Station)")

    # derive
    p = sub.add_parser("derive", help="Create a subclass that inherits from <path>")
    p.add_argument("path", help="Parent class path")
    p.add_argument("dest", nargs="?", default=None, help="Destination folder (optional)")
    p.add_argument("name", nargs="?", default=None, help="New class name (optional)")

    # duplicate
    p = sub.add_parser("duplicate", help="Copy <path> and cut inheritance")
    p.add_argument("path", help="Source class path")
    p.add_argument("dest", nargs="?", default=None, help="Destination folder (optional)")
    p.add_argument("name", nargs="?", default=None, help="New class name (optional)")

    # rename
    p = sub.add_parser("rename", help="Rename a class via setName")
    p.add_argument("path", help="Class path")
    p.add_argument("new_name", help="New name")

    # delete
    p = sub.add_parser("delete", help="Delete a class via deleteObject")
    p.add_argument("path", help="Class path")

    # move
    p = sub.add_parser("move", help="Move a class to another folder")
    p.add_argument("path", help="Class path")
    p.add_argument("folder", help="Destination folder path")

    # add-attr
    p = sub.add_parser("add-attr", help="Add a user-defined attribute to a class")
    p.add_argument("path", help="Class path")
    p.add_argument("name", help="Attribute name")
    p.add_argument("atype", help="Plant Simulation type name (integer, string, boolean, real, ...)")

    # del-attr
    p = sub.add_parser("del-attr", help="Delete a user-defined attribute")
    p.add_argument("path", help="Class path")
    p.add_argument("name", help="Attribute name")

    # set-attr
    p = sub.add_parser("set-attr", help="Set a user-defined attribute's InitValue")
    p.add_argument("path", help="Class path")
    p.add_argument("name", help="Attribute name")
    p.add_argument("value", help="Value (integer / real / boolean / string — heuristic)")

    # inherit-attr
    p = sub.add_parser("inherit-attr", help="Restore inheritance on a UDA's InitValue")
    p.add_argument("path", help="Class path")
    p.add_argument("name", help="Attribute name")

    args = ap.parse_args()
    result = run_op(args)
    # Always emit a single JSON envelope on stdout (one line — easier to consume)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    # Exit code mirrors ok
    sys.exit(0 if result.get("ok") else 1)


if __name__ == "__main__":
    main()