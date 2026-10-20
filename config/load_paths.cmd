@echo off
REM ============================================================
REM  Load CoPilot runtime paths from local.properties
REM  Called by Copilot-using\start_copilot.bat and stop_copilot.bat
REM
REM  Sets: COPILOT_DIR, COPILOT_PYTHON, COPILOT_SERVICE_FILE,
REM         COPILOT_SERVICE, COPILOT_HOST, COPILOT_PORT,
REM         COPILOT_LOG_SUBDIR, COPILOT_LOG_FILE
REM
REM  Exits with 1 if the config is missing or incomplete.
REM ============================================================

set "CONFIG_FILE=%~dp0local.properties"

if not exist "%CONFIG_FILE%" (
    echo [error] Config file not found:
    echo         %CONFIG_FILE%
    exit /b 1
)

set "COPILOT_DIR="
set "COPILOT_PYTHON="
set "COPILOT_SERVICE_FILE="
set "COPILOT_SERVICE="
set "COPILOT_HOST="
set "COPILOT_PORT="
set "COPILOT_LOG_SUBDIR="
set "COPILOT_LOG_FILE="

for /f "usebackq eol=; tokens=1,* delims==" %%A in ("%CONFIG_FILE%") do (
    if "%%A"=="COPILOT_DIR" set "COPILOT_DIR=%%B"
    if "%%A"=="COPILOT_PYTHON" set "COPILOT_PYTHON=%%B"
    if "%%A"=="COPILOT_SERVICE_FILE" set "COPILOT_SERVICE_FILE=%%B"
    if "%%A"=="COPILOT_SERVICE" set "COPILOT_SERVICE=%%B"
    if "%%A"=="COPILOT_HOST" set "COPILOT_HOST=%%B"
    if "%%A"=="COPILOT_PORT" set "COPILOT_PORT=%%B"
    if "%%A"=="COPILOT_LOG_SUBDIR" set "COPILOT_LOG_SUBDIR=%%B"
    if "%%A"=="COPILOT_LOG_FILE" set "COPILOT_LOG_FILE=%%B"
)

for %%K in (COPILOT_DIR COPILOT_PYTHON COPILOT_SERVICE_FILE COPILOT_SERVICE COPILOT_HOST COPILOT_PORT COPILOT_LOG_SUBDIR COPILOT_LOG_FILE) do (
    if not defined %%K (
        echo [error] Missing key %%K in %CONFIG_FILE%
        exit /b 1
    )
)

exit /b 0
