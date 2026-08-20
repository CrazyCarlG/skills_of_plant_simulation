#!/usr/bin/env python3
"""
simtalk-connector — 一个保持长连接的 TCP socket 客户端，一问一答（request/response）。

Maintains a persistent connection to a remote TCP server. Every `send` blocks
until the server replies (with a timeout), so the caller always gets a reply.

    python3 connector.py send "some data"    # 发送并等待服务器回复

How it works:
  - `start`  launches a daemon that keeps a TCP connection to the remote server
    open (auto-reconnect on drop) and listens on a local Unix socket.
  - `send`   connects to the local socket, forwards the payload, waits for the
    server's reply, and prints the reply. Blocking + timeout.
  - `stop`   stops the daemon.
  - `status` reports whether the daemon is running.

Response framing (how a "reply" is delimited), configured at start time via
`--resp-mode`:
  - line  (default): read until the delimiter string (default ||END||,
                     configurable via --resp-delimiter).
  - idle : read until the server is silent for `--resp-idle` seconds.
  - fixed: read exactly `--resp-length` bytes.

Local IPC:
  - Request  (client -> daemon): length-prefixed JSON meta, then
                                  length-prefixed payload bytes.
  - Response (daemon -> client): 1 status byte (0 ok / 1 timeout / 2 error),
                                  then length-prefixed message bytes.

Examples:
  python3 connector.py start --host 127.0.0.1 --port 9000 --daemon
  python3 connector.py send '{"cmd": "ping"}'          # wait for reply (default 10s)
  python3 connector.py send 'run SimTalk' --timeout 5  # 5s timeout for this call
  python3 connector.py status
  python3 connector.py stop
"""

import argparse
import json
import os
import signal
import socket
import struct
import sys
import threading
import time
from pathlib import Path

DEFAULT_NAME = "default"
DEFAULT_RUNTIME_DIR = Path.home() / ".cache" / "simtalk-connector"
HEADER = struct.Struct("!I")
MAX_FRAME_BYTES = 64 * 1024 * 1024  # 64 MiB safety cap


# --------------------------------------------------------------------------- #
# Logging
# --------------------------------------------------------------------------- #

def _log(msg: str) -> None:
    """Log to stderr. When daemonized, stderr is redirected to the log file."""
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}", file=sys.stderr, flush=True)


# --------------------------------------------------------------------------- #
# Runtime paths / pid helpers
# --------------------------------------------------------------------------- #

def _runtime_dir() -> Path:
    return Path(os.environ.get("SIMTALK_CONNECTOR_DIR", str(DEFAULT_RUNTIME_DIR)))


def _socket_path(name: str) -> Path:
    return _runtime_dir() / f"{name}.sock"


def _pid_path(name: str) -> Path:
    return _runtime_dir() / f"{name}.pid"


def _log_path(name: str) -> Path:
    return _runtime_dir() / f"{name}.log"


def _read_pid(name: str):
    p = _pid_path(name)
    if not p.exists():
        return None
    try:
        return int(p.read_text().strip())
    except (ValueError, OSError):
        return None


def _pid_alive(pid) -> bool:
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


# --------------------------------------------------------------------------- #
# Local IPC framing (Unix domain socket)
# --------------------------------------------------------------------------- #

def _send_frame(sock: socket.socket, data: bytes) -> None:
    sock.sendall(HEADER.pack(len(data)))
    sock.sendall(data)


def _recv_exact(sock: socket.socket, n: int) -> bytes:
    buf = bytearray()
    while len(buf) < n:
        chunk = sock.recv(n - len(buf))
        if not chunk:
            raise ConnectionError("local peer closed connection mid-frame")
        buf.extend(chunk)
    return bytes(buf)


def _recv_frame(sock: socket.socket) -> bytes:
    (n,) = HEADER.unpack(_recv_exact(sock, HEADER.size))
    if n > MAX_FRAME_BYTES:
        raise ValueError(f"frame too large: {n} bytes")
    return _recv_exact(sock, n)


# --------------------------------------------------------------------------- #
# Persistent remote connection (request/response, auto-reconnect)
# --------------------------------------------------------------------------- #

