#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
write_simtalk.py — Write SimTalk source code into an existing Plant
Simulation Method.

This skill ONLY writes code into a Method that already exists at the given
path. It does NOT create the Method — that is the job of the sibling skill
`local-simtalk-create-method-object`. If you call this script without
`--path` (or with a path that doesn't resolve to an existing Method),
it exits with an error pointing you at that skill.

The actual `obj.program := <source>` write goes through
`local-simtalk-add-note-to-method/scripts/add_note.py --mode replace --confirm`,
which handles backup / readback / execute-verify. This script is a front-end
that:

  1. Reads --code (multi-line string) or --code-file (UTF-8 file) and
     passes it to add_note.py --note, one line per --note arg. This
     bypasses Quirk #10 from local-simtalk-add-note-to-method (argparse
     stops at any token starting with `--`).

Usage:
  python3 scripts/write_simtalk.py \
      --path .Models.Model.count_parts \
      --code-file /tmp/code.txt

  # From --code argument directly (rare; watch quoting)
  python3 scripts/write_simtalk.py \
      --path .Models.Model.x \
      --code "line1
  line2"

  # Dry-run (no server contact)
  python3 scripts/write_simtalk.py \
      --path .Models.Model.count_parts \
      --code-file /tmp/code.txt \
      --dry-run
"""

import argparse
import os
import subprocess
import sys


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)

ADD_NOTE_SCRIPT = os.path.normpath(
    os.path.join(SKILL_DIR, "..", "local-simtalk-add-note-to-method",
                 "scripts", "add_note.py")
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def info(msg):
    print("[write_simtalk] " + str(msg), file=sys.stderr)


def fail(msg, code=1):
    print("[write_simtalk] ERROR: " + str(msg), file=sys.stderr)
    sys.exit(code)


def run(cmd, timeout=120):
    """Run a subprocess, return (rc, combined_stdout_stderr)."""
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


# ---------------------------------------------------------------------------
# Step 7 — write source code via add_note.py --mode replace --confirm
# ---------------------------------------------------------------------------

def write_code(method_path, code_lines):
    """Invoke add_note.py with --mode replace --confirm.

    IMPORTANT — argparse bug: add_note.py defines `--note` as `nargs="+"`
    WITHOUT `action="append"`. With repeated `--note` flags (one per line),
    argparse REPLACES the value each time and only the LAST line survives.
    Confirmed empirically: `--note A --note B --note C --note D` →
    args.note == ['D'].

    Fix: pass ALL lines as the values of a SINGLE `--note` flag
    (`--note L1 L2 L3 ...`). argparse consumes everything until the next
    flag, so all lines end up in args.note.

    Quirk #10 caveat: if any line starts with `--`, argparse will stop at
    it and treat the rest as new flags. We warn (not abort) so the user
    can fix and retry — for SimTalk source, lines starting with `--` are
    comments which the user can rewrite as `// ...` if needed.
    """
    if not code_lines:
        fail("--code / --code-file produced zero lines")

    info("writing " + str(len(code_lines)) + " lines to " + method_path)

    # Quirk #10 warning — surface before sending so the user can fix
    bad = [i for i, ln in enumerate(code_lines)
           if ln.lstrip().startswith("--")]
    if bad:
        info("WARNING: " + str(len(bad)) + " line(s) start with '--' (Quirk #10). "
             "argparse will stop consuming --note values at the first '--' "
             "token, so those lines (and any after them) will be DROPPED.")
        for i in bad:
            info("  line " + str(i + 1) + ": " + repr(code_lines[i]))

    cmd = [
        sys.executable, ADD_NOTE_SCRIPT,
        "--path", method_path,
        "--mode", "replace",
        "--confirm",
        "--note",
    ]
    # Single --note flag, all lines as positional values for nargs="+".
    cmd.extend(code_lines)

    rc, out = run(cmd)
    sys.stdout.write(out)
    if rc != 0:
        fail("add_note.py --mode replace failed (rc=" + str(rc) + ")",
             code=rc)


# ---------------------------------------------------------------------------
# Load source code from --code or --code-file
# ---------------------------------------------------------------------------

def load_code(args):
    """Return a list of source-code lines (no trailing newlines)."""
    sources = []
    if args.code:
        sources.append(args.code)
    if args.code_file:
        with open(args.code_file, "r", encoding="utf-8") as fh:
            sources.append(fh.read())

    if not sources:
        fail("must supply --code or --code-file (or both)")

    out = []
    for src in sources:
        out.extend(src.splitlines())

    # Strip trailing empty lines so add_note.py doesn't get a final blank
    while out and out[-1].strip() == "":
        out.pop()
    return out


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Write SimTalk source code into an EXISTING Plant "
                    "Simulation Method. Does NOT create the Method — "
                    "use `local-simtalk-create-method-object` first if "
                    "the target Method doesn't exist yet.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # --- Required: target Method path ---
    ap.add_argument("--path", required=True,
                    help="Path of an EXISTING Method to write into, e.g. "
                         ".Models.Model.count_parts. If the Method does "
                         "not exist, run `local-simtalk-create-method-object` "
                         "first to create an empty container.")

    # --- Source code ---
    ap.add_argument("--code", action="append", default=[],
                    help="Source code as a single string. May be repeated; "
                         "each --code is concatenated. Use real newlines, "
                         "or pass from a file via --code-file (recommended).")
    ap.add_argument("--code-file",
                    help="UTF-8 file containing the source code.")

    # --- Misc ---
    ap.add_argument("--dry-run", action="store_true",
                    help="Print resolved method path + code lines without "
                         "sending anything to the server.")

    args = ap.parse_args()

    code_lines = load_code(args)

    info("===== SUMMARY =====")
    info("  Method path : " + args.path + "  (existing)")
    info("  Lines       : " + str(len(code_lines)))
    info("===================")

    if args.dry_run:
        info("DRY RUN — nothing sent to the server")
        info("--- code ---")
        for line in code_lines:
            print(line)
        info("--- end code ---")
        sys.exit(0)

    write_code(args.path, code_lines)

    info("DONE.")


if __name__ == "__main__":
    main()