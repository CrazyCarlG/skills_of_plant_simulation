#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simtalk_send.py — ping 专用：连通性检查。

仅暴露 ping 子命令。其它动词用对应技能：
  ping    -> 本技能
  syntax  -> local-simtalk-checksyntax
  run     -> local-simtalk-runsimtalk
  readlog -> local-simtalk-readlog

退出码：
  0  ping 成功（type=="ping" AND result=="success"）
  1  socket 超时
  2  cannot connect
  3  连接中途断开 / 回包非 JSON
  10 ping 未成功（回包合法但 result≠success）

参考：references/lifelines.md §1-3 / §6 / §9
"""

import argparse
import json
import os
import subprocess
import sys
import uuid

SOCKET_CLIENT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "socket_client.py")
END_DELIM = "||END||"
DEFAULT_HOST = "host.docker.internal"
DEFAULT_PORT = 50007
DEFAULT_TIMEOUT = 30.0


def _run_socket_client(host, port, timeout, json_payload):
    payload = json.dumps(json_payload, ensure_ascii=False) + END_DELIM
    cmd = [
        sys.executable, SOCKET_CLIENT_PATH,
        "--host", host,
        "--port", str(port),
        "--timeout", str(timeout),
        "--data", payload,
        "--resp-mode", "delimiter",
        "--resp-delimiter", END_DELIM,
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 5.0)
    except subprocess.TimeoutExpired:
        return 1, "TIMEOUT: socket_client.py 子进程超时"
    reply = proc.stdout.rstrip("\n")
    if reply.endswith(END_DELIM):
        reply = reply[: -len(END_DELIM)]
    return proc.returncode, reply


def cmd_ping(args):
    payload = {"type": "ping", "timestamp": uuid.uuid4().hex}
    code, reply = _run_socket_client(args.host, args.port, args.timeout, payload)
    print(reply)
    if code != 0:
        return code
    try:
        resp = json.loads(reply)
    except json.JSONDecodeError:
        print("ERR: 服务端回包不是合法 JSON", file=sys.stderr)
        return 3
    if resp.get("type") == "ping" and resp.get("result") == "success":
        return 0
    print(f"ERR: ping 未成功 (回包: {resp})", file=sys.stderr)
    return 10


def main():
    # Windows 默认 cp1252 在 epilog 含中文时会 stack trace；reconfigure 到 utf-8
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(
        description="Plant Simulation ping — 通过 TCP 检查 SocketServer 是否可达。",
    )
    parser.add_argument("--host", default=DEFAULT_HOST,
                        help=f"Server host (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"Server port (default: {DEFAULT_PORT})")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help=f"Socket timeout in seconds (default: {DEFAULT_TIMEOUT})")
    args = parser.parse_args()
    return cmd_ping(args)


if __name__ == "__main__":
    sys.exit(main())