"""Read CoPilot runtime paths from the repository config file.

Single source of truth: ``config/local.properties`` at the repo root.
The same file is consumed by ``Copilot-using\\start_copilot.bat`` and
``stop_copilot.bat`` via ``config\\load_paths.cmd``, so the .bat scripts and
the Python client always agree on host, port and install dir.

Format: ``KEY=VALUE`` lines; lines starting with ``;`` are comments.
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = REPO_ROOT / "config" / "local.properties"

DEFAULTS = {
    "COPILOT_DIR": r"C:\ProgramFiles\Siemens\TecnomatixPlantSimulation2606\Copilot",
    "COPILOT_PYTHON": r"python-3.14.5-embed\pythonw.exe",
    "COPILOT_SERVICE_FILE": "copilot_service.py",
    "COPILOT_SERVICE": "copilot_service:app",
    "COPILOT_HOST": "127.0.0.1",
    "COPILOT_PORT": "8002",
    "COPILOT_LOG_SUBDIR": "logs",
    "COPILOT_LOG_FILE": "copilot.log",
}


def load_config(path: Path | None = None) -> dict[str, str]:
    """Return the merged config (file values over DEFAULTS)."""
    path = path or CONFIG_PATH
    values = dict(DEFAULTS)
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError:
        return values
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith(";"):
            continue
        key, separator, value = line.partition("=")
        if separator:
            values[key.strip()] = value.strip()
    return values


CONFIG = load_config()


def get(key: str) -> str:
    """Return one config value, falling back to DEFAULTS."""
    return CONFIG.get(key, DEFAULTS.get(key, ""))
