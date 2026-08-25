#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simtalk_send.py — 高层封装：自动生成 action_id + 默认参数 + Quirk 判据。

为什么需要它：
  `scripts/socket_client.py` 是底层一次性 TCP 客户端——每次调用都要手写：
    - JSON payload（包含 `type` / `action_id` / `simtalk_code` 等字段）
    - `||END||` 帧分隔符
    - `--resp-mode delimiter --resp-delimiter '||END||'`（lifelines.md §2）
    - Quirk #6 / #7 双重判据（lifelines.md §6）

  `simtalk_send.py` 把上面这些"每次都要做的事"封装成子命令 + 退出码语义，
  让 `local-simtalk-execution` 技能的调用方少写 boilerplate、少踩坑。

支持的子命令：
  ping       连通性检查（lifelines.md §6）
  syntax     simtalk_syntax：仅做语法检查（lifelines.md §6）
  run        simtalk_run：实际执行（lifelines.md §6 双重判据）
  readlog    拉取 readlog（⚠️ v15+ 已回归，详见 lifelines.md §5）

默认行为（可在 CLI 覆盖）：
  --host host.docker.internal   （WSL2 → 主机，详见 lifelines.md §1）
  --port 50007                  （Plant Simulation 默认端口）
  --timeout 30                  （simtalk_run 跑长任务时再加大）
  --resp-mode delimiter          （eof 模式在当前协议下一定超时，详见 lifelines.md §2）
  --resp-delimiter '||END||'
  --send-delimiter '||END||'

type 字段白名单（Quirk #13，详见 lifelines.md §3）：
  ping / simtalk_syntax / simtalk_run / readlog
  其它任何值会让服务端静默挂死到 timeout——本脚本只允许这四个值。

退出码（与 socket_client.py 一致 + 扩展）：
  0  socket 收到完整回复（语义成功需看 --success-only 与子命令的 stdout）
  1  超时
  2  无法建立连接
  3  连接中途断开
  10 simtalk_run 语义失败（result != "success"）
  11 simtalk_run Quirk #7 软失败（result == "success" 但 log 以 "code execute failed" 开头）
  12 simtalk_syntax 语法失败（result 含 "hasError"）
  20 readlog 不可信警告（v15+，仍会把内容打到 stdout）

参考：
  - references/lifelines.md §1-9（所有硬规则的唯一事实来源）
  - scripts/socket_client.py（底层客户端）
