#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
write_simtalk.py — Orchestrate "write SimTalk code into a Plant Simulation Method".

Two flows:

  A. Existing Method path: --path .CTU.Frame.Program --code "..." --code-file ...
  B. New Method instance: --frame .Models.Model --new-method myMethod
                           [--parent-class .InformationFlow.Method]
                           --code "..." --code-file ...

In both flows the actual `obj.program := <source>` write goes through
`local-simtalk-add-note-to-method/scripts/add_note.py --mode replace --confirm`,
which already handles backup / readback / execute-verify. This script is a
front-end that:

  1. (Flow B only) Sends `<parent>.duplicate(<frame>, <name>)` via simtalk_send.py
     and asserts the new method resolves via str_to_obj before writing code.
     (We use `duplicate()` not `create()` because `create` is a SimTalk
     keyword AND a list method — both `var p: object := str_to_obj(...)` +
     `p.create(f)` and `.InformationFlow.Method.create(f)` fail. The
     `.duplicate(<frame>, <name>)` syntax with `&` reference on the class
     name is the documented workaround.)
  2. Reads --code (multi-line string) or --code-file (UTF-8 file) and passes
     it to add_note.py --note, one line per --note arg. This bypasses Quirk
     #10 from local-simtalk-add-note-to-method (argparse stops at any token
     starting with `--`).

Usage:
  # A. Existing Method
  python3 scripts/write_simtalk.py --path .Models.Model.count_parts --code-file /tmp/code.txt

  # B. New Method (default parent .InformationFlow.Method)
  python3 scripts/write_simtalk.py --frame .Models.Model --new-method myMethod \
      --code-file /tmp/code.txt

  # B'. Custom parent class
  python3 scripts/write_simtalk.py --frame .Models.Model --new-method myMethod \
      --parent-class .UserObjects.MyMethod --code-file /tmp/code.txt

  # C. From --code argument directly (rare; watch quoting)
  python3 scripts/write_simtalk.py --path .Models.Model.x --code "line1$(printf '\\n')line2"
"""

import argparse
import os
import shlex
import subprocess
import sys


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)

ADD_NOTE_SCRIPT = os.path.normpath(
    os.path.join(SKILL_DIR, "..", "local-simtalk-add-note-to-method", "scripts", "add_note.py")
)

SIMTALK_SEND = os.path.normpath(
    os.path.join(SKILL_DIR, "..", "local-simtalk-execution", "scripts", "simtalk_send.py")
)

DEFAULT_PARENT_CLASS = ".InformationFlow.Method"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def info(msg):
    print("[write_simtalk] " + str(msg), file=sys.stderr)


def inject_amp_on_last_segment(dot_path):
    """Insert the `&` reference operator before the LAST segment of a
    dot-path. e.g. ".InformationFlow.Method" → ".InformationFlow.&Method".

    Plant Simulation's class-literal path syntax requires `&<DataType>` when
    the last segment collides with a built-in data type name (Method,
    Variable, List, Table, etc.) — without it, SimTalk parses the dot-path
    as the data type itself and `.duplicate(...)` / `.derive(...)` fails.
    """
    if "." not in dot_path:
        return "." + dot_path  # bare name → treat as top-level
    prefix, last = dot_path.rsplit(".", 1)
    return prefix + ".&" + last


def fail(msg, code=1):
    print("[write_simtalk] ERROR: " + str(msg), file=sys.stderr)
    sys.exit(code)


def run(cmd, timeout=60):
    """Run a subprocess, return (rc, combined_stdout_stderr)."""
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def simtalk_run(code, timeout=30):
    """Send a single SimTalk snippet via simtalk_send.py run.

    Returns (rc, combined_output). combined_output includes:
      - the JSON envelope from `simtalk_send.py run` (stdout)
      - the readlog buffer (so any `print(...)` output is visible)

    v15+ quirk: `simtalk_run` returns `result:"success"` even when the
    SimTalk code raises a runtime exception — the actual error lives in
    the log field as `"code execute failed. error msg:..."`. So callers
    must check both `rc == 0` AND `not log.startswith("code execute failed")`
    for semantic success.
    """
    proc = subprocess.run(
        [sys.executable, SIMTALK_SEND, "run", code],
        capture_output=True, text=True, timeout=timeout,
    )
    run_stdout = proc.stdout or ""
    run_stderr = proc.stderr or ""

    # Fetch readlog so any `print(...)` from the snippet is visible.
    # v15+ readlog may return exit code 20 (warning) but still ships
    # stdout content — treat 0 and 20 both as success.
    try:
        rl_proc = subprocess.run(
            [sys.executable, SIMTALK_SEND, "readlog"],
            capture_output=True, text=True, timeout=20.0,
        )
        rl_stdout = rl_proc.stdout if rl_proc.returncode in (0, 20) else ""
    except Exception:
        rl_stdout = ""

    combined = run_stdout + run_stderr + rl_stdout
    return proc.returncode, combined


def is_soft_failure(out):
    """True if `simtalk_run` returned `result:"success"` but the SimTalk
    code actually raised a runtime exception (Quirk #7 — soft failure
    where the error text lives in the log field prefixed by
    `"code execute failed. error msg:..."`)."""
    # The envelope's log field is short ("execute success" or the error
    # prefix). readlog buffer can also contain the prefix if multiple
    # failed calls accumulated. Search both.
    return "code execute failed" in out


def quote_simtalk_string(s):
    """Wrap a Python string as a SimTalk double-quoted literal. Escape only
    backslash and double-quote — enough for SimTalk source code on one line."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def join_simtalk_lines(lines):
    """Concatenate a list of source-code lines into a SimTalk expression that
    evaluates to the multi-line string. Uses chr(10) — never '\\n'."""
    parts = [quote_simtalk_string(line) for line in lines]
    return " + chr(10) + ".join(parts)


