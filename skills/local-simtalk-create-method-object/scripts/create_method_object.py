#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
create_method_object.py — Insert a new Method instance under a Frame.

This is the standalone Method-creation skill. `local-simtalk-write-simtalk`
delegates to this skill when the user hasn't specified a target Method.

Plant Simulation gotchas encoded here:

  1. **`create` is a SimTalk keyword AND a list method** — it cannot be used
     to instantiate InformationFlow objects. Three seemingly-reasonable
     `create()` patterns all fail (see session-20260826.md in
     local-simtalk-write-simtalk/log). The only reliable Method-creation
     path is `.InformationFlow.&Method.duplicate(<frame>, <name>)`, which
     `local-simtalk-class-management/scripts/class_ops.py duplicate`
     already wraps correctly using `srcObj.duplicate(...)` (object ref,
     no `&` collision needed). We delegate to that.

  2. **`duplicate(<frame>, <name>)`'s frame parameter must be an object
     reference**, not a string. `class_ops.py` handles this by wrapping
     the frame path with `str_to_obj(...)`.

  3. **Method name must not collide with a SimTalk reserved word**. The
     lexer treats `method`, `variable`, `list`, `table`, etc. as data-type
     keywords — creating a Method with that name fails with
     "Invalid identifier or identifier already exists in the name scope".
     See `references/simtalk-reserved-words.md` for the full blocklist.

  4. **Name collision** under the target frame silently produces a
     `duplicate_returned_void` error from Plant Simulation. We pre-check
     via `class_ops.py inspect` of the candidate new path so the failure
     surfaces a clean error message instead of a runtime exception.

Usage:
  python3 scripts/create_method_object.py \
      --frame .Models.Model \
      --method-name myMethod

  # Custom parent class (e.g. user-defined Method subclass):
  python3 scripts/create_method_object.py \
      --frame .Models.Model \
      --method-name log_warn \
      --parent-class .UserObjects.LoggingMethod

  # No server call — only validate inputs:
  python3 scripts/create_method_object.py \
      --frame .Models.Model \
      --method-name myMethod \
      --dry-run

Output (JSON envelope on stdout):

  {
    "ok": true,
    "method_path": ".Models.Model.myMethod",
    "frame_path": ".Models.Model",
    "method_name": "myMethod",
    "parent_class": ".InformationFlow.Method",
    "internal_class_type": "Method"
  }

