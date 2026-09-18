"""Re-export Dispatch so `from win32com.client import Dispatch` works."""

from win32com import Dispatch, com_error  # noqa: F401
