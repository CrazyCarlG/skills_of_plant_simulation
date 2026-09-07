"""Direct TCP socket client - bypass simtalk_send.py cp1252 trap."""
import socket, json, sys, uuid


END_DELIM = "||END||"


def send_recv(payload, host="127.0.0.1", port=50007, timeout=30):
    s = socket.create_connection((host, port), timeout=timeout)
    msg = json.dumps(payload, ensure_ascii=False) + END_DELIM
    s.sendall(msg.encode("utf-8"))
    # read until ||END||
    buf = bytearray()
    s.settimeout(timeout)
    while True:
        try:
            chunk = s.recv(65536)
        except socket.timeout:
            break
        if not chunk:
            break
        buf.extend(chunk)
        if END_DELIM.encode("utf-8") in buf:
            break
    s.close()
    # strip delimiter
    if buf.endswith(END_DELIM.encode("utf-8")):
        buf = buf[: -len(END_DELIM)]
    return bytes(buf)


def run_code(code, host="127.0.0.1", port=50007, timeout=30):
    payload = {
        "type": "simtalk_run",
        "action_id": uuid.uuid4().hex,
        "simtalk_code": code,
    }
    raw = send_recv(payload, host, port, timeout)
    try:
        env = json.loads(raw.decode("utf-8"))
        return env
    except Exception as e:
        return {"_raw": raw, "_decode_err": str(e)}


def read_log(host="127.0.0.1", port=50007, timeout=10):
    payload = {"type": "readlog", "action_id": uuid.uuid4().hex}
    raw = send_recv(payload, host, port, timeout)
    try:
        env = json.loads(raw.decode("utf-8"))
        return env
    except Exception as e:
        return {"_raw": raw, "_decode_err": str(e)}


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "SimHandler"
    code = f'''
var pm: object := str_to_obj(".Models.Example.GA.{target}")
if pm = void
  print "###VOID###"
  return
end
print "###CODE###"
print pm.PythonCode
'''
    env = run_code(code)
    if "_raw" in env:
        print(f"RAW: {env['_raw'][:300]}", file=sys.stderr)
        sys.exit(1)
    log = env.get("log", "")
    if "###CODE###" in log:
        print(log.split("###CODE###", 1)[1], end="")
    else:
        print(f"NO MARKER; log={log[:300]}", file=sys.stderr)
        sys.exit(1)