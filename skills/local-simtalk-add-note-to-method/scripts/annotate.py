#!/usr/bin/env python3
"""annotate.py — chunked-write driver for annotating one Method's `program`.

Reads the original program via SimTalk markers + readlog (the only
byte-exact path in v15+ — `log` field of simtalk_run reply contains only
"execute success" / "code execute failed...", not print output), then
writes the NOTE block + original body in chunked `obj.program := ...`
operations, then syntax-checks via `simtalk_hasError` and verifies via
readback of the same marker pattern.

Usage:
    python3 scripts/annotate.py \
        --path .P4_CTU.AdvancedObject.Software.RCS.m_addBinStateInTable \
        --note-file notes/m_addBinStateInTable.md \
        --backup code_log/P4_CTU_AdvancedObject_Software_RCS_m_addBinStateInTable_original.txt

Optional:
    --chunk-size N    Lines per chunk (default 10). For Chinese-heavy
                      NOTEs (each Chinese char adds ~6 bytes via chr()),
                      6-8 is safer; for English-only, 12-15 is fine.
    --host HOST       Plant Simulation TCP host (default host.docker.internal)
    --port PORT       Plant Simulation TCP port (default 50007)
    --socket-client   Path to socket_client.py (default auto-detected)
    --no-smoke        Skip the obj.execute smoke test
    --no-readback     Skip the readback verification

Implements the "Verified workflow" from SKILL.md:
  1. read original via markers + readlog
  2. encode NOTE + body via encode_for_simtalk()
  3. split NOTE into chunks; send 1 simtalk_run per chunk
  4. retry up to 5x per chunk with 1s sleep (Quirk #21)
  5. syntax-check via simtalk_hasError
  6. verify via readback of obj.Program with markers
"""
import argparse
import json
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from simtalk_string_utils import encode_for_simtalk, chunk_lines


DEFAULT_HOST = "host.docker.internal"
DEFAULT_PORT = 50007
DEFAULT_SOCKET_CLIENT = "/root/skills-of-plant-simulation-no-experience/skills/local-simtalk-execution/scripts/socket_client.py"
MAX_RETRIES = 5
RETRY_SLEEP = 1.0


def send_run(code, host, port, socket_client, timeout=30):
    payload = json.dumps({
        "type": "simtalk_run",
        "action_id": uuid.uuid4().hex,
        "simtalk_code": code,
    }, ensure_ascii=False) + "||END||"
    r = subprocess.run([
        sys.executable, socket_client,
        "--host", host, "--port", str(port),
        "--data", payload,
        "--resp-mode", "delimiter", "--resp-delimiter", "||END||",
        "--timeout", str(timeout),
    ], capture_output=True, text=True)
    return r.returncode, r.stdout


def readlog(host, port, socket_client, timeout=30):
    payload = json.dumps({"type": "readlog", "action_id": uuid.uuid4().hex}, ensure_ascii=False) + "||END||"
    r = subprocess.run([
        sys.executable, socket_client,
        "--host", host, "--port", str(port),
        "--data", payload,
        "--resp-mode", "delimiter", "--resp-delimiter", "||END||",
        "--timeout", str(timeout),
    ], capture_output=True, text=True)
    try:
        env = json.loads(r.stdout.rstrip("\n").rstrip("||END||").rstrip())
        return env.get("log", "")
    except Exception:
        return r.stdout


def capture_program(path, host, port, socket_client, timeout=15):
    """Capture obj.Program byte-exactly via markers + readlog.

    Returns the decoded program string. Single-line marker format means
    we use a JSON escape-aware decode (`\\n` -> real LF).
    """
    m_start = "###CAP_START_" + uuid.uuid4().hex + "###"
    m_end = "###CAP_END_" + uuid.uuid4().hex + "###"
    code = (
        f'var obj: object\n'
        f'obj := str_to_obj("{path}")\n'
        f'print "{m_start}"\n'
        f'print obj.Program\n'
        f'print "{m_end}"\n'
    )
    rc, out = send_run(code, host, port, socket_client, timeout=timeout)
    if rc != 0:
        raise RuntimeError(f"capture simtalk_run failed: rc={rc} out={out[:200]}")
    time.sleep(0.3)
    log = readlog(host, port, socket_client)
    TS_RE = re.compile(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}:\s?(.*)$')
    in_block = False
    captured = []
    for ln in log.split("\n"):
        m = TS_RE.match(ln)
        s = m.group(1) if m else ln
        if m_start in s:
            in_block = True
            continue
        if m_end in s:
            break
        if in_block:
            captured.append(s)
    joined = "\n".join(captured)
    # readlog response uses JSON-envelope escape style: \n = real LF, \t = real tab
    return joined.replace("\\n", "\n").replace("\\t", "\t")


def send_chunk(path, chunk_idx, total, payload_rhs, is_first, host, port, socket_client, timeout=30):
    """Send one chunk-write with retry. payload_rhs is the RHS expression (encoded).

    Success detection (Quirk #7 double-check):
      rc == 0 AND result == "success" AND log starts with "execute success".
    Print output is NOT in `log` field in v15+ (only in GUI Console buffer).
    """
    if is_first:
        op = f"obj.program := {payload_rhs}"
    else:
        op = f"obj.program := obj.program + chr(10) + {payload_rhs}"
    code = f'var obj: object; obj := str_to_obj("{path}"); {op}'
    for attempt in range(1, MAX_RETRIES + 1):
        rc, out = send_run(code, host, port, socket_client, timeout=timeout)
        try:
            parsed = json.loads(out.rstrip("\n").rstrip("||END||").rstrip())
        except Exception:
            parsed = {}
        result = parsed.get("result", "")
        log = parsed.get("log", "")
        ok = (rc == 0 and result == "success" and log.startswith("execute success"))
        print(f"  chunk {chunk_idx}/{total} attempt {attempt}: rc={rc} "
              f"result={result!r} log_prefix={log[:30]!r}")
        if ok:
            return True
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_SLEEP)
    return False


