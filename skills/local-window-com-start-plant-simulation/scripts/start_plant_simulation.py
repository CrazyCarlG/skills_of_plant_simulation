"""Start Plant Simulation via COM RemoteControl.

Usage:
    python start_plant_simulation.py -m <model.spp> -s <simtalkclaude.pslib> [options]

Required:
    -m, --model PATH                 Path to the .spp model file to load
    -s, --simtalkclaudefile PATH     Path to the SimtalkClaude .pslib injected via basis.loadObjectAs

Optional:
	-p, --port N                     Starting TCP port for SimtalkClaude SocketServer (default: 50007; scans upward)
    --print-pid                      After loading, look up Plant Simulation.exe PIDs via tasklist and print them
    --no-visible                     Run Plant Simulation without showing the main window (default: visible)
    --allow-message-box              Allow modal message boxes (default: SetNoMessageBox(true))

Exit codes:
    0  success — PS launched, model loaded, port set
    2  bad CLI arguments (e.g. port out of range)
    3  COM dispatch failed
    4  model or SimtalkClaude file not found
    5  other unhandled exception

Example (Windows, cmd):
    python start_plant_simulation.py ^
        -m "C:\Models\MyModel.spp" ^
        -s "C:\lib\SimtalkClaude.pslib" ^
        -p 50007 ^
        --print-pid

Notes:
    - Requires pywin32 (`pip install pywin32`) and a registered
      "Tecnomatix.PlantSimulation.RemoteControl.26.6" COM class (Plant Simulation 2606).
    - Designed to be the first step before any TCP-based skill (local-simtalk-*) talks to the model;
      it intentionally does not run business SimTalk beyond the two lines needed to inject
      SimtalkClaude and flip the SocketServer port.
    - This script does NOT verify the SimtalkClaude socket is reachable; callers should follow up
      with `local-simtalk-ping` to confirm protocol-level readiness.
"""
from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys

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
	visible: bool = True,
	no_message_box: bool = True,
	port: int = 50007,
) -> int:
	"""Start PS, load model, inject SimtalkClaude, set port.

	Raises:
		RuntimeError: pywin32 not installed.
		ValueError: port out of range or no free port remains.
		FileNotFoundError: model or simtalkclaudefile missing.
		pywintypes.com_error: COM dispatch / model load / SimTalk execution failed.
	"""
	if win32com is None:
		raise RuntimeError("pywin32 (win32com) is required. Install with 'pip install pywin32'.")
	if not (1 <= port <= 65535):
		raise ValueError(f"Port must be in 1..65535, got {port}")
	port = find_available_port(port)

	model_path = os.path.abspath(model_path)
	if not os.path.isfile(model_path):
		raise FileNotFoundError(f"Model file not found: {model_path}")

	simtalkclaudefile = os.path.abspath(simtalkclaudefile)
	if not os.path.isfile(simtalkclaudefile):
		raise FileNotFoundError(f"SimtalkClaude library not found: {simtalkclaudefile}")

	# escape any double-quotes in the path to avoid breaking the SimTalk string
	esc = simtalkclaudefile.replace('"', '\\"')
	inject_command = f'basis.loadObjectAs("{esc}","", true, false)'
	changeport_command = f'var obj:=.SimtalkClaude.Main.SocketServer.mysocket;obj.on:=false;obj.port:={port};obj.on:=true;'

	# Create COM object and call methods similar to the VBScript example
	rc = win32com.client.Dispatch("Tecnomatix.PlantSimulation.RemoteControl.26.6")
	rc.SetVisible(bool(visible))
	rc.SetNoMessageBox(bool(no_message_box))

	rc.LoadModel(model_path)
	rc.SetTrustModels(True)
	rc.ExecuteSimTalk(inject_command)
	rc.ExecuteSimTalk(changeport_command)

	return port


def find_available_port(start_port: int) -> int:
	"""Return the first bindable TCP port at or above start_port."""
	for candidate in range(start_port, 65536):
		try:
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
				probe.bind(("0.0.0.0", candidate))
			return candidate
		except OSError:
			print(f"Port {candidate} is occupied; trying {candidate + 1}.", file=sys.stderr)
	raise ValueError(f"No available TCP port at or above {start_port} (maximum is 65535)")


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
	p.add_argument("--no-visible", dest="visible", action="store_false", help="Do not show the Plant Simulation window")
	p.add_argument("--allow-message-box", dest="no_message_box", action="store_false", help="Allow message boxes (disable SetNoMessageBox)")
	p.add_argument("-s", "--simtalkclaudefile", required=True, help="Path to a SimtalkClaude .pslib to inject via basis.loadObjectAs before changing the port (required)")
	p.add_argument("-p", "--port", type=int, default=50007, help="Starting TCP port; scan upward for the first available port (default: 50007)")
	p.add_argument("--print-pid", dest="print_pid", action="store_true", help="After loading, look up Plant Simulation.exe PIDs via tasklist and print them on stdout")
	return p.parse_args()


def main() -> int:
	args = _parse_args()

	try:
		actual_port = start_plant_simulation(
			args.model,
			args.simtalkclaudefile,
			visible=args.visible,
			no_message_box=args.no_message_box,
			port=args.port,
		)
	except FileNotFoundError as exc:
		print(f"Error: {exc}", file=sys.stderr)
		return EXIT_FILE_NOT_FOUND
	except ValueError as exc:
		print(f"Error: {exc}", file=sys.stderr)
		return EXIT_BAD_ARGS
	except Exception as exc:  # noqa: BLE001 — top-level dispatcher
		if pywintypes is not None and isinstance(exc, pywintypes.com_error):
			return _handle_com_error(exc)
		print(f"Error: {exc}", file=sys.stderr)
		return EXIT_OTHER

	print(f"Plant Simulation launched, model loaded, socket port set to {actual_port}.")
	if args.print_pid:
		pids = get_ps_pids_via_tasklist()
		if pids:
			print(f"Plant Simulation PID: {pids}")
		else:
			print("Warning: --print-pid requested but Plant Simulation.exe not found via tasklist.", file=sys.stderr)
	return EXIT_OK


if __name__ == "__main__":
	raise SystemExit(main())
