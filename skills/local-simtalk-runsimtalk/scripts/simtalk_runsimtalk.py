#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simtalk_send.py — 真跑 SimTalk，会改变模型状态。

仅暴露 run 动词。其它动词用对应技能：
  ping    -> local-simtalk-ping
  syntax  -> local-simtalk-checksyntax
  run     -> 本技能
  readlog -> local-simtalk-readlog

退出码：
  0  语义成功（result=="success" AND log 不以 "code execute failed" 开头）
  10 编译错 / result≠success
  11 Quirk #7 软失败（result==success 但 log 前缀 "code execute failed"）
  12 回包非 JSON
  1  socket 超时
  2  cannot connect
  3  连接中途断开
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


def cmd_run(args):
    payload = {
        "type": "simtalk_run",
        "action_id": uuid.uuid4().hex,
        "simtalk_code": args.code,
    }
    code, reply = _send_and_recv(args.host, args.port, args.timeout, payload)
    print(reply)
    if code != 0:
        print(f"[simtalk_send.cmd_run] socket error: code={code}", file=sys.stderr)
        return 10  # socket 层错误按"编译错"处理，让调用方拿到稳定 exit code
    try:
        resp = json.loads(reply)
    except json.JSONDecodeError:
        return 12  # 服务端走裸字符串路径（schema 违规）

    result = resp.get("result", "")
    log = resp.get("log", "")
    if result != "success":
        return 10
    if log.startswith("code execute failed"):
        # Quirk #7 软失败——用户主动设计，不要"修复"服务端
        return 11
    return 0


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(
        description="Plant Simulation simtalk_run — 真跑 SimTalk，会改变模型状态。",
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    parser.add_argument("code", help="SimTalk 代码字符串")
    args = parser.parse_args()
    return cmd_run(args)


if __name__ == "__main__":
    sys.exit(main())