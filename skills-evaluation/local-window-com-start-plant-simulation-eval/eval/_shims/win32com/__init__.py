"""Fake `win32com` package for the eval framework.

Loaded by setting PYTHONPATH to the parent of this `_shims/` directory
in the subprocess environment, and invoking the script under test.
The shim:

- Replaces `win32com.client.Dispatch(progid)` with a recorder.
- (Optionally) stubs `os.path.isfile` so hermetic tests don't need real
  model / SimtalkClaude files on disk. Controlled by
  `EVAL_MOCK_PATHS_AS_EXISTING` env var (semicolon-separated path
  substrings).
- Writes the recorded call sequence to the file named in
  `EVAL_MOCK_LOG` so the parent runner can read it.

The shim is intentionally NOT a full COM emulator. It covers the
specific calls the start_plant_simulation.py script makes:

    rc = Dispatch("Tecnomatix.PlantSimulation.RemoteControl.26.6")
    rc.SetVisible(...)
    rc.SetNoMessageBox(...)
    rc.LoadModel(...)
    rc.SetTrustModels(...)
    rc.ExecuteSimTalk(...)

If a task wants to inject a fault (a raised com_error, a return value
override), it can set the env var `EVAL_MOCK_FAULTS` to a JSON file
specifying the per-method behavior. See `_apply_faults`.
"""

from __future__ import annotations

import json
import os
import sys
import types


# --- Recorder state ---------------------------------------------------------

_RECORD: list[str] = []
_FAULT_PROGRAM_ID: dict[str, dict] = {}  # progid -> {method: {action, ...}}
_FAULT_GLOBAL: dict[str, dict] = {}  # method -> {action, ...} (all progids)


def _record(name: str) -> None:
    _RECORD.append(name)


def _log_setup_error(msg: str) -> None:
    """Write a setup-error line to EVAL_MOCK_LOG without raising."""
    log_path = os.environ.get("EVAL_MOCK_LOG")
    if not log_path:
        return
    try:
        with open(log_path, "w", encoding="utf-8") as fh:
            json.dump({"setup_error": msg, "calls": []}, fh)
    except OSError:
        pass


