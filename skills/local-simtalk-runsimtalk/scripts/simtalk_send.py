#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simtalk_send.py — simtalk_run 专用：真跑 SimTalk，会改变模型状态。

仅暴露 run 子命令。其它动词用对应技能：
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

参考：references/lifelines.md §1-9
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


def cmd_run(args):
    payload = {
        "type": "simtalk_run",
        "action_id": uuid.uuid4().hex,
        "simtalk_code": args.code,
    }
    if args.context_path:
        payload["context_path"] = args.context_path
    if args.return_value:
        # 注意：实测无效（Quirk #6），data 字段永远不出现。
        payload["return_value"] = True

    code, reply = _run_socket_client(args.host, args.port, args.timeout, payload)
    print(reply)
    if code != 0:
        # socket 层错误（连接拒/超时/协议错）——stderr 留痕，按"编译错"处理
        # （exit 10）。让调用方拿到稳定 exit code 而不是静默的 1 + 空 stdout。
        print(
            f"[simtalk_send.cmd_run] socket error: code={code} reply={reply!r}",
            file=sys.stderr,
        )
        return 10

    try:
        resp = json.loads(reply)
    except json.JSONDecodeError:
        # JSON 解析错 / 字段缺失：服务端走裸字符串路径（lifelines.md §6）
        return 12

    result = resp.get("result", "")
    log = resp.get("log", "")

    # 双重判据（Quirk #7，lifelines.md §6）
    if result != "success":
        return 10
    if log.startswith("code execute failed"):
        # Quirk #7 软失败——用户主动设计，不要"修复"服务端（lifelines.md §6）
        return 11
    return 0


def main():
    # Windows 默认 cp1252 在 epilog 含中文时会 stack trace；reconfigure 到 utf-8
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(
        description="Plant Simulation simtalk_run — 真跑 SimTalk，会改变模型状态。",
    )
    parser.add_argument("--host", default=DEFAULT_HOST,
                        help=f"Server host (default: {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"Server port (default: {DEFAULT_PORT})")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help=f"Socket timeout in seconds (default: {DEFAULT_TIMEOUT})")
    parser.add_argument("code", help="SimTalk 代码字符串")
    parser.add_argument("--context-path", default=None,
                        help="执行上下文，例如 path.to.Machine")
    parser.add_argument("--return-value", action="store_true",
                        help="尝试让服务端回传 return 值（⚠️ Quirk #6 实测无效）")
    args = parser.parse_args()
    return cmd_run(args)


if __name__ == "__main__":
    sys.exit(main())