def syntax_check(path, host, port, socket_client, timeout=15):
    """Return the simtalk_hasError string for the modified program."""
    m_start = "###SE_START_" + uuid.uuid4().hex + "###"
    m_end = "###SE_END_" + uuid.uuid4().hex + "###"
    code = (
        f'var obj: object\n'
        f'obj := str_to_obj("{path}")\n'
        f'var synOut: string\n'
        f'synOut := simtalk_hasError(obj.Program)\n'
        f'print "{m_start}"\n'
        f'print synOut\n'
        f'print "{m_end}"\n'
    )
    rc, out = send_run(code, host, port, socket_client, timeout=timeout)
    if rc != 0:
        return f"<send failed: rc={rc}>"
    time.sleep(0.3)
    log = readlog(host, port, socket_client)
    TS_RE = re.compile(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}:\s?(.*)$')
    in_block = False
    for ln in log.split("\n"):
        m = TS_RE.match(ln)
        s = m.group(1) if m else ln
        if m_start in s:
            in_block = True
            continue
        if m_end in s:
            break
        if in_block:
            return s.strip()
    return "<no result captured>"


def readback(path, host, port, socket_client, timeout=15):
    """Read obj.Program back via markers + readlog. Returns the decoded program string."""
    return capture_program(path, host, port, socket_client, timeout=timeout)


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--path", required=True, help="Method path (e.g., .P4_CTU.AdvancedObject.Software.RCS.m_addBinStateInTable)")
    p.add_argument("--note-file", required=True, help="UTF-8 NOTE block file (one logical line per newline)")
    p.add_argument("--backup", required=True, help="Original-program backup file path (will be overwritten if exists)")
    p.add_argument("--chunk-size", type=int, default=10, help="Lines per chunk (default 10; Chinese NOTEs often need 6-8)")
    p.add_argument("--host", default=DEFAULT_HOST)
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    p.add_argument("--socket-client", default=DEFAULT_SOCKET_CLIENT)
    p.add_argument("--no-smoke", action="store_true")
    p.add_argument("--no-readback", action="store_true")
    args = p.parse_args()

    print(f"=== Annotate {args.path} ===")
    note_text = Path(args.note_file).read_text(encoding="utf-8")
    note_lines = note_text.splitlines()
    backup_path = Path(args.backup)

    print(f"Step 1: capture original program")
    body = capture_program(args.path, args.host, args.port, args.socket_client)
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(body, encoding="utf-8")
    print(f"  captured {len(body)} chars -> {backup_path}")

    encoded_note = encode_for_simtalk(note_text)
    encoded_body = encode_for_simtalk(body)
    print(f"Step 2: encode NOTE ({len(encoded_note)}B) + body ({len(encoded_body)}B)")

    note_chunks = chunk_lines(note_lines, args.chunk_size)
    total = len(note_chunks) + 1
    print(f"Step 3: {len(note_chunks)} NOTE chunks + 1 body chunk = {total} writes (chunk_size={args.chunk_size})")

    print(f"Step 4: write chunks")
    for i, lines in enumerate(note_chunks, start=1):
        rhs = encode_for_simtalk("\n".join(lines))
        print(f"  chunk {i}/{total}: {len(rhs)}B")
        if not send_chunk(args.path, i, total, rhs, is_first=(i == 1),
                          host=args.host, port=args.port, socket_client=args.socket_client):
            sys.exit(f"FAILED at chunk {i}; aborting")
        time.sleep(0.1)
    print(f"  chunk {total}/{total}: body, {len(encoded_body)}B")
    if not send_chunk(args.path, total, total, encoded_body, is_first=False,
                      host=args.host, port=args.port, socket_client=args.socket_client):
        sys.exit("FAILED at body chunk; aborting")

    print(f"Step 5: syntax check")
    syn = syntax_check(args.path, args.host, args.port, args.socket_client)
    print(f"  simtalk_hasError = {syn!r}")

    if not args.no_smoke:
        print(f"Step 6: smoke test (obj.execute)")
        smoke = (
            f'var obj: object; obj := str_to_obj("{args.path}"); '
            f'print "EXEC_DONE"'
        )
        rc, out = send_run(smoke, args.host, args.port, args.socket_client, timeout=15)
        print(f"  rc={rc}")

    if not args.no_readback:
        print(f"Step 7: readback verification")
        rb = readback(args.path, args.host, args.port, args.socket_client)
        print(f"  readback {len(rb)} chars")
        has_note = note_lines[0].strip().startswith("-- Method path") if note_lines else False
        ends_correctly = rb.rstrip().endswith("next") or rb.rstrip().endswith("end")
        print(f"  starts with NOTE header: {has_note}")
        print(f"  ends with body terminator (next/end): {ends_correctly}")
        if not (has_note and ends_correctly):
            print("  VERIFICATION FAILED")
            print("--- readback tail ---")
            print(rb[-500:])


if __name__ == "__main__":
    main()
