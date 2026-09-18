"""Fake `pywintypes` module for the eval framework.

The script does `import pywintypes` and then `pywintypes.com_error`.
This shim provides just enough surface to make that work in mock mode.
"""

from __future__ import annotations

import sys


# Reuse the com_error class from the win32com shim so isinstance checks
# are consistent across both modules.
try:
    from win32com import com_error  # type: ignore
except ImportError:
    # If the win32com shim isn't loaded yet (shouldn't happen, but just
    # in case), define a local one.
    class com_error(Exception):  # type: ignore[no-redef]
        def __init__(self, hresult: int, message: str = ""):
            super().__init__(message or f"com_error {hex(hresult)}")
            self.hresult = hresult
            self.strerror = message or f"com_error {hex(hresult)}"


# Make sure the shim's com_error is the same class exposed by win32com.
# This matters because the script does
#   `if pywintypes is not None and isinstance(exc, pywintypes.com_error):`
# and we want the com_error raised by the win32com shim to be recognized
# here.
import win32com as _w32  # type: ignore
if hasattr(_w32, "com_error") and _w32.com_error is not com_error:
    com_error = _w32.com_error  # type: ignore[misc]


__all__ = ["com_error"]
