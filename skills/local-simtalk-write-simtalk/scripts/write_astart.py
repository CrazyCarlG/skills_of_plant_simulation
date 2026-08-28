#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
write_astart.py — chunked write of A* algorithm into .Models.Model.Astart.

Full-replace mode (the existing program was empty, so no original to preserve).
Splits source into N-line chunks; first chunk uses `obj.program := <encoded>`,
subsequent chunks use `obj.program := obj.program + chr(10) + <encoded>`.
Verifies via simtalk_hasError(obj.Program).

Usage:
  python3 write_astart.py [--chunk-size N] [--no-infobox]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
SOCKET = os.path.normpath(
    os.path.join(HERE, "..", "..", "local-simtalk-execution", "scripts", "socket_client.py")
)
SIMTALK_STR = os.path.normpath(
    os.path.join(HERE, "..", "..", "local-simtalk-add-note-to-method", "scripts", "simtalk_string_utils.py")
)

sys.path.insert(0, os.path.dirname(SIMTALK_STR))
from simtalk_string_utils import encode_for_simtalk, scan_note_lines  # noqa: E402

PATH = ".Models.Model.Astart"
SOURCE_FILE = os.path.join(HERE, "..", "code_log", "Astart_source.sim")
HOST = os.environ.get("SIMTALK_HOST", "host.docker.internal")
PORT = int(os.environ.get("SIMTALK_PORT", "50007"))


def call(payload, timeout=20):
    """Send one TCP payload; return parsed JSON envelope (or raw stdout on failure)."""
    body = payload + "||END||"
    r = subprocess.run(
        [sys.executable, SOCKET, "--host", HOST, "--port", str(PORT),
         "--data", body, "--resp-mode", "delimiter", "--resp-delimiter", "||END||",
         "--timeout", str(timeout)],
        capture_output=True, text=True,
    )
    out = r.stdout
    try:
        # Trim trailing whitespace, then the literal suffix ||END||.
        out = out.rstrip()
        if out.endswith("||END||"):
            out = out[:-len("||END||")]
        out = out.rstrip()
        return json.loads(out)
    except Exception:
        return {"_raw": out, "_rc": r.returncode}


def simtalk_run(code, timeout=15):
    """Send a simtalk_run payload, return (envelope_dict, log_text)."""
    payload = json.dumps(
        {"type": "simtalk_run", "action_id": uuid.uuid4().hex, "simtalk_code": code},
        ensure_ascii=False,
    )
    env = call(payload, timeout=timeout)
    # In v15+, print() output is in readlog(), not in env["log"].
    # Always fetch readlog afterwards to get the actual output.
    return env


def readlog(timeout=20):
    payload = json.dumps({"type": "readlog", "action_id": uuid.uuid4().hex})
    env = call(payload, timeout=timeout)
    return env.get("log", "") if isinstance(env, dict) else ""


def infobox(text, timeout=10):
    return simtalk_run(f'infoBox("{text}", false)', timeout=timeout)


def infobox_close(timeout=5):
    simtalk_run('infoBox("", false)', timeout=timeout)
    simtalk_run('infoBox("", false)', timeout=timeout)


def chunk_source(src_text, chunk_size):
    """Yield (chunk_index, is_first, list_of_lines) for chunked writes."""
    lines = src_text.split("\n")
    chunks = []
    for i in range(0, len(lines), chunk_size):
        chunks.append(lines[i:i + chunk_size])
    for i, chunk in enumerate(chunks):
        yield i, (i == 0), chunk


def write_chunk(path, chunk_lines, is_first, timeout=20):
    """Write one chunk into obj.program. Returns True on success."""
    chunk_text = "\n".join(chunk_lines)
    encoded = encode_for_simtalk(chunk_text)
    if is_first:
        code = f'var o: object\no := str_to_obj("{path}")\no.program := {encoded}'
    else:
        code = (
            f'var o: object\n'
            f'o := str_to_obj("{path}")\n'
            f'o.program := o.program + chr(10) + {encoded}'
        )
    env = simtalk_run(code, timeout=timeout)
    if not isinstance(env, dict):
        return False, f"non-json reply: {env}"
    if env.get("result") != "success":
        return False, f"result={env.get('result')} log={env.get('log','')[:200]}"
    log = env.get("log", "")
    # Quirk #7: server reports success but log starts with "code execute failed"
    if log.startswith("code execute failed"):
        return False, f"soft-fail log={log[:300]}"
    return True, ""


