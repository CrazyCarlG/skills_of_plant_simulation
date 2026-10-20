#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simtalk_send.py — simtalk_syntax 专用：仅做 SimTalk 语法/编译检查。

仅暴露 syntax 子命令。其它动词用对应技能：
  ping    -> local-simtalk-ping
  syntax  -> 本技能
  run     -> local-simtalk-runsimtalk
  readlog -> local-simtalk-readlog

退出码：
  0  语法通过（"hasError" not in result）
  12 语法失败（result 含 "hasError" 或 socket 错）
  1  socket 超时
  2  cannot connect
  3  连接中途断开 / 回包非 JSON

参考：references/lifelines.md §1-3 / §6 / §9
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
    """TCP 往返一次。返回 (exit_code, reply_text)。"""
    data = (json.dumps(payload_json, ensure_ascii=False) + END_DELIM).encode("utf-8")
    delim = END_DELIM.encode("utf-8")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((host, port))
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        return 2, f"ERR: cannot connect to {host}:{port} -> {e}"
    try:
        sock.sendall(data)
        buf = bytearray()
        while delim not in buf:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buf.extend(chunk)
        reply = buf.decode("utf-8", errors="replace")
        if reply.endswith(END_DELIM):
            reply = reply[: -len(END_DELIM)]
        return 0, reply
    except socket.timeout:
        return 1, f"TIMEOUT: no reply within {timeout}s"
    except OSError as e:
        return 3, f"ERR: connection closed before reply -> {e}"
    finally:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        sock.close()


def cmd_syntax(args):
    payload = {
        "type": "simtalk_syntax",
        "action_id": uuid.uuid4().hex,
        "simtalk_code": args.code,
    }
    if args.target_path:
        payload["target_path"] = args.target_path

    code, reply = _send_and_recv(args.host, args.port, args.timeout, payload)
    print(reply)
    if code != 0:
        # socket 层错误（连接拒/超时/协议错）——stderr 留痕，按"语法失败"处理
        # （exit 12）。让调用方拿到稳定 exit code 而不是静默的 1 + 空 stdout。
        print(
            f"[simtalk_send.cmd_syntax] socket error: code={code} reply={reply!r}",
            file=sys.stderr,
        )
        return 12

    try:
        resp = json.loads(reply)
    except json.JSONDecodeError:
        # 服务端对坏 JSON / 字段缺失回裸字符串（lifelines.md §6 异常抛出矩阵）
        # reply 已经打到 stdout
        return 12

    result = resp.get("result", "")
    if "hasError" in result:
        return 12
    return 0


def main():
    # Windows 默认 cp1252 在 epilog 含中文时会 stack trace；reconfigure 到 utf-8
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(
        description="Plant Simulation simtalk_syntax — 仅做 SimTalk 语法/编译检查。",
    )
    parser.add_argument("--host", default=DEFAULT_HOST,
                        help=f"Server host (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"Server port (default: {DEFAULT_PORT})")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help=f"Socket timeout in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("code", help="SimTalk 代码字符串")
    parser.add_argument("--target-path", default=None,
                        help="限定到某个对象做解析，例如 .Models.Model.m")
    args = parser.parse_args()
    return cmd_syntax(args)


if __name__ == "__main__":
    sys.exit(main())