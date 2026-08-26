#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
add_note.py — Insert comment lines into a Method object's `program` attribute
on a running Plant Simulation server.

Modes:
  prepend  — add comment block before the existing code (preserve original)
  append   — add comment block after the existing code (preserve original)
  replace  — overwrite the entire program (requires explicit --confirm)
  trailing — append a trailing `-- ...` comment to the last line

Quirks enforced:
  Q1   Use chr(10) for real newlines, not "\n" (SimTalk does NOT interpret escapes)
  Q2   Always backup the current program before writing
  Q3   Verify internalclasstype == "Method" before touching `program`
  Q4   Read back obj.program after every write
  Q5   obj.execute after the write to confirm the new source still runs

Usage:
  # Prepend a header block
  python3 scripts/add_note.py --path .CTU.Frame.Program --mode prepend \\
      --note "-- line 1" "-- line 2" "-- line 3"

  # Append a footer / TODO
  python3 scripts/add_note.py --path .Models.Model.init --mode append \\
      --note "-- TODO: refactor in v2"

  # Add a trailing comment to the last line
  python3 scripts/add_note.py --path .CTU.Frame.Program --mode trailing \\
      --note "  -- local counter, starting at 1"

  # Replace (requires --confirm; otherwise refuses)
  python3 scripts/add_note.py --path .CTU.Frame.Program --mode replace \\
      --note "-- full new body" "var i := 1" --confirm

  # Restore from a backup file
  python3 scripts/add_note.py --path .CTU.Frame.Program \\
      --backup log/ctu_frame_program_original.txt
"""

import argparse
import os
import subprocess
import sys


# ---------------------------------------------------------------------------
# Path / config
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)

# Default transport — local-simtalk-execution's high-level sender.
SIMTALK_SEND = os.path.normpath(
    os.path.join(SKILL_DIR, "..", "local-simtalk-execution", "scripts", "simtalk_send.py")
)


# ---------------------------------------------------------------------------
# SimTalk helpers (use chr(10) — never "\n")
# ---------------------------------------------------------------------------

def quote(s):
    """Wrap a Python string as a SimTalk double-quoted literal.
    Escapes only the backslash and double-quote (sufficient for ASCII
    comment text)."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build_simtalk(payload):
    """Compose a multi-line SimTalk snippet from (line1, line2, ...) using
    chr(10) as the line separator. Returns a single string that can be
    passed as the `code` positional to `simtalk_send.py run`."""
    return ("\n".join(payload))  # the *Python* newline — the actual payload
                                # for simtalk_send.py is one argument; newlines
                                # inside the *string* are still chr(10) for
                                # SimTalk once it arrives.


