# 写一个脚本，通过socket往本机的指定端口发送数据，并接收返回的数据。
import argparse
import socket
import sys


def recv_until(sock, delimiter, max_bytes=65536):
    """Read from sock until delimiter bytes are seen or max_bytes reached."""
    buf = bytearray()
    while delimiter not in buf and len(buf) < max_bytes:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf.extend(chunk)
    return bytes(buf)


def main():
    parser = argparse.ArgumentParser(description="TCP socket client: send to local port and print reply.")
    parser.add_argument("--host", default="127.0.0.1", help="Server host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, required=True, help="Server port")
    parser.add_argument("--data", required=True, help="Data to send")
    parser.add_argument("--timeout", type=float, default=10.0, help="Socket timeout in seconds (default: 10)")
    parser.add_argument("--encoding", default="utf-8", help="Text encoding (default: utf-8)")
    parser.add_argument("--binary", action="store_true", help="Treat --data as bytes literal (Python escapes)")
    parser.add_argument("--send-delimiter", default="", help="Append this delimiter to the outgoing payload")
    parser.add_argument("--resp-mode", choices=["eof", "line", "fixed", "delimiter"], default="eof",
                        help="How to know the reply is complete")
    parser.add_argument("--resp-delimiter", default="", help="Delimiter used when --resp-mode=delimiter")
    parser.add_argument("--resp-fixed", type=int, default=0, help="Exact reply size in bytes when --resp-mode=fixed")
    args = parser.parse_args()

    if args.binary:
        payload = args.data.encode("latin-1").decode("unicode_escape").encode("latin-1")
    else:
        payload = args.data.encode(args.encoding)
    if args.send_delimiter:
        payload += args.send_delimiter.encode(args.encoding)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(args.timeout)
    try:
        sock.connect((args.host, args.port))
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        print(f"ERR: cannot connect to {args.host}:{args.port} -> {e}", file=sys.stderr)
        return 2

    try:
        sock.sendall(payload)

        if args.resp_mode == "fixed":
            buf = bytearray()
            while len(buf) < args.resp_fixed:
                chunk = sock.recv(args.resp_fixed - len(buf))
                if not chunk:
                    break
                buf.extend(chunk)
            reply = bytes(buf)
        elif args.resp_mode in ("line", "delimiter"):
            delim = args.resp_delimiter.encode(args.encoding)
            reply = recv_until(sock, delim)
        else:  # eof
            buf = bytearray()
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                buf.extend(chunk)
            reply = bytes(buf)

        try:
            print(reply.decode(args.encoding))
        except UnicodeDecodeError:
            sys.stdout.buffer.write(reply)
            sys.stdout.buffer.flush()
        return 0
    except socket.timeout:
        print(f"TIMEOUT: no reply within {args.timeout}s", file=sys.stderr)
        return 1
    except OSError as e:
        print(f"ERR: connection closed before reply -> {e}", file=sys.stderr)
        return 3
    finally:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        sock.close()


if __name__ == "__main__":
    sys.exit(main())
