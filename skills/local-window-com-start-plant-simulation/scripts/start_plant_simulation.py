"""Start Plant Simulation via COM RemoteControl.

Example VBScript equivalent being mirrored:
var PlantSim = WScript.CreateObject("Tecnomatix.PlantSimulation.RemoteControl.26.6");
PlantSim.SetVisible(true);
PlantSim.SetNoMessageBox(true);
PlantSim.OpenConsoleLogFile("C:\\logs\\run_" + Date() + ".txt");
PlantSim.LoadModel("C:\\Models\\MyModel.spp");

This script provides a Python equivalent using pywin32's win32com.client,
plus validation, COM-specific error handling, optional socket-readiness polling,
and optional PID lookup via tasklist.

It does NOT execute any business SimTalk, does NOT maintain a socket
connection, and does NOT interact with the model beyond the steps required
to get a SocketServer listening on the requested port.
"""
from __future__ import annotations

import argparse
import datetime
import os
import socket
import subprocess
import sys
import time

try:
	import win32com.client
	import pywintypes
except ImportError:  # pragma: no cover - environment dependent
	win32com = None
	pywintypes = None


# Exit codes (documented in references/cli-args.md)
EXIT_OK = 0
EXIT_BAD_ARGS = 2
EXIT_COM_OR_SOCKET = 3
EXIT_FILE_NOT_FOUND = 4
EXIT_OTHER = 5


def start_plant_simulation(
	model_path: str,
	simtalkclaudefile: str,
	log_dir: str,
	visible: bool = True,
	no_message_box: bool = True,
	port: int = 50007,
	wait_ready: int = 0,
) -> None:
	"""Start PS, load model, inject SimtalkClaude, set port.

	Raises:
		RuntimeError: pywin32 not installed.
		ValueError: port out of range.
		FileNotFoundError: model or simtalkclaudefile missing.
		pywintypes.com_error: COM dispatch / model load / SimTalk execution failed.
		TimeoutError: --wait-ready polling did not see a listener in time.
		OSError: --wait-ready polling hit a non-recoverable network error.
	"""
	if win32com is None:
		raise RuntimeError("pywin32 (win32com) is required. Install with 'pip install pywin32'.")
	if not (1 <= port <= 65535):
		raise ValueError(f"Port must be in 1..65535, got {port}")

	model_path = os.path.abspath(model_path)
	if not os.path.isfile(model_path):
		raise FileNotFoundError(f"Model file not found: {model_path}")

	simtalkclaudefile = os.path.abspath(simtalkclaudefile)
	if not os.path.isfile(simtalkclaudefile):
		raise FileNotFoundError(f"SimtalkClaude library not found: {simtalkclaudefile}")

	os.makedirs(log_dir, exist_ok=True)
	timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
	logfile = os.path.join(log_dir, f"run_{timestamp}.txt")

	# escape any double-quotes in the path to avoid breaking the SimTalk string
	esc = simtalkclaudefile.replace('"', '\\"')
	inject_command = f'basis.loadObjectAs("{esc}","", true, false)'
	changeport_command = f'var obj:=.SimtalkClaude.Main.SocketServer.mysocket;obj.on:=false;obj.port:={port};obj.on:=true;'

	# Create COM object and call methods similar to the VBScript example
	rc = win32com.client.Dispatch("Tecnomatix.PlantSimulation.RemoteControl.26.6")
	rc.SetVisible(bool(visible))
	rc.SetNoMessageBox(bool(no_message_box))

	rc.OpenConsoleLogFile(logfile)
	rc.LoadModel(model_path)
	rc.SetTrustModels(True)
	rc.ExecuteSimTalk(inject_command)
	rc.ExecuteSimTalk(changeport_command)

	if wait_ready > 0:
		wait_for_socket("127.0.0.1", port, wait_ready)


def wait_for_socket(host: str, port: int, timeout: int) -> None:
	"""Poll TCP until connection succeeds or timeout (in seconds) elapses.

	Note: this only verifies that *something* is listening on host:port —
	it does not verify the listener is *our* SimtalkClaude socket. See
	references/lifelines.md §1 for why this is unavoidable without
	protocol-level handshake.

	Raises:
		TimeoutError: no listener within timeout.
		OSError: non-recoverable socket error (host unreachable, etc.).
	"""
	deadline = time.time() + timeout
	attempts = 0
	print(f"Waiting for socket on {host}:{port} ...", file=sys.stderr)
	while time.time() < deadline:
		attempts += 1
		try:
			with socket.create_connection((host, port), timeout=1):
				elapsed = timeout - (deadline - time.time())
				print(f"socket ready after {elapsed:.1f}s ({attempts} attempt(s))")
				return
		except (ConnectionRefusedError, TimeoutError):
			time.sleep(1)
	raise TimeoutError(
		f"Socket on {host}:{port} not ready after {timeout}s. "
		"Verify SimtalkClaude is loaded and the port change took effect "
		"(see references/lifelines.md §1)."
	)