class Remote:
    """A single TCP connection to the remote server, guarded by a reentrant lock.

    The lock serializes requests so that at most one question is in flight at a
    time, which keeps request/response correlation trivial on a single socket.
    """

    def __init__(self, host, port, reconnect_delay, newline, resp_mode,
                 resp_idle, resp_length, default_timeout, delimiter):
        self.host = host
        self.port = port
        self.reconnect_delay = reconnect_delay
        self.newline = newline
        self.resp_mode = resp_mode
        self.resp_idle = resp_idle
        self.resp_length = resp_length
        self.default_timeout = default_timeout
        self.delimiter = delimiter
        self.lock = threading.RLock()
        self.sock: socket.socket | None = None
        self._rbuf = b""  # leftover bytes from a previous read

    def _connect(self) -> socket.socket:
        _log(f"connecting to {self.host}:{self.port}")
        s = socket.create_connection((self.host, self.port))
        _log(f"connected to {self.host}:{self.port}")
        return s

    def _close(self) -> None:
        with self.lock:
            if self.sock is not None:
                try:
                    self.sock.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                try:
                    self.sock.close()
                except OSError:
                    pass
                self.sock = None

    def ensure(self) -> socket.socket:
        with self.lock:
            if self.sock is None:
                self.sock = self._connect()
            return self.sock

    def _recv(self, sock: socket.socket, deadline: float, max_wait=None) -> bytes:
        rem = deadline - time.monotonic()
        if rem <= 0:
            raise TimeoutError()
        wait = rem if max_wait is None else min(rem, max_wait)
        sock.settimeout(wait)
        return sock.recv(65536)

    def _read_response(self, sock: socket.socket, timeout: float):
        """Read one reply. Returns (status, bytes) where status is
        'ok' | 'timeout' | 'error'."""
        deadline = time.monotonic() + timeout

        if self.resp_mode == "line":
            delim = self.delimiter
            while True:
                i = self._rbuf.find(delim)
                if i >= 0:
                    line = self._rbuf[:i]
                    self._rbuf = self._rbuf[i + len(delim):]
                    return "ok", line
                try:
                    chunk = self._recv(sock, deadline)
                except TimeoutError:
                    if self._rbuf:
                        line, self._rbuf = self._rbuf, b""
                        return "ok", line
                    return "timeout", b"no reply within timeout"
                except OSError as e:
                    return "error", str(e).encode()
                if not chunk:
                    if self._rbuf:
                        line, self._rbuf = self._rbuf, b""
                        return "ok", line
                    return "error", b"connection closed before reply"
                self._rbuf += chunk

        elif self.resp_mode == "idle":
            while True:
                try:
                    chunk = self._recv(sock, deadline, self.resp_idle)
                except TimeoutError:
                    if self._rbuf:
                        data, self._rbuf = self._rbuf, b""
                        return "ok", data
                    return "timeout", b"no reply within timeout"
                except OSError as e:
                    return "error", str(e).encode()
                if not chunk:
                    if self._rbuf:
                        data, self._rbuf = self._rbuf, b""
                        return "ok", data
                    return "error", b"connection closed before reply"
                self._rbuf += chunk

        else:  # fixed
            while len(self._rbuf) < self.resp_length:
                try:
                    chunk = self._recv(sock, deadline)
                except TimeoutError:
                    return "timeout", b"incomplete fixed-length reply"
                except OSError as e:
                    return "error", str(e).encode()
                if not chunk:
                    return "error", b"connection closed before full reply"
                self._rbuf += chunk
            data = self._rbuf[:self.resp_length]
            self._rbuf = self._rbuf[self.resp_length:]
            return "ok", data

    def request(self, data: bytes, timeout=None):
        """Send one payload and wait for the reply. Returns (status, bytes)."""
        if timeout is None:
            timeout = self.default_timeout
        payload = data + (b"\n" if self.newline else b"")
        with self.lock:
            try:
                sock = self.ensure()
            except OSError as e:
                return "error", str(e).encode()
            try:
                sock.sendall(payload)
            except OSError as e:
                self._close()
                return "error", str(e).encode()
            status, msg = self._read_response(sock, timeout)
            if status == "error":
                self._close()
            return status, msg


# --------------------------------------------------------------------------- #
# Daemon
# --------------------------------------------------------------------------- #

