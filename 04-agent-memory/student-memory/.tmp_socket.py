"""Direct TCP socket client bypassing simtalk_send.py cp1252 trap."""
import socket, json, sys


def send_recv(payload, host="127.0.0.1", port=50007, timeout=20):
    s = socket.create_connection((host, port), timeout=timeout)
    s.sendall((json.dumps(payload) + "\n").encode("utf-8"))
    chunks = []
    while True:
        try:
            buf = s.recv(65536)
        except socket.timeout:
            break
        if not buf:
            break
        chunks.append(buf)
        # Heuristic: read until we've seen full JSON ending with "}\n"
        if b"}\n" in chunks[-1] or (chunks[-1].endswith(b"}\n")):
            break
    s.close()
    return b"".join(chunks)


def run_code(code, host="127.0.0.1", port=50007, timeout=20):
    payload = {"type": "simtalk_run", "code": code}
    raw = send_recv(payload, host, port, timeout)
    try:
        env = json.loads(raw.decode("utf-8"))
        return env
    except Exception as e:
        return {"raw": raw, "decode_err": str(e)}


def read_log(host="127.0.0.1", port=50007, timeout=10):
    payload = {"type": "readlog"}
    raw = send_recv(payload, host, port, timeout)
    try:
        env = json.loads(raw.decode("utf-8"))
        return env
    except Exception as e:
        return {"raw": raw[:500], "decode_err": str(e)}


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
    log = env.get("log", "")
    if "###CODE###" in log:
        print(log.split("###CODE###", 1)[1], end="")
    else:
        print(f"NO MARKER; log_first={log[:200]}", file=sys.stderr)
        sys.exit(1)