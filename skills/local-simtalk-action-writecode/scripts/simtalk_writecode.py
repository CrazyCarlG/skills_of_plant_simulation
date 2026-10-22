#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# simtalk_writecode.py：将 SimTalk 代码写入指定方法。
# 使用方法（在仓库根目录运行）：
#   python skills/local-simtalk-action-writecode/scripts/simtalk_writecode.py --targetmethodpath "Models.Line1.Method" --code "print('hello')"
# --targetmethodpath 和 --code 必填；--code 可包含多行代码。
# 可选连接参数：--host（默认 127.0.0.1）、--port（默认 50007）、--timeout（默认 30 秒）。
# 示例：python skills/local-simtalk-action-writecode/scripts/simtalk_writecode.py --targetmethodpath "Models.Line1.Method" --code "print('hello')" --host 127.0.0.1 --port 50007

import argparse
import json
import socket
import sys
import uuid

END_DELIM = "||END||"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 50007
DEFAULT_TIMEOUT = 30.0


def _send_and_recv(host, port, timeout, payload_json):
    """Send one request and receive its delimiter-terminated reply."""
    data = (json.dumps(payload_json, ensure_ascii=False) + END_DELIM).encode("utf-8")
    delimiter = END_DELIM.encode("utf-8")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
    except (socket.timeout, ConnectionRefusedError, OSError) as exc:
        sock.close()
        return 2, f"ERR: cannot connect to {host}:{port} -> {exc}"

    try:
        sock.sendall(data)
        buffer = bytearray()
        while delimiter not in buffer:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buffer.extend(chunk)
        reply = buffer.decode("utf-8", errors="replace")
        if reply.endswith(END_DELIM):
            reply = reply[:-len(END_DELIM)]
        return 0, reply
    except socket.timeout:
        return 1, f"TIMEOUT: no reply within {timeout}s"
    except OSError as exc:
        return 3, f"ERR: connection closed before reply -> {exc}"
    finally:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        sock.close()


def cmd_writecode(args):
    payload = {
        "type": "writecode",
        "action_id": uuid.uuid4().hex,
        "targetmethodpath": args.targetmethodpath,
        "code": args.code
    }
    code, reply = _send_and_recv(args.host, args.port, args.timeout, payload)
    print(reply)
    if code != 0:
        return code

    try:
        resp = json.loads(reply)
    except json.JSONDecodeError:
        return 20

    if resp.get("status") == "success":
        return 0
    return 10


def main():
    # Windows 默认 cp1252 在 epilog 含中文时会 stack trace；reconfigure 到 utf-8
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(
        description="Plant Simulation writecode — 将 SimTalk 代码写入指定方法。",
    )
    parser.add_argument("--targetmethodpath", required=True,
                        help="Target method path to receive the code")
    parser.add_argument("--code", required=True,
                        help="SimTalk code to write; may contain multiple lines")
    parser.add_argument("--host", default=DEFAULT_HOST,
                        help=f"Server host (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"Server port (default: {DEFAULT_PORT})")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help=f"Socket timeout in seconds (default: {DEFAULT_TIMEOUT})")
    args = parser.parse_args()
    return cmd_writecode(args)


if __name__ == "__main__":
    sys.exit(main())