On failure `ok` is `false` and `error` carries the reason
(e.g. `"name is a SimTalk reserved word"`,
`"frame path does not resolve"`,
`"parent class is not a Method (got Station)"`,
`"name already exists"`,
`"duplicate() returned void"`).
"""
import argparse
import json
import os
import subprocess
import sys


# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)

# Sibling skill — we delegate the actual `duplicate()` call to it.
CLASS_OPS = os.path.normpath(
    os.path.join(SKILL_DIR, "..", "local-simtalk-class-management",
                 "scripts", "class_ops.py")
)

DEFAULT_PARENT_CLASS = ".InformationFlow.Method"

# SimTalk reserved words that conflict with creating a Method instance.
# Lower-case form is what Plant Simulation's lexer rejects; we compare
# case-insensitively so `Method` / `METHOD` are also blocked.
#
# Sources:
#   - session-20260826.md (write_simtalk/log) — `method` data-type collision
#   - 01-plantsimulation-knowledge/01-plant-simulation-help/programming-a-method/
#   - common-methods.md (Method / Variable / Table / List built-in classes)
SIMTALK_RESERVED_WORDS = frozenset({
    # Plant Simulation built-in data types (these collide with creating
    # a class instance of the same name — see Quirk #15).
    "method", "variable", "table", "list", "string", "integer",
    "boolean", "real", "length", "time", "speed", "acceleration",
    "weight", "currency", "object", "any", "date", "timewindow",
    # Built-in module roots (would create ambiguous dot-paths)
    "informationflow", "materialflow", "workerpool", "resources",
    "musrcc", "connectors", "drain", "eventcontroller", "infobox",
    # Other Plant Simulation reserved / special forms
    "result", "self", "current", "currentuser",
    # SimTalk control keywords (would never be valid identifiers anyway,
    # but block them defensively)
    "if", "then", "else", "end", "for", "next", "while", "loop",
    "return", "do", "call", "var", "param", "print", "true", "false",
    "void", "and", "or", "not", "mod",
    # Class operation keywords that double as identifiers
    "create", "derive", "duplicate", "delete", "move", "rename",
})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def info(msg):
    print("[create_method_object] " + str(msg), file=sys.stderr)


def fail(msg, code=1):
    print("[create_method_object] ERROR: " + str(msg), file=sys.stderr)
    sys.exit(code)


def emit_envelope(envelope):
    """Print the JSON envelope on stdout (machine-readable contract)."""
    print(json.dumps(envelope, ensure_ascii=False))


def is_reserved(name):
    return name.lower() in SIMTALK_RESERVED_WORDS


def is_valid_identifier(name):
    """Plant Simulation identifiers: ASCII letter or `_` followed by
    letters / digits / `_`. We accept the conventional PascalCase /
    snake_case forms and disallow leading digits, hyphens, dots, and
    non-ASCII (Plant Simulation identifiers are ASCII-only even though
    the GUI may display translated labels)."""
    if not name:
        return False
    if not (name[0].isalpha() or name[0] == "_"):
        return False
    for ch in name:
        if not (ch.isalnum() or ch == "_"):
            return False
    return True


def run_class_ops(subcommand, *args, timeout=60):
    """Run `class_ops.py <subcommand> <args>`, return parsed envelope or None.

    class_ops.py exits 1 when `ok:false` is in the envelope (e.g. inspect
    on a non-existent path returns `ok:false` with `error: "path does not
    resolve"`). We still parse and return the envelope in that case —
    callers should branch on `envelope.get("ok")` rather than treating
    None as failure.
    """
    cmd = [sys.executable, CLASS_OPS, subcommand] + list(args)
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        fail(f"class_ops.py not found at {CLASS_OPS}", code=2)
    out = (proc.stdout or "").strip()
    try:
        env = json.loads(out) if out else None
    except json.JSONDecodeError:
        info(f"class_ops.py {subcommand} returned non-JSON: {out[:200]}")
        return None
    if env is None and proc.returncode != 0:
        info(f"class_ops.py {subcommand} rc={proc.returncode} "
             f"stderr={(proc.stderr or '').strip()[:300]}")
    return env


# ---------------------------------------------------------------------------
# Validation steps
# ---------------------------------------------------------------------------

def _ict(env):
    """Read the InternalClassType from a class_ops.py inspect envelope.

    class_ops.py puts the parsed marker data under the `data` key (not at
    the envelope's top level). The TYPE marker uses `TYPE:` (not
    `INTERNALCLASSTYPE:`), so we read `env["data"]["TYPE"]`.
    """
    if not env:
        return ""
    data = env.get("data") or {}
    return data.get("TYPE", "")


def validate_frame(frame_path):
    """Confirm <frame_path> resolves and is a Frame (not a class / folder /
    other). Plant Simulation's `InternalClassType` is "Frame" for both
    top-level Models.Model and nested sub-Frames."""
    info(f"validating frame path: {frame_path}")
    env = run_class_ops("inspect", frame_path)
    if not env or not env.get("ok"):
        return False, f"frame path does not resolve: {frame_path}"
    ict = _ict(env)
    if ict != "Frame":
        return False, f"path {frame_path} is not a Frame (got {ict!r})"
    return True, None


def validate_parent_class(parent_path):
    """Confirm <parent_path> resolves and its InternalClassType is Method."""
    info(f"validating parent class: {parent_path}")
    env = run_class_ops("inspect", parent_path)
    if not env or not env.get("ok"):
        return False, f"parent class path does not resolve: {parent_path}"
    ict = _ict(env)
    if ict != "Method":
        return False, (f"parent class {parent_path} is not a Method "
                       f"(got {ict!r}) — pick a Method subclass or "
                       f"inherit-from-Method class")
    return True, None


def validate_no_collision(frame_path, method_name):
    """Check that <frame_path>.<method_name> does NOT already resolve.
    Returns (True, None) on free slot, (False, reason) on collision."""
    candidate = frame_path + "." + method_name
    env = run_class_ops("inspect", candidate)
    if env is None:
        # Transport / parse failure — fail closed: assume collision to
        # avoid silently creating a duplicate if the inspect call couldn't
        # reach the server at all.
        return False, "could not verify name slot (inspect failed)"
    if env.get("ok"):
        ict = _ict(env)
        return False, (f"name already exists at {candidate} "
                       f"(type={ict or '?'})")
    # ok:false from inspect = path does not resolve → free slot
    return True, None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Insert a new Method instance under a Plant Simulation "
                    "Frame. Writes NO code — only creates the empty Method "
                    "container. Use local-simtalk-write-simtalk afterwards to "
                    "fill in the body.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--frame", required=True,
                    help="Target Frame path (where to insert the Method). "
                         "Must resolve to a Frame / SubFrame / .Models.Model.")
    ap.add_argument("--method-name",
                    help="Name of the new Method. Default: 'myMethod'. "
                         "Must NOT be a SimTalk reserved word and must NOT "
                         "already exist under <frame>.")
    ap.add_argument("--parent-class",
                    help="Parent class for the new Method. Default: "
                         + DEFAULT_PARENT_CLASS
                         + ". Must be a Method (or Method subclass).")
    ap.add_argument("--dry-run", action="store_true",
                    help="Validate inputs only — do NOT call duplicate() or "
                         "touch the server.")
    args = ap.parse_args()

    method_name = args.method_name or "myMethod"
    parent_class = args.parent_class or DEFAULT_PARENT_CLASS

    # ---- 1. Identifier shape ----
    if not is_valid_identifier(method_name):
        emit_envelope({
            "ok": False,
            "error": "invalid_method_name",
            "detail": f"{method_name!r} is not a valid Plant Simulation "
                      f"identifier (must start with letter or _, contain "
                      f"only letters/digits/_)",
        })
        sys.exit(1)

    # ---- 2. Reserved-word block ----
    if is_reserved(method_name):
        emit_envelope({
            "ok": False,
            "error": "name_is_simtalk_reserved_word",
            "detail": f"{method_name!r} collides with a SimTalk data type, "
                      f"module root, or control keyword — Plant Simulation "
                      f"rejects it as a Method name. See "
                      f"references/simtalk-reserved-words.md",
        })
        sys.exit(1)

    info("===== SUMMARY =====")
    info(f"  frame        : {args.frame}")
    info(f"  method-name  : {method_name}")
    info(f"  parent-class : {parent_class}")
    info("===================")

    # ---- 3. Frame resolves & is a Frame ----
    ok, err = validate_frame(args.frame)
    if not ok:
        emit_envelope({"ok": False, "error": "frame_invalid", "detail": err})
        sys.exit(1)

    # ---- 4. Parent class resolves & is a Method ----
    ok, err = validate_parent_class(parent_class)
    if not ok:
        emit_envelope({"ok": False, "error": "parent_class_invalid",
                       "detail": err})
        sys.exit(1)

    # ---- 5. No name collision ----
    ok, err = validate_no_collision(args.frame, method_name)
    if not ok:
        emit_envelope({"ok": False, "error": "name_collision", "detail": err})
        sys.exit(1)

    info("all pre-flight validations passed")

    if args.dry_run:
        info("DRY RUN — skipping duplicate()")
        emit_envelope({
            "ok": True,
            "dry_run": True,
            "method_path": f"{args.frame}.{method_name}",
            "frame_path": args.frame,
            "method_name": method_name,
            "parent_class": parent_class,
        })
        sys.exit(0)

    # ---- 6. Actually create via class_ops.py duplicate ----
    info(f"calling class_ops.py duplicate {parent_class} {args.frame} "
         f"{method_name}")
    env = run_class_ops("duplicate", parent_class, args.frame, method_name,
                        timeout=60)
    if not env or not env.get("ok"):
        err = (env or {}).get("error", "unknown")
        emit_envelope({
            "ok": False,
            "error": "duplicate_failed",
            "detail": (env or {}).get("log_tail", err),
        })
        sys.exit(1)

    # class_ops.py puts the AFTER_PATH / AFTER_TYPE / etc. keys under
    # `data`, not under a top-level `after` key.
    after = (env or {}).get("data") or {}
    method_path = after.get("AFTER_PATH") or f"{args.frame}.{method_name}"

    info(f"created Method: {method_path}")

    emit_envelope({
        "ok": True,
        "method_path": method_path,
        "frame_path": args.frame,
        "method_name": method_name,
        "parent_class": parent_class,
        "internal_class_type": (after.get("TYPE") or "Method"),
        "origin": (after.get("ORIGIN") or parent_class),
        "origin_root": (after.get("ORIGINROOT") or parent_class),
        "class": (after.get("CLASS") or parent_class),
    })


if __name__ == "__main__":
    main()