"""

import argparse
import json
import os
import socket
import subprocess
import sys
import uuid


SOCKET_CLIENT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "socket_client.py")

# Quirk #13 白名单（详见 lifelines.md §3）
VALID_TYPES = {"ping", "simtalk_syntax", "simtalk_run", "readlog"}

# 帧分隔符（详见 lifelines.md §2）
END_DELIM = "||END||"

# 默认连接目标（详见 lifelines.md §1）
DEFAULT_HOST = "host.docker.internal"
DEFAULT_PORT = 50007
DEFAULT_TIMEOUT = 30.0


def _build_socket_client_cmd(host, port, timeout, payload_str):
    """
    构造 socket_client.py 的命令行参数（以 list 形式返回）。

    payload_str : 已包含 ||END|| 帧分隔符的 str（socket_client.py 内部按 utf-8 编码）
    """
    return [
        sys.executable,
        SOCKET_CLIENT_PATH,
        "--host", host,
        "--port", str(port),
        "--timeout", str(timeout),
        "--data", payload_str,
        "--resp-mode", "delimiter",
        "--resp-delimiter", END_DELIM,
    ]


def _run_socket_client(host, port, timeout, json_payload):
    """
    通过 subprocess 调用底层 socket_client.py，返回 (exit_code, reply_text)。

    退出码 0=成功（socket 收到 ||END|| 帧）、1=超时、2=连接错、3=中途断开。
    """
    # 自动追加 ||END|| 帧（详见 lifelines.md §2）
    payload = json.dumps(json_payload, ensure_ascii=False) + END_DELIM
    cmd = _build_socket_client_cmd(host, port, timeout, payload)
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout + 5.0,  # 多给 5s 给 subprocess 启动开销
        )
    except subprocess.TimeoutExpired:
        return 1, "TIMEOUT: socket_client.py 子进程超时"
    # socket_client.py 把 ||END|| 也写到 stdout——剥离后再返回
    reply = proc.stdout.rstrip("\n")
    if reply.endswith(END_DELIM):
        reply = reply[: -len(END_DELIM)]
    return proc.returncode, reply


def cmd_ping(args):
    """
    ping 子命令：连通性检查（lifelines.md §6）。

    成功判据：type == "ping" AND result == "success"。
    """
    payload = {"type": "ping", "timestamp": uuid.uuid4().hex}
    code, reply = _run_socket_client(args.host, args.port, args.timeout, payload)
    print(reply)
    if code != 0:
        return code
    # 解析回包
    try:
        resp = json.loads(reply)
    except json.JSONDecodeError:
        print("ERR: 服务端回包不是合法 JSON", file=sys.stderr)
        return 3
    if resp.get("type") == "ping" and resp.get("result") == "success":
        return 0
    print(f"ERR: ping 未成功 (回包: {resp})", file=sys.stderr)
    return 10


def cmd_syntax(args):
    """
    simtalk_syntax 子命令：仅做语法检查（lifelines.md §6）。

    成功判据："hasError" not in result。
    退出码 12 = 语法失败。
    """
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
        return code

    try:
        resp = json.loads(reply)
    except json.JSONDecodeError:
        # 服务端对坏 JSON / 字段缺失回裸字符串（lifelines.md §6 异常抛出矩阵）
        # 这是 schema 违规或 JSON 解析失败的正常路径——不要当成 socket_client 错
        # reply 已经是裸字符串错误描述，已通过 print 打到 stdout
        return 12

    result = resp.get("result", "")
    if "hasError" in result:
        return 12
    return 0


def cmd_run(args):
    """
    simtalk_run 子命令：实际执行 SimTalk（lifelines.md §6 双重判据）。

    双重判据：result == "success" AND not log.startswith("code execute failed")
      - 退出码 10 = 编译错或 result != "success"
      - 退出码 11 = Quirk #7 软失败（runtime 异常，result=success 但 log 前缀 code execute failed）

    永远忽略 data 字段（Quirk #6，lifelines.md §6）。
    """
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
        return code

    try:
        resp = json.loads(reply)
    except json.JSONDecodeError:
        # JSON 解析错 / 字段缺失：服务端走裸字符串路径（lifelines.md §6）
        # reply 已经打到 stdout
        return 12

    result = resp.get("result", "")
    log = resp.get("log", "")

    # 双重判据（Quirk #7，lifelines.md §6）
    if result != "success":
        # 编译错（result="failed"）或 result="timeout"
        return 10
    if log.startswith("code execute failed"):
        # Quirk #7 软失败——用户主动设计，不要"修复"服务端（lifelines.md §6 / team memory）
        return 11
    # 真正的语义成功
    return 0


def cmd_readlog(args):
    """
    readlog 子命令：拉取 GUI Console 输出（⚠️ v15+ 已回归，详见 lifelines.md §5）。

    v15+ 行为：buffer 会把上一条 readlog 的响应嵌套回自己，造成体积指数膨胀；
    同时捕获不到 print(...) 输出。

    本子命令仍然发出请求，但在 stderr 打一个警告，并把退出码设为 20。
    """
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
    parser = argparse.ArgumentParser(
        description=(
            "simtalk_send.py — Plant Simulation SimTalk 高层发送器。"
            " 所有硬规则见 references/lifelines.md。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    # 全局连接参数（子命令共享默认值）
    parser.add_argument("--host", default=DEFAULT_HOST,
                        help=f"Server host (default: {DEFAULT_HOST}，详见 lifelines.md §1)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"Server port (default: {DEFAULT_PORT})")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help=f"Socket timeout in seconds (default: {DEFAULT_TIMEOUT})")

    subparsers = parser.add_subparsers(dest="subcommand", required=True,
                                       help="子命令（type 字段对应；白名单约束详见 lifelines.md §3）")

    # ping
    p_ping = subparsers.add_parser("ping", help="连通性检查")
    p_ping.set_defaults(func=cmd_ping)

    # syntax
    p_syn = subparsers.add_parser("syntax", help="simtalk_syntax：仅做语法检查")
    p_syn.add_argument("code", help="SimTalk 代码字符串")
    p_syn.add_argument("--target-path", default=None,
                       help="限定到某个对象做解析，例如 .Models.Model.m")
    p_syn.set_defaults(func=cmd_syntax)

    # run
    p_run = subparsers.add_parser("run", help="simtalk_run：实际执行 SimTalk")
    p_run.add_argument("code", help="SimTalk 代码字符串")
    p_run.add_argument("--context-path", default=None,
                       help="执行上下文，例如 path.to.Machine")
    p_run.add_argument("--return-value", action="store_true",
                       help="尝试让服务端回传 return 值（⚠️ Quirk #6 实测无效）")
    p_run.set_defaults(func=cmd_run)

    # readlog
    p_rl = subparsers.add_parser("readlog",
                                 help="readlog：拉取 GUI Console 输出（⚠️ v15+ 不可信）")
    p_rl.set_defaults(func=cmd_readlog)

    args = parser.parse_args()

    # type 白名单校验（Quirk #13，详见 lifelines.md §3）
    type_map = {
        "ping": "ping",
        "syntax": "simtalk_syntax",
        "run": "simtalk_run",
        "readlog": "readlog",
    }
    if args.subcommand not in type_map:
        parser.error(f"未知子命令 {args.subcommand}（白名单：{sorted(VALID_TYPES)}）")
    # type_map 的键必然是白名单的子集——上面这一行实际上是双重保险

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())