def run(code, return_value=False, timeout=30):
    """Send `code` to the running server via simtalk_send.py run.
    Returns (exit_code, stdout_str)."""
    cmd = [
        sys.executable, SIMTALK_SEND, "run",
    ]
    if return_value:
        cmd.append("--return-value")
    cmd.append(code)
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def readlog():
    """Pull the latest GUI Console log entries. v15+ degraded — best-effort."""
    proc = subprocess.run(
        [sys.executable, SIMTALK_SEND, "readlog"],
        capture_output=True, text=True, timeout=30,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


# ---------------------------------------------------------------------------
# Mode handlers
# ---------------------------------------------------------------------------

def compose_program(mode, before, note_lines):
    """Compose the new program string in SimTalk source form using chr(10).
    Returns a SimTalk expression that evaluates to the new string.
    """
    parts = []
    if mode == "prepend":
        for line in note_lines:
            parts.append(quote(line))
        parts.append(quote(before))
    elif mode == "append":
        parts.append(quote(before))
        for line in note_lines:
            parts.append(quote(line))
    elif mode == "trailing":
        # Append the trailing comment to the LAST line of `before`.
        last_nl = before.rfind(chr(10))
        head = before[: last_nl + 1] if last_nl >= 0 else ""
        last_line = before[last_nl + 1:] if last_nl >= 0 else before
        # `note_lines` is expected to be a single element starting with
        # whitespace + `-- ...`. Concatenate with the last line.
        trailing = (note_lines[0] if note_lines else "")
        new_last = last_line + trailing
        parts.append(quote(head + new_last))
    elif mode == "replace":
        for line in note_lines:
            parts.append(quote(line))
    else:
        raise ValueError("unknown mode: " + mode)

    return " + chr(10) + ".join(parts)


def path_to_backup_name(path):
    """Sanitize a Plant Simulation path for use as a filename."""
    return path.strip(".").replace(".", "_").replace("/", "_") + "_program_original.txt"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Insert comment lines into a Method's `program` attribute.",
    )
    ap.add_argument("--path", required=True,
                    help="Path to the Method object, e.g. .CTU.Frame.Program")
    ap.add_argument("--mode", choices=["prepend", "append", "replace", "trailing"],
                    default="prepend")
    ap.add_argument("--note", nargs="+",
                    help="Comment lines to insert (each as one --note arg, "
                         "or space-separated after the flag)")
    ap.add_argument("--backup", default=None,
                    help="Path to a backup file. Used by --restore. "
                         "Defaults to log/<sanitized-path>_program_original.txt")
    ap.add_argument("--confirm", action="store_true",
                    help="Required for --mode replace (otherwise refuses)")
    ap.add_argument("--restore", action="store_true",
                    help="Restore `program` from --backup instead of editing")
    ap.add_argument("--no-verify-execute", action="store_true",
                    help="Skip the final obj.execute verification step")
    args = ap.parse_args()

    # Safety guard for replace
    if args.mode == "replace" and not args.confirm:
        print("ERROR: --mode replace requires --confirm (it overwrites the "
              "entire program).", file=sys.stderr)
        sys.exit(2)

    # Resolve default backup path
    if args.backup is None:
        log_dir = os.path.join(SKILL_DIR, "log")
        os.makedirs(log_dir, exist_ok=True)
        args.backup = os.path.join(log_dir, path_to_backup_name(args.path))

    # ------------------------------------------------------------------
    # RESTORE branch
    # ------------------------------------------------------------------
    if args.restore:
        with open(args.backup, "r", encoding="utf-8") as f:
            original = f.read()
        code = (
            'var obj: object; obj := str_to_obj("' + args.path + '"); '
            'obj.program := ' + quote(original) + '; '
            'print "###RESTORE_OK###";'
        )
        rc, out = run(code)
        print("[restore] " + out.strip())
        sys.exit(0 if rc == 0 else 1)

    # ------------------------------------------------------------------
    # EDIT branch
    # ------------------------------------------------------------------
    if not args.note:
        print("ERROR: --note is required for prepend/append/replace/trailing "
              "(unless --restore).", file=sys.stderr)
        sys.exit(2)

    # 1) Resolve + type-check
    typecheck_code = (
        'var obj: object; obj := str_to_obj("' + args.path + '"); '
        'print "###MARKER###"; '
        'if obj = void then '
        '  print "void"; '
        'else '
        '  print to_str(obj.internalclasstype); '
        'end; '
        'print "###END###"'
    )
    rc, out = run(typecheck_code)
    if rc != 0:
        print("[typecheck] FAILED: " + out, file=sys.stderr)
        sys.exit(11)
    rc2, log2 = readlog()
    log_text = log2 if rc2 == 0 else out
    if "Method" not in log_text:
        print("[typecheck] Object is not a Method (or readlog degraded). "
              "Path: " + args.path, file=sys.stderr)
        print(log_text)
        sys.exit(11)

    # 2) Read current program
    read_code = (
        'var obj: object; obj := str_to_obj("' + args.path + '"); '
        'print "###PROG_START###"; '
        'print obj.program; '
        'print "###PROG_END###"'
    )
    rc, out = run(read_code)
    if rc != 0:
        print("[read] FAILED: " + out, file=sys.stderr)
        sys.exit(11)
    rc2, log2 = readlog()
    log_text = log2 if rc2 == 0 else out
    before = extract_between(log_text, "###PROG_START###", "###PROG_END###")
    if before is None:
        print("[read] could not extract current program. readlog:", file=sys.stderr)
        print(log_text)
        sys.exit(11)
    print("[read] current program (" + str(len(before)) + " bytes):")
    print("    " + before.replace(chr(10), chr(10) + "    "))

    # 3) Backup
    with open(args.backup, "w", encoding="utf-8") as f:
        f.write(before)
    print("[backup] saved to " + args.backup)

    # 4) Compose + write
    rhs = compose_program(args.mode, before, args.note)
    write_code = (
        'var obj: object; obj := str_to_obj("' + args.path + '"); '
        'obj.program := ' + rhs + '; '
        'print "###WRITE_OK###"'
    )
    rc, out = run(write_code)
    if rc != 0:
        print("[write] FAILED: " + out, file=sys.stderr)
        sys.exit(11)
    print("[write] sent. " + out.strip())

    # 5) Readback
    rc2, log2 = readlog()
    rb_code = (
        'var obj: object; obj := str_to_obj("' + args.path + '"); '
        'print "###RB_START###"; print obj.program; print "###RB_END###"'
    )
    rc, out = run(rb_code)
    rc2, log2 = readlog()
    log_text = log2 if rc2 == 0 else out
    after = extract_between(log_text, "###RB_START###", "###RB_END###")
    if after is None:
        print("[readback] could not extract new program. readlog:", file=sys.stderr)
        print(log_text)
        sys.exit(11)
    print("[readback] new program (" + str(len(after)) + " bytes):")
    print("    " + after.replace(chr(10), chr(10) + "    "))

    # 6) Execute to verify it still runs
    if not args.no_verify_execute:
        exec_code = (
            'var obj: object; obj := str_to_obj("' + args.path + '"); '
            'obj.execute; print "###EXEC_OK###"'
        )
        rc, out = run(exec_code)
        rc2, log2 = readlog()
        log_text = log2 if rc2 == 0 else out
        if "###EXEC_OK###" in log_text:
            print("[verify] method executes OK after edit")
        else:
            print("[verify] WARNING — execute marker not found. readlog:", file=sys.stderr)
            print(log_text)

    print("[done] mode=" + args.mode + " path=" + args.path
          + " backup=" + args.backup)


def extract_between(text, start_marker, end_marker):
    """Extract substring between the LAST occurrence of start_marker and
    end_marker. readlog output is line-prefixed with timestamps, so we
    strip the prefix first."""
    lines = text.splitlines()
    cleaned = []
    for line in lines:
        # Strip "YYYY-MM-DD HH:MM:SS: " timestamp prefix
        if len(line) >= 21 and line[4] == "-" and line[10] == " ":
            cleaned.append(line[21:])
        elif len(line) >= 11 and line[2] == ":" and line[5] == ":":
            cleaned.append(line[11:])
        else:
            cleaned.append(line)
    body = "\n".join(cleaned)
    si = body.rfind(start_marker)
    ei = body.rfind(end_marker)
    if si < 0 or ei < 0 or ei <= si:
        return None
    return body[si + len(start_marker) : ei].lstrip("\n").rstrip("\n")


if __name__ == "__main__":
    main()