def _flush_log() -> None:
    """Write the call sequence + setup_error to EVAL_MOCK_LOG."""
    log_path = os.environ.get("EVAL_MOCK_LOG")
    if not log_path:
        return
    payload = {
        "setup_error": None,
        "calls": list(_RECORD),
    }
    try:
        with open(log_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
    except OSError as e:
        # Last resort — print to stderr so the parent can see something.
        print(f"[mock_win32com] could not write log: {e}", file=sys.stderr)


def _load_faults() -> None:
    """Load fault config from EVAL_MOCK_FAULTS (JSON file)."""
    global _FAULT_GLOBAL, _FAULT_PROGRAM_ID
    fault_path = os.environ.get("EVAL_MOCK_FAULTS")
    if not fault_path or not os.path.exists(fault_path):
        return
    try:
        data = json.loads(open(fault_path, encoding="utf-8").read())
    except (json.JSONDecodeError, OSError) as e:
        _log_setup_error(f"could not load faults file: {e}")
        return
    if not isinstance(data, dict):
        _log_setup_error(f"faults file root must be a dict, got {type(data).__name__}")
        return
    _FAULT_GLOBAL = data.get("global", {}) if isinstance(data.get("global"), dict) else {}
    _FAULT_PROGRAM_ID = data.get("by_progid", {}) if isinstance(data.get("by_progid"), dict) else {}


def _apply_faults(progid: str, method: str, args: tuple, kwargs: dict):
    """If a fault is registered for (progid, method) or (None, method),
    apply it. Returns a tuple (skip, result_or_exc) where:
      - skip = True means the underlying mock should NOT be called
      - result_or_exc is either a return value or an Exception to raise
    """
    faults = _FAULT_PROGRAM_ID.get(progid, {}) or {}
    if not isinstance(faults, dict):
        faults = {}
    f = faults.get(method) or _FAULT_GLOBAL.get(method)
    if not f:
        return False, None
    if not isinstance(f, dict):
        return False, None
    action = f.get("action", "ok")
    if action == "raise_com_error":
        hresult = int(f.get("hresult", 0x80040154))
        msg = f.get("message", f"mock com_error {hex(hresult)}")
        return True, com_error(hresult, msg)
    if action == "raise":
        msg = f.get("message", f"mock exception in {method}")
        return True, RuntimeError(msg)
    if action == "return":
        return True, f.get("value")
    # default: ok
    return False, None


# --- Fakes -------------------------------------------------------------------


class com_error(Exception):
    """Stand-in for pywintypes.com_error."""

    def __init__(self, hresult: int, message: str = ""):
        super().__init__(message or f"com_error {hex(hresult)}")
        self.hresult = hresult
        self.strerror = message or f"com_error {hex(hresult)}"


class _MethodRecorder:
    """Represents one method call on a MockRemoteControl.

    The start_plant_simulation.py script uses:
        rc.SetVisible(...)
        rc.SetNoMessageBox(...)
        rc.LoadModel(...)
        rc.SetTrustModels(...)
        rc.ExecuteSimTalk(...)
    Each is a one-shot — no state on the remote control is required.
    """

    def __init__(self, progid: str, method: str, instance: "MockRemoteControl"):
        self._progid = progid
        self._method = method
        self._instance = instance

    def __call__(self, *args, **kwargs):
        _record(f"{self._progid}.{self._method}")
        skip, override = _apply_faults(self._progid, self._method, args, kwargs)
        if skip:
            if isinstance(override, Exception):
                raise override
            return override
        # Default: pretend success.
        return None


class MockRemoteControl:
    """Stand-in for a Plant Simulation RemoteControl COM object."""

    def __init__(self, progid: str):
        self._progid = progid
        _record(f"Dispatch({progid!r})")

    def __getattr__(self, name: str):
        # Treat any unknown attribute access as a method call.
        return _MethodRecorder(self._progid, name, self)


# --- Module surface ----------------------------------------------------------


def Dispatch(progid: str):
    """win32com.client.Dispatch shim."""
    return MockRemoteControl(progid)


# Expose com_error on the win32com module too (some scripts may use it).
com_error = com_error


# --- Bootstrap ---------------------------------------------------------------


def _install_isfile_stub() -> None:
    """Optionally stub `os.path.isfile` so hermetic tests can pass
    arbitrary paths without real files on disk.

    Activated by `EVAL_MOCK_PATHS_AS_EXISTING` (semicolon-separated list
    of path substrings; any path that contains one of these substrings
    is treated as existing).
    """
    import os.path as _osp
    substrs_raw = os.environ.get("EVAL_MOCK_PATHS_AS_EXISTING", "")
    if not substrs_raw:
        return
    substrs = [s for s in substrs_raw.split(";") if s]
    if not substrs:
        return
    _real_isfile = _osp.isfile

    def _patched_isfile(path):
        try:
            p = str(path)
        except Exception:
            return _real_isfile(path)
        for s in substrs:
            if s in p:
                return True
        return _real_isfile(path)

    _osp.isfile = _patched_isfile
    try:
        os.isfile = _patched_isfile  # type: ignore[attr-defined]
    except (AttributeError, TypeError):
        pass


def _install_pywintypes_into_sys() -> None:
    """If the real pywintypes is not on the subprocess's path, install
    a stub in sys.modules. The stub's `com_error` is the shim's class
    so the script's `isinstance(exc, pywintypes.com_error)` works.

    NOTE: When the parent has a real `pywintypes.py` on PYTHONPATH, the
    import below will resolve to it and this function is a no-op. This
    function only runs if PYTHONPATH doesn't include a real pywintypes.
    """
    if "pywintypes" in sys.modules:
        return
    mod = types.ModuleType("pywintypes")
    mod.com_error = com_error
    sys.modules["pywintypes"] = mod


def _bootstrap() -> None:
    """Initialize the shim — load faults, install atexit hook, etc.

    If `EVAL_MOCK_DISABLE=1` is set, the shim raises ImportError on import.
    This simulates a host that has no pywin32 installed — used to test
    the script's RuntimeError fallback path (lifelines.md §6).
    """
    if os.environ.get("EVAL_MOCK_DISABLE", "").strip() in ("1", "true", "yes"):
        # Write a setup-error log so the runner knows the shim was
        # disabled intentionally, not by accident.
        _log_setup_error("EVAL_MOCK_DISABLE=1; shim refused to load")
        raise ImportError(
            "EVAL_MOCK_DISABLE=1: mock_win32com shim refused to load "
            "(simulating missing pywin32)"
        )
    _install_pywintypes_into_sys()
    _load_faults()
    _install_isfile_stub()
    import atexit
    atexit.register(_flush_log)
    log_path = os.environ.get("EVAL_MOCK_LOG")
    if log_path and not os.path.exists(log_path):
        try:
            with open(log_path, "w", encoding="utf-8") as fh:
                json.dump({"setup_error": None, "calls": []}, fh)
        except OSError:
            pass


_bootstrap()