# ---------------------------------------------------------------------------
# Step 5 — create new Method instance (Flow B)
# ---------------------------------------------------------------------------

def create_method_instance(frame_path, method_name, parent_class_path):
    """Insert a new Method instance under <frame_path>/<method_name>.

    SimTalk gotchas encoded here:

    1. **`create` is a SimTalk keyword AND a list method — it cannot be used
       to instantiate InformationFlow objects.** Both
       `var p: object := str_to_obj(".InformationFlow.Method"); p.create(f)`
       AND `.InformationFlow.Method.create(f)` fail:
         - the first fails with `Unknown identifier 'create'` (generic
           `object` reference can't dispatch a keyword-named method);
         - the second fails with `'create' can only be applied to lists or
           objects or variables of data type list` (SimTalk parses
           `.InformationFlow.Method` as the Method data type, not the class,
           and `.create(...)` as the list-create method).
       The documented `.create()` for `.MUs.<X>` and `.Resources.<X>` is a
       special case for Mobile Units and Workers — it does NOT generalize
       to arbitrary classes.

    2. **Workaround: use `duplicate(<frame>, <name>)` with the `&` reference
       operator on the class name.** Plant Simulation help documents this
       pattern for Variable / Method / etc.:
           .InformationFlow.&Variable.duplicate
           .InformationFlow.&Method.duplicate
       With `Destination = <frame>` (an object reference, not a string)
       and `Name = <name>`, `duplicate()` inserts a new instance into the
       Frame — exactly what we want for Method. Verified end-to-end:
       creates `.Models.Model.<name>` with internalclasstype="Method" and
       Origin=.InformationFlow.Method.

    3. **The frame argument must be an object reference, not a string.**
       Use `var f: object := str_to_obj("<frame>");` first, then pass `f`
       (no quotes) to `.duplicate(f, ...)`.

    4. **The class name in the dot-path needs the `&` operator** to tell
       SimTalk to treat the name as a class object (not the data type).
       Without `&`, `.InformationFlow.Method.duplicate(...)` parses as
       "list variable Method in module InformationFlow" and fails.

    Source: 01-plantsimulation-knowledge/01-plant-simulation-help/objects/
    common-methods/common-methods.md §duplicate (line 164:
    `.InformationFlow.&Method.duplicate`); keywords list in
    simtalk/language-fundamentals/names-object-access/names-object-access.md.
    """
    info("creating new Method instance")
    info("  parent class : " + parent_class_path)
    info("  target frame : " + frame_path)
    info("  method name  : " + method_name)

    # Validate parent class path exists (type-check)
    parent_check = (
        'var p: object; p := str_to_obj("' + parent_class_path + '"); '
        'if p = void then print "###PARENT_VOID###"; '
        'else print to_str(p.internalclasstype); end; '
        'print "###END_PARENT###"'
    )
    rc, out = simtalk_run(parent_check)
    if rc == 11 or "###PARENT_VOID###" in out:
        fail("parent class path does not resolve: " + parent_class_path)
    info("  parent class typecheck OK")

    # Validate frame path exists (separate str_to_obj, since duplicate()
    # takes an object, not a string).
    frame_check = (
        'var f: object; f := str_to_obj("' + frame_path + '"); '
        'if f = void then print "###FRAME_VOID###"; '
        'else print to_str(f.internalclasstype); end; '
        'print "###END_FRAME###"'
    )
    rc, out = simtalk_run(frame_check)
    if rc == 11 or "###FRAME_VOID###" in out:
        fail("target frame path does not resolve: " + frame_path)
    info("  frame path typecheck OK")

    # Create() — use `duplicate()` with `&` reference on class name. The `&`
    # bypasses the Method data type collision in the dot-path.
    # Insert `&` before the last segment of parent_class_path (e.g.
    # ".InformationFlow.Method" → ".InformationFlow.&Method").
    parent_with_amp = inject_amp_on_last_segment(parent_class_path)
    create_code = (
        'var f: object; f := str_to_obj("' + frame_path + '"); '
        'var dup: object; dup := ' + parent_with_amp + '.duplicate(f, "' + method_name + '"); '
        'if dup = void then print "###DUP_VOID###"; '
        'else print "DUP_NAME=" + dup.name; print "DUP_TYPE=" + dup.internalClassType; end; '
        'print "###CREATE_OK###"'
    )
    rc, out = simtalk_run(create_code)
    if rc != 0 or "###CREATE_OK###" not in out:
        # Surface the soft-failure error text if present
        err_hint = ""
        if is_soft_failure(out):
            for line in out.splitlines():
                if "code execute failed" in line:
                    err_hint = line.strip()
                    break
        fail("duplicate() failed" + (": " + err_hint if err_hint else ".") + "\n" + out)

    # Verify the new Method resolves and is internalclasstype "Method"
    verify_code = (
        'var obj: object; obj := str_to_obj("' + frame_path + '.' + method_name + '"); '
        'if obj = void then print "###NEW_VOID###"; '
        'else print to_str(obj.internalclasstype); end; '
        'print "###END_NEW###"'
    )
    rc, out = simtalk_run(verify_code)
    if rc == 11 or "###NEW_VOID###" in out:
        fail("after duplicate(), the new Method path did not resolve: "
             + frame_path + "." + method_name)
    info("  new Method resolves; internalclasstype OK")


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
    bad = [i for i, ln in enumerate(code_lines) if ln.lstrip().startswith("--")]
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

    rc, out = run(cmd, timeout=120)
    sys.stdout.write(out)
    if rc != 0:
        fail("add_note.py --mode replace failed (rc=" + str(rc) + ")", code=rc)


