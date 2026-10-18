#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simtalk_send.py — readlog 专用：拉取 GUI Console 输出。

仅暴露 readlog 子命令。其它动词用对应技能：
  ping    -> local-simtalk-ping
  syntax  -> local-simtalk-checksyntax
  run     -> local-simtalk-runsimtalk
  readlog -> 本技能

⚠️ v15+ 已回归 v12 反馈循环模式——不可信，仅供一次性调试。
详见 references/lifelines.md §5 / Q-002。

退出码：
  0  拉取成功（但内容不可信）
  20 readlog 不可信警告（v15+，stdout 仍携带完整 log 内容，视为读取成功）
  10 result≠success
  1  socket 超时
  2  cannot connect
  3  连接中途断开 / 回包非 JSON
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


def cmd_readlog(args):
    print(
        "⚠️  v15+ readlog 已回归 v12 反馈循环模式——不可信，仅供一次性调试。"
        "详见 references/lifelines.md §5。",
        file=sys.stderr,
    )

    payload = {
        "type": "readlog",
        "action_id": uuid.uuid4().hex,
    }
    code, reply = _run_socket_client(args.host, args.port, args.timeout, payload)
    print(reply)
    if code != 0:
        return code

    try:
        resp = json.loads(reply)
    except json.JSONDecodeError:
        # readlog 在某些异常路径下也可能回裸字符串
        return 20

    if resp.get("result") == "success":
        # ⚠️ 语义"成功"——但 v15+ 内容不可信（lifelines.md §5）
        return 20
    return 10


def main():
    # Windows 默认 cp1252 在 epilog 含中文时会 stack trace；reconfigure 到 utf-8
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(
        description="Plant Simulation readlog — 拉取 GUI Console 输出（⚠️ v15+ 不可信）。",
    )
    parser.add_argument("--host", default=DEFAULT_HOST,
                        help=f"Server host (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"Server port (default: {DEFAULT_PORT})")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help=f"Socket timeout in seconds (default: {DEFAULT_TIMEOUT})")
    args = parser.parse_args()
    return cmd_readlog(args)


if __name__ == "__main__":
    sys.exit(main())