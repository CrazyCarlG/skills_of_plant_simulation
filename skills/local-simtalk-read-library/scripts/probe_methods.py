#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Probe every Method object in a Plant Simulation model — capture its
metadata (path / name / type / encrypted / has-syntax-error /
num-in-execution) and its verbatim source code (`&Method.Program`).

Usage:
  python3 scripts/probe_methods.py [--no-infobox] <paths.txt> [out.tsv]

Inputs:
  <paths.txt>    one Method path per line (e.g. from
                 `local-simtalk-get-folder-tree` filtered to type=Method)
  [out.tsv]      tab-separated output (default: data/methods_raw.tsv)

Output columns (TSV):
  path<TAB>name<TAB>type<TAB>encrypted<TAB>has_syntax_error<TAB>num_in_execution<TAB>program_len<TAB>program

The script batches paths in groups of 8 (empirical — see references/
protocol-notes.md §LIB-2). Each batch sends one simtalk_run + one
readlog, tagged with a unique `###LIB_HEADER<id>###` marker.

Skill convention (matches local-simtalk-execution v18→v19):
  - On entry, open a non-modal infoBox on the Plant Simulation GUI
    describing what is being done (`infoBox(text, false)`).
  - On exit (success OR failure), close the infoBox defensively —
    call `infoBox("", false)` twice to be safe.
  - Pass `--no-infobox` to suppress the open/close cycle for batch /
    headless runs.