def verify_syntax(path, timeout=15):
    """Run simtalk_hasError on the written program; return (ok, message)."""
    code = (
        f'var o: object\n'
        f'o := str_to_obj("{path}")\n'
        f'var syn: string\n'
        f'syn := simtalk_hasError(o.Program)\n'
        f'var okStr: string\n'
        f'if syn = "has no Error"\n'
        f'  okStr := "true"\n'
        f'else\n'
        f'  okStr := "false"\n'
        f'end\n'
        f'print "###SYN_OK:" + okStr + "###"\n'
        f'print "###SYN_OUT:" + syn + "###"'
    )
    env = simtalk_run(code, timeout=timeout)
    if not isinstance(env, dict) or env.get("result") != "success":
        return False, f"verify call failed: {env.get('log','')[:200] if isinstance(env, dict) else env}"
    # v15+ log field may be empty; pull from readlog
    log = env.get("log", "")
    if "###SYN_OK:" not in log:
        log = readlog()
    ok_match = re.search(r'###SYN_OK:(true|false)###', log)
    out_match = re.search(r'###SYN_OUT:(.*?)###', log)
    if not ok_match:
        return False, f"no marker in log: {log[:300]}"
    return ok_match.group(1) == "true", out_match.group(1) if out_match else ""


def readback(path, timeout=15):
    """Print program length + head + tail; return the log text."""
    code = (
        f'var o: object\n'
        f'o := str_to_obj("{path}")\n'
        f'print "###RB_LEN:" + to_str(strlen(o.Program)) + "###"\n'
        f'print "###RB_HEAD:" + str_copy(o.Program, 1, 200) + "###"\n'
        f'print "###RB_TAIL:" + str_copy(o.Program, strlen(o.Program) - 200, 200) + "###"'
    )
    env = simtalk_run(code, timeout=timeout)
    if not isinstance(env, dict) or env.get("result") != "success":
        return env.get("log", "") if isinstance(env, dict) else ""
    log = env.get("log", "")
    if "###RB_LEN:" not in log:
        log = readlog()
    return log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunk-size", type=int, default=10)
    ap.add_argument("--no-infobox", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(SOURCE_FILE):
        print(f"FATAL: source file missing: {SOURCE_FILE}", file=sys.stderr)
        sys.exit(2)

    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        src_text = f.read()

    src_lines = src_text.split("\n")
    findings = scan_note_lines(src_lines)
    if findings:
        print(f"FATAL: source has {len(findings)} forbidden-char findings; abort.", file=sys.stderr)
        for f in findings[:10]:
            print(f"  {f}", file=sys.stderr)
        sys.exit(3)

    n_chunks = (len(src_lines) + args.chunk_size - 1) // args.chunk_size
    print(f"[plan] {len(src_lines)} lines → {n_chunks} chunks of ~{args.chunk_size} lines")

    if not args.no_infobox:
        infobox(f"write-simtalk -> {PATH}: writing A* ({n_chunks} chunks)")

    failures = []
    t0 = time.time()
    for i, is_first, chunk in chunk_source(src_text, args.chunk_size):
        ok, err = write_chunk(PATH, chunk, is_first, timeout=30)
        status = "OK" if ok else f"FAIL: {err}"
        print(f"[chunk {i+1}/{n_chunks} lines={len(chunk)} first={is_first}] {status}")
        if not ok:
            failures.append((i, err))
            if not args.no_infobox:
                infobox_close()
            sys.exit(1)

    if not args.no_infobox:
        # keep open during verify; close at the very end
        pass

    print(f"[write] all {n_chunks} chunks OK in {time.time()-t0:.1f}s")

    print("[verify] running simtalk_hasError...")
    ok, msg = verify_syntax(PATH)
    print(f"[verify] syntax_ok={ok} msg={msg!r}")
    if not ok:
        if not args.no_infobox:
            infobox_close()
            infobox_close()
        sys.exit(4)

    print("[readback]")
    log = readback(PATH)
    for ln in log.split("\n"):
        m_ts = re.match(r"^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}:\s?(.*)$", ln)
        s = m_ts.group(1) if m_ts else ln
        if s.startswith("###RB_"):
            print(f"  {s}")

    if not args.no_infobox:
        infobox_close()
        infobox_close()

    print("[done] OK")


if __name__ == "__main__":
    main()