# -*- coding: utf-8 -*-
"""
TCP socket 客户端脚本：通过 socket 向本机指定端口发送数据，并接收、打印返回的数据。

功能概述
--------
1. 建立到指定 host:port 的 TCP 连接；
2. 将用户提供的文本（或二进制字面量）编码后作为请求负载发送；
3. 根据不同的“回复结束判定模式”（resp-mode）读取服务端返回的数据：
   - eof       : 服务端关闭连接（FIN）视为回复结束（默认）；
   - line      : 读到指定的换行/分隔符为止；
   - fixed     : 读取固定字节数；
   - delimiter : 读到指定分隔符为止；
4. 将收到的回复解码为文本打印到 stdout；若解码失败则原样写入 stdout 二进制流。

退出码约定
----------
  0 : 成功
  1 : 超时（在 --timeout 内未收到回复）
  2 : 无法建立连接（连接被拒 / 目标不存在等）
  3 : 收到回复前连接被提前关闭或发生其他 socket 错误

用法示例
--------
  # 默认 eof 模式：发送 "hello" 并等待服务端关闭连接
  python socket_client.py --port 9001 --data "hello"

  # 按行读取回复（服务端以换行结束回复）
  python socket_client.py --port 9002 --data "ping" --resp-mode line --resp-delimiter $'\n'

  # 读取固定 10 字节的回复
  python socket_client.py --port 9003 --data "ping" --resp-mode fixed --resp-fixed 10

  # 以自定义分隔符结束回复
  python socket_client.py --port 9004 --data "ping" --resp-mode delimiter --resp-delimiter "<END>"
"""

import argparse
import os
import socket
import sys


def recv_until(sock, delimiter, max_bytes=65536):
    """
    从 socket 持续读取数据，直到遇到指定的分隔符字节序列，或达到最大字节数上限。

    用于 --resp-mode=line / delimiter 两种模式：服务端不会主动关闭连接，
    而是以某个分隔符（如换行符）标识一条完整回复的结束。

    参数
    ----
    sock       : 已连接的 socket 对象。
    delimiter  : 分隔符字节串（bytes）。当接收缓冲区中出现该子串时停止读取。
    max_bytes  : 单次回复允许的最大字节数，防止服务端不发送分隔符时无限阻塞/膨胀。

    返回
    ----
    bytes : 读取到的原始字节（包含分隔符本身）。若连接提前关闭则返回已读到的部分。
    """
    buf = bytearray()
    # 只要缓冲区里还没出现分隔符、且未超过上限，就继续读
    while delimiter not in buf and len(buf) < max_bytes:
        chunk = sock.recv(4096)
        if not chunk:
            # recv 返回空字节串说明对端已关闭连接，停止读取
            break
        buf.extend(chunk)
    return bytes(buf)