def get_ps_pids_via_tasklist() -> list[int]:
	"""Return PIDs of running Plant Simulation.exe processes via tasklist."""
	try:
		out = subprocess.check_output(
			["tasklist", "/FI", "IMAGENAME eq Plant Simulation.exe", "/NH", "/FO", "CSV"],
			stderr=subprocess.DEVNULL,
			text=True,
		)
	except (subprocess.CalledProcessError, FileNotFoundError):
		return []
	pids: list[int] = []
	for line in out.splitlines():
		parts = line.strip().strip('"').split('","')
		if len(parts) >= 2 and "plant simulation.exe" in parts[0].lower():
			try:
				pids.append(int(parts[1]))
			except ValueError:
				continue
	return pids


def _handle_com_error(exc: BaseException) -> int:
	"""Print a hint tailored to common COM HRESULTs and return EXIT_COM_OR_SOCKET."""
	hresult = getattr(exc, "hresult", None)
	msg = getattr(exc, "strerror", None) or str(exc)
	hr_hex = f"0x{hresult & 0xFFFFFFFF:08X}" if isinstance(hresult, int) else "(unknown)"
	print(f"COMError: {msg} (hresult={hr_hex})", file=sys.stderr)
	if hresult == 0x80040154:
		print("Hint: class not registered. Install Plant Simulation 2606, or run:", file=sys.stderr)
		print('  regsvr32 "<PS install dir>\\Tecnomatix.PlantSimulation.RemoteControl.dll"', file=sys.stderr)
		return EXIT_COM_OR_SOCKET
	if hresult == 0x80080005:
		print("Hint: COM server launch failed. Another Plant Simulation instance may be", file=sys.stderr)
		print('  holding the singleton. Try:  taskkill /IM "Plant Simulation.exe" /F', file=sys.stderr)
		return EXIT_COM_OR_SOCKET
	print("Hint: see references/lifelines.md, or re-run with --allow-message-box to surface dialogs.", file=sys.stderr)
	return EXIT_COM_OR_SOCKET


def _parse_args() -> argparse.Namespace:
	p = argparse.ArgumentParser(
		description="Start Tecnomatix Plant Simulation via COM RemoteControl"
	)
	p.add_argument("-m", "--model", required=True, help="Path to the .spp model file to load")
	p.add_argument("-l", "--log-dir", required=True, help="Directory to write console log files (required; e.g. C:\\logs or a user-chosen writable path)")
	p.add_argument("--no-visible", dest="visible", action="store_false", help="Do not show the Plant Simulation window")
	p.add_argument("--allow-message-box", dest="no_message_box", action="store_false", help="Allow message boxes (disable SetNoMessageBox)")
	p.add_argument("-s", "--simtalkclaudefile", required=True, help="Path to a SimtalkClaude .pslib to inject via basis.loadObjectAs before changing the port (required)")
	p.add_argument("-p", "--port", type=int, default=50007, help="TCP port for SimtalkClaude SocketServer (default: 50007, range 1-65535)")
	p.add_argument("--wait-ready", type=int, default=0, metavar="SECONDS", help="After loading, poll 127.0.0.1:port until TCP connect succeeds or timeout (default: 0 = skip)")
	p.add_argument("--print-pid", dest="print_pid", action="store_true", help="After loading, look up Plant Simulation.exe PIDs via tasklist and print them on stdout")
	return p.parse_args()


def main() -> int:
	args = _parse_args()

	try:
		start_plant_simulation(
			args.model,
			args.simtalkclaudefile,
			args.log_dir,
			visible=args.visible,
			no_message_box=args.no_message_box,
			port=args.port,
			wait_ready=args.wait_ready,
		)
	except FileNotFoundError as exc:
		print(f"Error: {exc}", file=sys.stderr)
		return EXIT_FILE_NOT_FOUND
	except ValueError as exc:
		print(f"Error: {exc}", file=sys.stderr)
		return EXIT_BAD_ARGS
	except (ConnectionRefusedError, TimeoutError, OSError) as exc:
		print(f"Error: socket readiness check failed: {exc}", file=sys.stderr)
		return EXIT_COM_OR_SOCKET
	except Exception as exc:  # noqa: BLE001 — top-level dispatcher
		if pywintypes is not None and isinstance(exc, pywintypes.com_error):
			return _handle_com_error(exc)
		print(f"Error: {exc}", file=sys.stderr)
		return EXIT_OTHER

	print(f"Plant Simulation launched, model loaded, socket port set to {args.port}.")
	if args.print_pid:
		pids = get_ps_pids_via_tasklist()
		if pids:
			print(f"Plant Simulation PID: {pids}")
		else:
			print("Warning: --print-pid requested but Plant Simulation.exe not found via tasklist.", file=sys.stderr)
	return EXIT_OK


if __name__ == "__main__":
	raise SystemExit(main())