"""
import json
import os
import re
import subprocess
import sys
import time
import uuid


HOST = "host.docker.internal"
PORT = 50007
SOCKET_CLIENT = "/root/skills_of_plant_simulation/skills/local-simtalk-execution/scripts/socket_client.py"
BATCH = 8  # paths per simtalk_run


def send_run(code, timeout=30):
    """Send one simtalk_run. Returns (returncode, raw_stdout_text)."""
    payload = (json.dumps({
        "type": "simtalk_run",
        "action_id": uuid.uuid4().hex,
        "simtalk_code": code,
    }, ensure_ascii=False) + "||END||")
    r = subprocess.run(
        [sys.executable, SOCKET_CLIENT,
         "--host", HOST, "--port", str(PORT),
         "--data", payload,
         "--resp-mode", "delimiter", "--resp-delimiter", "||END||",
         "--timeout", str(timeout)],
        capture_output=True, text=True,
    )
    return r.returncode, r.stdout


def send_readlog(timeout=10):
    """Send one readlog. Returns (returncode, raw_stdout_text)."""
    payload = (json.dumps({
        "type": "readlog",
        "action_id": uuid.uuid4().hex,
    }) + "||END||")
    r = subprocess.run(
        [sys.executable, SOCKET_CLIENT,
         "--host", HOST, "--port", str(PORT),
         "--data", payload,
         "--resp-mode", "delimiter", "--resp-delimiter", "||END||",
         "--timeout", str(timeout)],
        capture_output=True, text=True,
    )
    return r.returncode, r.stdout


def send_infobox(text, timeout=10):
    """Open or update a non-modal infoBox on the Plant Simulation GUI."""
    safe = text.replace("\\", "\\\\").replace("\"", "\\\"")
    send_run(f'infoBox("{safe}", false)', timeout=timeout)


def send_infobox_close():
    """Defensively close the infoBox — call twice (idempotent)."""
    send_run('infoBox("", false)', timeout=10)
    send_run('infoBox("", false)', timeout=10)


# ---------------------------------------------------------------------------
# SimTalk code generation
# ---------------------------------------------------------------------------

def build_method_block(i, path):
    """Return the SimTalk fragment that probes one Method and prints
    its metadata + source delimited by per-method markers.

    NOTE: when `o` is already an `object` reference (as returned by
    `str_to_obj`), accessing its Method attributes does NOT need the
    `&` reference operator. The `&` operator is for converting a Method
    **name/content** into a Method **object** — once you have an
    `object` reference, you access its attributes directly. (The
    "&o.Encrypted" form actually raises a compile error:
    "The ref-operator has no effect in this context." — caught at
    runtime by Quirk #7 / §LIB-5.)
    """
    p_esc = path.replace("\\", "\\\\").replace("\"", "\\\"")
    return f'''
o := str_to_obj("{p_esc}")
print "###LIB_BEGIN_{i}###"
if o = void
  print "META_PATH={p_esc}"
  print "META_VOID=true"
else
  print "META_PATH={p_esc}"
  print "META_NAME=" + o.Name
  print "META_TYPE=" + o.InternalClassType
  print "META_ENCRYPTED=" + to_str(o.Encrypted)
  print "META_SYNTAX_ERROR=" + to_str(o.HasSyntaxError)
  print "META_NUM_IN_EXECUTION=" + to_str(o.NumInExecution)
  print "###LIB_BODY_{i}###"
  if o.Encrypted
    print "<encrypted>"
  else
    print o.Program
  end
  print "###LIB_END_{i}###"
end
'''


def build_batch_code(batch_id, paths):
    """Assemble the full SimTalk program for one batch."""
    blocks = "\n".join(build_method_block(i, p) for i, p in enumerate(paths))
    # `var o: object` declared ONCE before the method blocks (see INH-6
    # in local-simtalk-get-class-inheritance/references/protocol-notes.md —
    # a `var` declared inside a loop body collides on the second iteration).
    return f"""var o: object
print "###LIB_HEADER{batch_id}###"
{blocks}
"""


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

TS_RE = re.compile(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}:\s?(.*)$')


def strip_timestamp(line):
    """Drop the `YYYY-MM-DD HH:MM:SS: ` prefix that the readlog buffer
    prepends to every line."""
    m = TS_RE.match(line)
    if m:
        return m.group(1)
    return line


def parse_log_field(log_text, batch_id, batch_paths):
    """Parse the JSON-escaped log text into per-method rows.

    Returns a list of dicts in the same order as batch_paths. Missing
    methods (no markers found) become rows with only the path set and
    the rest blank.
    """
    # Unescape \\n -> real newlines (lifelines §A4 / protocol-notes §LIB-3)
    chunks = log_text.replace("\\n", "\n").split("\n")
    lines = [strip_timestamp(c).rstrip('"').rstrip() for c in chunks]

    header = f"###LIB_HEADER{batch_id}###"
    if header in lines:
        idx = lines.index(header)
        lines = lines[idx + 1:]
    else:
        # Marker missing — return blanks so the caller can see what's missing
        return [{"path": p, "name": "", "type": "", "encrypted": "",
                 "has_syntax_error": "", "num_in_execution": "",
                 "program_len": 0, "program": ""} for p in batch_paths]

    rows = [None] * len(batch_paths)
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("###LIB_BEGIN_") and line.endswith("###"):
            try:
                idx_m = int(line[len("###LIB_BEGIN_"):-3])
            except ValueError:
                i += 1
                continue
            meta = {}
            j = i + 1
            while j < len(lines) and not lines[j].startswith("###LIB_BODY_"):
                ml = lines[j]
                if ml.startswith("META_"):
                    eq = ml.find("=")
                    if eq > 0:
                        key = ml[:eq]
                        val = ml[eq + 1:]
                        meta[key] = val
                # If we hit another BEGIN without BODY (VOID case), break
                if ml.startswith("###LIB_BEGIN_"):
                    break
                j += 1
            # Body
            program_lines = []
            if j < len(lines) and lines[j].startswith("###LIB_BODY_"):
                j += 1
                while j < len(lines) and not lines[j].startswith("###LIB_END_"):
                    program_lines.append(lines[j])
                    j += 1
            program = "\n".join(program_lines)
            encrypted = meta.get("META_ENCRYPTED", "").lower() == "true"
            is_void = meta.get("META_VOID", "").lower() == "true"
            rows[idx_m] = {
                "path": meta.get("META_PATH", batch_paths[idx_m]),
                "name": meta.get("META_NAME", ""),
                "type": meta.get("META_TYPE", ""),
                "encrypted": "true" if encrypted else "false",
                "has_syntax_error": meta.get("META_SYNTAX_ERROR", ""),
                "num_in_execution": meta.get("META_NUM_IN_EXECUTION", ""),
                "program_len": len(program) if program else 0,
                "program": program if not encrypted else "<encrypted>",
                "_void": is_void,
            }
            i = j + 1
        else:
            i += 1

    # Fill in any missing rows
    for k, row in enumerate(rows):
        if row is None:
            rows[k] = {"path": batch_paths[k], "name": "", "type": "",
                       "encrypted": "", "has_syntax_error": "",
                       "num_in_execution": "", "program_len": 0,
                       "program": "", "_void": False}
    return rows


# ---------------------------------------------------------------------------
# Main driver
# ---------------------------------------------------------------------------

def probe_batch(batch_paths, batch_id, timeout=30):
    code = build_batch_code(batch_id, batch_paths)
    rc, out = send_run(code, timeout=timeout)
    if rc != 0:
        print(f"[batch {batch_id[:6]}] run FAIL rc={rc} out={out[:200]}",
              file=sys.stderr)
        return []
    time.sleep(0.2)
    rc2, raw = send_readlog(timeout=15)
    if rc2 != 0:
        print(f"[batch {batch_id[:6]}] readlog FAIL rc={rc2} raw={raw[:200]}",
              file=sys.stderr)
        return []

    log_text = None
    try:
        env = json.loads(raw)
        log_text = env.get("log", "")
    except json.JSONDecodeError:
        # Truncated JSON — pull out the log field by regex
        m = re.search(r'"log":\s*"(.*?)"\s*\}\|\|END\|\|', raw, re.S)
        if m:
            log_text = m.group(1)
        else:
            print(f"[batch {batch_id[:6]}] could not extract log; raw tail:\n"
                  f"{raw[-400:]}", file=sys.stderr)
            return []

    return parse_log_field(log_text, batch_id, batch_paths)


def main():
    args = sys.argv[1:]
    no_infobox = False
    if "--no-infobox" in args:
        no_infobox = True
        args.remove("--no-infobox")

    if len(args) < 1:
        print("usage: probe_methods.py [--no-infobox] <paths.txt> [out.tsv]",
              file=sys.stderr)
        sys.exit(2)
    paths_file = args[0]
    out_file = args[1] if len(args) > 1 else "data/methods_raw.tsv"

    with open(paths_file) as f:
        paths = [ln.strip() for ln in f if ln.strip()]
    print(f"probing {len(paths)} method paths (batch={BATCH})", file=sys.stderr)

    os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)

    all_rows = []
    try:
        if not no_infobox:
            send_infobox(
                f"[probe_methods] start: paths={len(paths)} batch={BATCH}"
            )

        for i in range(0, len(paths), BATCH):
            batch = paths[i:i + BATCH]
            batch_id = uuid.uuid4().hex[:8]
            label = f"batch {i // BATCH + 1}/{(len(paths) + BATCH - 1) // BATCH}"
            print(f"  [{label}] probing {len(batch)} paths (id={batch_id})",
                  file=sys.stderr)
            if not no_infobox:
                send_infobox(
                    f"[probe_methods] {label}: paths={i + 1}-{i + len(batch)}"
                )
            rows = probe_batch(batch, batch_id)
            print(f"  [{label}] got {len([r for r in rows if r])} rows",
                  file=sys.stderr)
            all_rows.extend(rows)

        # Write TSV
        with open(out_file, "w", encoding="utf-8") as f:
            for r in all_rows:
                # TSV: 8 fields. Program may contain tabs and newlines; we
                # keep newlines (as real \n) and replace tabs with spaces.
                prog = r["program"].replace("\t", "    ")
                f.write(f"{r['path']}\t{r['name']}\t{r['type']}\t"
                        f"{r['encrypted']}\t{r['has_syntax_error']}\t"
                        f"{r['num_in_execution']}\t{r['program_len']}\t"
                        f"{prog}\n")
        print(f"wrote {len(all_rows)} rows to {out_file}", file=sys.stderr)
        print(json.dumps([{k: v for k, v in r.items() if k != '_void'}
                          for r in all_rows], ensure_ascii=False, indent=2))
    finally:
        if not no_infobox:
            send_infobox_close()


if __name__ == "__main__":
    main()