def main():
    # ------------------------------------------------------------------
    # 1. 命令行参数解析
    # ------------------------------------------------------------------
    parser = argparse.ArgumentParser(description="TCP socket client: send to local port and print reply.")

    # 连接相关
    parser.add_argument("--host", default="127.0.0.1",
                        help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, required=True,
                        help="Server port")
    parser.add_argument("--timeout", type=float, default=10.0,
                        help="Socket timeout in seconds (default: 10)")

    # 数据/编码相关
    parser.add_argument("--data", required=True,
                        help="Data to send")
    parser.add_argument("--encoding", default="utf-8",
                        help="Text encoding (default: utf-8)")
    parser.add_argument("--binary", action="store_true",
                        help="Treat --data as bytes literal (Python escapes)")
    parser.add_argument("--send-delimiter", default="",
                        help="Append this delimiter to the outgoing payload")

    # 回复读取方式相关
    parser.add_argument("--resp-mode",
                        choices=["eof", "line", "fixed", "delimiter"], default="eof",
                        help="How to know the reply is complete")
    parser.add_argument("--resp-delimiter", default="",
                        help="Delimiter used when --resp-mode=line or delimiter")
    parser.add_argument("--resp-fixed", type=int, default=0,
                        help="Exact reply size in bytes when --resp-mode=fixed")
    args = parser.parse_args()

    # 回复读取方式的一致性校验：line/delimiter 必须给分隔符，fixed 必须给正数长度。
    # 否则 recv_until 会在空分隔符下立即返回空串，或 fixed 模式读到 0 字节。
    if args.resp_mode in ("line", "delimiter") and not args.resp_delimiter:
        parser.error("--resp-mode line/delimiter requires --resp-delimiter")
    if args.resp_mode == "fixed" and args.resp_fixed <= 0:
        parser.error("--resp-mode fixed requires --resp-fixed > 0")

    # ------------------------------------------------------------------
    # 2. 构造待发送的负载（payload）
    # ------------------------------------------------------------------
    if args.binary:
        # --binary 模式：把 --data 当作 Python 转义字节字面量解析。
        # 例如 '\x01\x02\x03' 会被转成真实的三个字节 0x01 0x02 0x03。
        # 实现上先用 latin-1（单字节映射，1:1 对应 0-255）编码为字节，
        # 再用 unicode_escape 解码还原 \xNN / \\ 等转义，最后重新编码回字节。
        payload = args.data.encode("latin-1").decode("unicode_escape").encode("latin-1")
    else:
        # 普通文本模式：按指定编码（默认 utf-8）编码为字节
        payload = args.data.encode(args.encoding)

    # 若指定了发送分隔符（如换行、回车换行等），追加到负载末尾
    if args.send_delimiter:
        payload += args.send_delimiter.encode(args.encoding)

    # ------------------------------------------------------------------
    # 3. 建立 TCP 连接
    # ------------------------------------------------------------------
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 设置超时，避免在连接或接收阶段无限阻塞
    sock.settimeout(args.timeout)
    try:
        sock.connect((args.host, args.port))
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        # 连接失败：目标端口未监听（拒绝）或网络不可达等情况
        msg = f"ERR: cannot connect to {args.host}:{args.port} -> {e}"
        # 容器内常见陷阱：127.0.0.1 指向容器自身，宿主机需用 host.docker.internal
        if (
            args.host in ("127.0.0.1", "localhost")
            and isinstance(e, ConnectionRefusedError)
            and os.path.exists("/.dockerenv")
        ):
            msg += (
                "\nHINT: running in a container? 127.0.0.1 points to the container itself;"
                " use --host host.docker.internal to reach the host machine."
            )
        print(msg, file=sys.stderr)
        return 2

    try:
        # 发送完整负载（sendall 会循环发送直到全部发出或出错）
        sock.sendall(payload)

        # ------------------------------------------------------------------
        # 4. 根据 resp-mode 读取回复
        # ------------------------------------------------------------------
        if args.resp_mode == "fixed":
            # 固定长度模式：精确读取 resp-fixed 字节
            buf = bytearray()
            while len(buf) < args.resp_fixed:
                # 每次只请求剩余尚未读满的字节数
                chunk = sock.recv(args.resp_fixed - len(buf))
                if not chunk:
                    # 对端提前关闭：停止读取，返回已读到的部分
                    break
                buf.extend(chunk)
            reply = bytes(buf)

        elif args.resp_mode in ("line", "delimiter"):
            # 行/分隔符模式：读取直到遇到指定分隔符
            delim = args.resp_delimiter.encode(args.encoding)
            reply = recv_until(sock, delim)

        else:  # eof（默认）
            # 读到对端关闭连接为止
            buf = bytearray()
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                buf.extend(chunk)
            reply = bytes(buf)

        # ------------------------------------------------------------------
        # 5. 输出回复内容
        # ------------------------------------------------------------------
        try:
            # 尝试按指定编码解码为文本并打印（print 会自动追加换行）
            print(reply.decode(args.encoding))
        except UnicodeDecodeError:
            # 解码失败说明是纯二进制数据：直接写入 stdout 的底层二进制流
            sys.stdout.buffer.write(reply)
            sys.stdout.buffer.flush()
        return 0

    except socket.timeout:
        # 在 --timeout 内未收到任何/足够的数据
        print(f"TIMEOUT: no reply within {args.timeout}s", file=sys.stderr)
        return 1
    except OSError as e:
        # 收到回复前连接被重置或发生其他 I/O 错误
        print(f"ERR: connection closed before reply -> {e}", file=sys.stderr)
        return 3
    finally:
        # 无论成功失败都确保关闭连接，释放资源
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            # 对端可能已经关闭，shutdown 会抛异常，忽略即可
            pass
        sock.close()


if __name__ == "__main__":
    # 以脚本退出码形式返回 main() 的结果
    sys.exit(main())
