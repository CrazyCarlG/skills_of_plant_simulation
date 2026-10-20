#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simtalk_readlog.py — readlog 专用：拉取 GUI Console 输出。

仅暴露 readlog 子命令。其它动词用对应技能：
  ping    -> local-simtalk-ping
  syntax  -> local-simtalk-checksyntax
  run     -> local-simtalk-runsimtalk
  readlog -> 本技能

用法示例：
    python simtalk_readlog.py
    python simtalk_readlog.py --host 127.0.0.1 --port 50007 --timeout 10

参数说明：
    --host     SocketServer 地址，默认 host.docker.internal
    --port     SocketServer 端口，默认 50007
    --timeout  等待响应的秒数，默认 30；超时返回退出码 1

注意：v15+ 服务端的 readlog 内容不可信，仅适合一次性调试，不要放入自动化循环。
退出码 20 表示已收到并输出回包，但内容可能是陈旧日志或不完整数据；请勿丢弃 stdout。

退出码：
  0  拉取成功（但内容不可信）
  20 readlog 
  10 result≠success
  1  socket 超时
  2  cannot connect
  3  连接中途断开 / 回包非 JSON
"""

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
    """Send one readlog request and receive its delimiter-terminated reply."""
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


def cmd_readlog(args):


    payload = {
        "type": "readlog",
        "action_id": uuid.uuid4().hex,
    }
    code, reply = _send_and_recv(args.host, args.port, args.timeout, payload)
    print(reply)
    if code != 0:
        return code

    try:
        resp = json.loads(reply)
    except json.JSONDecodeError:
        return 20

    # 服务端对 readlog 把内容放在 log 字段，result 恒为空串——
    # 所以不能只认 result == "success"，否则成功的读取会被判成失败。
    if resp.get("result") == "success" or "log" in resp:
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
        description="Plant Simulation readlog — 拉取 GUI Console 输出。",
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