def _daemonize(log_path: Path) -> None:
    """Double-fork into the background and redirect stdio to the log file."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    if os.fork() > 0:
        os._exit(0)
    os.setsid()
    if os.fork() > 0:
        os._exit(0)
    fd = os.open(log_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
    os.dup2(fd, 0)
    os.dup2(fd, 1)
    os.dup2(fd, 2)
    if fd > 2:
        os.close(fd)


def run_daemon(args) -> int:
    local_path = _socket_path(args.name)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    if local_path.exists():
        local_path.unlink()

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(local_path))
    server.listen(16)

    pid_path = _pid_path(args.name)
    pid_path.parent.mkdir(parents=True, exist_ok=True)
    pid_path.write_text(str(os.getpid()))

    stop = threading.Event()
    remote = Remote(
        args.host, args.port, args.reconnect_delay, args.newline,
        args.resp_mode, args.resp_idle, args.resp_length, args.timeout,
        args.resp_delimiter.encode(),
    )

    def on_term(signum, frame):
        _log("received signal, shutting down")
        stop.set()

    signal.signal(signal.SIGTERM, on_term)
    signal.signal(signal.SIGINT, on_term)

    def handle_client(conn: socket.socket) -> None:
        try:
            meta_bytes = _recv_frame(conn)
            meta = json.loads(meta_bytes.decode("utf-8")) if meta_bytes else {}
            payload = _recv_frame(conn)
            timeout = meta.get("timeout")
            status, msg = remote.request(payload, timeout)
            code = {"ok": 0, "timeout": 1, "error": 2}[status]
            conn.sendall(bytes([code]) + HEADER.pack(len(msg)) + msg)
        except (ConnectionError, ValueError, OSError, json.JSONDecodeError):
            pass
        finally:
            try:
                conn.close()
            except OSError:
                pass

    _log(f"listening on {local_path} -> {args.host}:{args.port} "
         f"(resp-mode={args.resp_mode}, timeout={args.timeout}s)")

    try:
        while not stop.is_set():
            server.settimeout(1.0)
            try:
                conn, _ = server.accept()
            except socket.timeout:
                continue
            t = threading.Thread(target=handle_client, args=(conn,), daemon=True)
            t.start()
    finally:
        stop.set()
        remote._close()
        server.close()
        try:
            local_path.unlink()
        except OSError:
            pass
        try:
            pid_path.unlink()
        except OSError:
            pass
        _log("shutdown complete")
    return 0


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #

def cmd_send(args) -> int:
    if args.data is not None:
        data = args.data.encode()
    else:
        data = sys.stdin.read().encode()
    local_path = args.local_socket or str(_socket_path(args.name))
    daemon_timeout = args.timeout if args.timeout is not None else 10.0
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(daemon_timeout + 10.0)
        s.connect(local_path)
        _send_frame(s, json.dumps({"timeout": args.timeout}).encode())
        _send_frame(s, data)
        status = _recv_exact(s, 1)[0]
        msg = _recv_frame(s)
        s.close()
    except (OSError, ConnectionError, ValueError) as e:
        print(f"ERR: cannot reach connector at {local_path}: {e}", file=sys.stderr)
        return 1

    if status == 0:
        out = sys.stdout.buffer
        out.write(msg)
        if not msg.endswith(b"\n"):
            out.write(b"\n")
        out.flush()
        return 0
    label = {1: "TIMEOUT", 2: "ERR"}.get(status, "ERR")
    print(f"{label}: {msg.decode(errors='replace').strip()}", file=sys.stderr)
    return 1


def cmd_stop(args) -> int:
    pid = _read_pid(args.name)
    if pid is None or not _pid_alive(pid):
        print("not running")
        return 0
    os.kill(pid, signal.SIGTERM)
    for _ in range(50):
        if not _pid_alive(pid):
            print("stopped")
            return 0
        time.sleep(0.1)
    print("sent SIGTERM but still running")
    return 1


def cmd_status(args) -> int:
    pid = _read_pid(args.name)
    alive = _pid_alive(pid)
    sock_exists = _socket_path(args.name).exists()
    print(f"name={args.name} pid={pid} alive={alive} socket={sock_exists}")
    return 0 if alive else 1


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="long-lived TCP client with blocking request/response",
    )
    p.add_argument("--name", default=DEFAULT_NAME, help="connector instance name")
    p.add_argument("--local-socket", default=None, help="override local socket path")
    sub = p.add_subparsers(dest="command", required=True)

    def _add_common(subp):
        # Accept --name / --local-socket after the subcommand as well.
        subp.add_argument("--name", default=argparse.SUPPRESS, help="connector instance name")
        subp.add_argument("--local-socket", default=argparse.SUPPRESS, help="override local socket path")

    sp = sub.add_parser("start", help="start the daemon")
    _add_common(sp)
    sp.add_argument("--host", required=True)
    sp.add_argument("--port", type=int, required=True)
    sp.add_argument("--reconnect-delay", type=float, default=2.0)
    sp.add_argument("--newline", action="store_true", default=True, dest="newline")
    sp.add_argument("--no-newline", action="store_false", dest="newline")
    sp.add_argument("--resp-mode", choices=("line", "idle", "fixed"), default="line")
    sp.add_argument("--resp-delimiter", default="||END||",
                    help="line mode: reply terminates at this string")
    sp.add_argument("--resp-idle", type=float, default=0.2,
                    help="idle mode: seconds of silence that ends a reply")
    sp.add_argument("--resp-length", type=int, default=1024,
                    help="fixed mode: exact reply length in bytes")
    sp.add_argument("--timeout", type=float, default=10.0,
                    help="default seconds to wait for a reply")
    sp.add_argument("--daemon", action="store_true", help="run in the background")

    se = sub.add_parser("send", help="send data and wait for the reply")
    _add_common(se)
    se.add_argument("data", nargs="?", help="payload; if omitted, read from stdin")
    se.add_argument("--timeout", type=float, default=None,
                    help="seconds to wait for the reply (overrides start default)")

    stop_p = sub.add_parser("stop", help="stop the daemon")
    _add_common(stop_p)
    status_p = sub.add_parser("status", help="show daemon status")
    _add_common(status_p)

    args = p.parse_args(argv)

    if args.command == "start":
        if args.daemon:
            _daemonize(_log_path(args.name))
        return run_daemon(args)
    if args.command == "send":
        return cmd_send(args)
    if args.command == "stop":
        return cmd_stop(args)
    if args.command == "status":
        return cmd_status(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
