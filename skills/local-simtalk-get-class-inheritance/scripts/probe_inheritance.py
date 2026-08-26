#!/usr/bin/env python3
"""Probe Origin/OriginRoot/Class via simtalk_run + readlog.

The v15+ readlog returns JSON with the log field containing \\n (escaped
newlines). The cumulative buffer grows per batch and gets capped at 65536
bytes. We parse the JSON envelope loosely (allowing truncation) and then
extract data lines via regex.
"""
import json, re, subprocess, sys, os, time

HOST = "host.docker.internal"
PORT = 50007
SOCKET_CLIENT = "/root/skills_of_plant_simulation/skills/local-simtalk-execution/scripts/socket_client.py"


def send_run(code, timeout=30):
    payload = json.dumps({"type": "simtalk_run",
                          "action_id": os.urandom(8).hex(),
                          "simtalk_code": code}) + "||END||"
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
    payload = json.dumps({"type": "readlog",
                          "action_id": os.urandom(8).hex()}) + "||END||"
    r = subprocess.run(
        [sys.executable, SOCKET_CLIENT,
         "--host", HOST, "--port", str(PORT),
         "--data", payload,
         "--resp-mode", "delimiter", "--resp-delimiter", "||END||",
         "--timeout", str(timeout)],
        capture_output=True, text=True,
    )
    return r.returncode, r.stdout


def build_code(paths):
    lines = ['var o: object', 'print "###INH_BATCH###"']
    for p in paths:
        esc = p.replace('\\', '\\\\').replace('"', '\\"')
        lines.append(f'o := str_to_obj("{esc}")')
        lines.append(
            f'if o = void then print "{p} | VOID" '
            f'else print "{p} | name=" + o.Name + " | type=" + o.InternalClassType '
            f'+ " | Origin=" + obj_to_str(o.Origin) + " | OriginRoot=" + obj_to_str(o.OriginRoot) '
            f'+ " | Class=" + obj_to_str(o.Class) end'
        )
    return "\n".join(lines)


# regex: <ts> <HH:MM:SS>: <DATA>
TS_RE = re.compile(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}:\s+(.*)$')
LINE_RE = re.compile(
    r'^(?P<path>\S+)\s*\|\s*'
    r'name=(?P<name>[^|]*?)\s*\|\s*'
    r'type=(?P<type>[^|]*?)\s*\|\s*'
    r'Origin=(?P<origin>[^|]*?)\s*\|\s*'
    r'OriginRoot=(?P<originroot>[^|]*?)\s*\|\s*'
    r'Class=(?P<cls>[^|]*?)\s*$'
)
VOID_LINE_RE = re.compile(r'^(?P<path>\S+)\s*\|\s*VOID\s*$')


def parse_log_field(log_text):
    """Extract (path -> dict) from a JSON-escaped log field.

    `log_text` is the value of the JSON `log` key — newlines are literal
    \\n (two chars). We split on those, drop header/timestamp noise, and
    regex out our data lines.
    """
    rows = {}
    # Unescape \n -> real newline for line-by-line scanning
    # (only the newline escape; leave other escapes alone)
    chunks = log_text.replace("\\n", "\n").split("\n")
    for chunk in chunks:
        # strip trailing JSON string quote artifacts if any
        chunk = chunk.rstrip('"').rstrip()
        # Drop the server's "Log file opened" / "execute sim-code" lines
        if "Log file opened" in chunk or "execute sim-code" in chunk:
            continue
        m_ts = TS_RE.match(chunk)
        if not m_ts:
            continue
        payload = m_ts.group(1)
        m = LINE_RE.match(payload)
        if m:
            d = m.groupdict()
            rows.setdefault(d["path"], d)
            continue
        m = VOID_LINE_RE.match(payload)
        if m:
            key = m.group("path")
            rows.setdefault(key, {"path": key, "name": "", "type": "",
                                  "origin": "VOID", "originroot": "VOID",
                                  "cls": "VOID"})
    return rows


def probe_batch(paths, label):
    code = build_code(paths)
    rc, out = send_run(code)
    if rc != 0:
        print(f"[{label}] run FAIL rc={rc} out={out[:200]}", file=sys.stderr)
        return {}
    time.sleep(0.2)
    rc2, raw = send_readlog()
    if rc2 != 0:
        print(f"[{label}] readlog FAIL rc={rc2} raw={raw[:200]}", file=sys.stderr)
        return {}

    # Try strict JSON parse first; fall back to extracting the `log` value via regex.
    log_text = None
    try:
        env = json.loads(raw)
        log_text = env.get("log", "")
    except json.JSONDecodeError:
        # Truncated JSON: pull out the log field by regex
        m = re.search(r'"log":\s*"(.*?)"\s*\}\|\|END\|\|', raw, re.S)
        if m:
            log_text = m.group(1)
        else:
            print(f"[{label}] could not extract log; raw tail:\n{raw[-400:]}",
                  file=sys.stderr)
            return {}

    return parse_log_field(log_text)


def main():
    paths_file = sys.argv[1]
    out_file = sys.argv[2] if len(sys.argv) > 2 else None
    with open(paths_file) as f:
        paths = [ln.strip() for ln in f if ln.strip()]
    print(f"probing {len(paths)} paths", file=sys.stderr)

    BATCH = 12
    all_rows = {}
    for i in range(0, len(paths), BATCH):
        batch = paths[i:i + BATCH]
        label = f"batch {i//BATCH + 1} (paths {i+1}-{i+len(batch)})"
        rows = probe_batch(batch, label)
        print(f"  [{label}] got {len(rows)} rows", file=sys.stderr)
        for p, d in rows.items():
            all_rows.setdefault(p, d)

    print(f"\n# total unique paths: {len(all_rows)} / {len(paths)}", file=sys.stderr)
    missing = [p for p in paths if p not in all_rows]
    if missing:
        print(f"# missing: {missing}", file=sys.stderr)

    if out_file:
        with open(out_file, "w") as f:
            for p in paths:
                if p in all_rows:
                    d = all_rows[p]
                    f.write(f"{p}\t{d['name']}\t{d['type']}\t{d['origin']}\t{d['originroot']}\t{d['cls']}\n")
        print(f"wrote {len(all_rows)} rows to {out_file}", file=sys.stderr)

    print(json.dumps(list(all_rows.values()), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