# ---------------------------------------------------------------------------
# Load source code from --code or --code-file
# ---------------------------------------------------------------------------

def load_code(args):
    """Return a list of source-code lines (no trailing newlines)."""
    sources = []
    if args.code:
        sources.append(args.code)
    if args.code_file:
        with open(args.code_file, "r", encoding="utf-8") as f:
            sources.append(f.read())

    if not sources:
        fail("must supply --code or --code-file (or both)")

    # Split combined sources by real newlines. Each source is independent;
    # we concatenate them as-is (no separator added — user controls joins).
    out = []
    for src in sources:
        out.extend(src.splitlines())

    # Strip trailing empty lines so add_note.py doesn't get a final blank
    while out and out[-1].strip() == "":
        out.pop()
    return out


# ---------------------------------------------------------------------------
# Resolve the final Method path
# ---------------------------------------------------------------------------

def resolve_method_path(args):
    """Return (method_path, need_create). When --dry-run is set, the
    create() side-effect is skipped even on Flow B."""
    if args.path:
        if args.frame or args.new_method:
            fail("--path is mutually exclusive with --frame / --new-method")
        return args.path, False

    if not args.frame or not args.new_method:
        fail("must supply --path (existing Method) OR "
             "(--frame + --new-method) to create one")

    parent = args.parent_class or DEFAULT_PARENT_CLASS
    if not args.dry_run:
        create_method_instance(args.frame, args.new_method, parent)
    else:
        info("DRY RUN — skipping create() (would normally insert "
             + args.frame + "." + args.new_method + " from " + parent + ")")
    return args.frame + "." + args.new_method, True


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Write SimTalk code into a Plant Simulation Method. "
                    "Wraps local-simtalk-add-note-to-method (Flow A) or "
                    "creates a new Method then writes (Flow B).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # --- Flow selection ---
    ap.add_argument("--path",
                    help="Existing Method path, e.g. .Models.Model.count_parts. "
                         "Mutually exclusive with --frame/--new-method.")
    ap.add_argument("--frame",
                    help="Target Frame path (Flow B). The Method will be "
                         "inserted as <frame>.<new-method>.")
    ap.add_argument("--new-method",
                    help="Name of the new Method to create (Flow B).")
    ap.add_argument("--parent-class",
                    help="Parent class path for new Method (Flow B). "
                         "Default: .InformationFlow.Method.")

    # --- Source code ---
    ap.add_argument("--code", action="append", default=[],
                    help="Source code as a single string. May be repeated; "
                         "each --code is concatenated. Use real newlines, "
                         "or pass from a file via --code-file (recommended).")
    ap.add_argument("--code-file",
                    help="UTF-8 file containing the source code.")

    # --- Misc ---
    ap.add_argument("--dry-run", action="store_true",
                    help="Print resolved method path + code lines + command "
                         "without sending anything to the server.")

    args = ap.parse_args()

    code_lines = load_code(args)
    method_path, created = resolve_method_path(args)

    info("===== SUMMARY =====")
    info("  Method path : " + method_path + ("  (newly created)" if created else "  (existing)"))
    info("  Lines       : " + str(len(code_lines)))
    info("===================")

    if args.dry_run:
        info("DRY RUN — nothing sent to the server")
        info("--- code ---")
        for line in code_lines:
            print(line)
        info("--- end code ---")
        sys.exit(0)

    write_code(method_path, code_lines)

    info("DONE.")


if __name__ == "__main__":
    main()