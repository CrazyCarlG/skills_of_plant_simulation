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


def cmd_syntax(args):
    payload = {
        "type": "simtalk_syntax",
        "action_id": uuid.uuid4().hex,
        "simtalk_code": args.code,
    }
    if args.target_path:
        payload["target_path"] = args.target_path

    code, reply = _run_socket_client(args.host, args.port, args.timeout, payload)
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