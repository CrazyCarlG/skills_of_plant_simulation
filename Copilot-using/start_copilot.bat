@echo off
REM ============================================================
REM  Start Plant Simulation CoPilot service and stream its startup log
REM  Double-click to run.
REM
REM  Paths come from ..\config\local.properties
REM ============================================================

setlocal

REM --- load paths from config ---
call "%~dp0..\config\load_paths.cmd"
if errorlevel 1 (
    pause
    exit /b 1
)

set "COPILOT_CONSOLE_PYTHON=%COPILOT_PYTHON:pythonw.exe=python.exe%"

set "LOG_DIR=%COPILOT_DIR%\%COPILOT_LOG_SUBDIR%"
set "LOG=%LOG_DIR%\%COPILOT_LOG_FILE%"

REM --- preflight ---
if not exist "%COPILOT_DIR%\%COPILOT_CONSOLE_PYTHON%" (
    echo [error] Console Python not found at:
    echo         %COPILOT_DIR%\%COPILOT_CONSOLE_PYTHON%
    echo         Run setup.bat first.
    pause
    exit /b 1
)
if not exist "%COPILOT_DIR%\%COPILOT_SERVICE_FILE%" (
    echo [error] %COPILOT_SERVICE_FILE% not found at:
    echo         %COPILOT_DIR%
    pause
    exit /b 1
)
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

REM --- already-running check ---
powershell -NoProfile -Command ^
    "try { $h=Invoke-RestMethod -TimeoutSec 2 http://%COPILOT_HOST%:%COPILOT_PORT%/health; if($h.agent_ready -eq $true){'READY'} else {'STARTING'} } catch { 'DOWN' }" ^
    > "%TEMP%\copilot_check.txt" 2>nul
set /p STATUS=<"%TEMP%\copilot_check.txt"
del "%TEMP%\copilot_check.txt" 2>nul
if /i "%STATUS%"=="READY" (
    echo [CoPilot] Already ready on port %COPILOT_PORT%.
    goto :ready
)
if /i "%STATUS%"=="STARTING" (
    echo [CoPilot] Service is responding but the agent is still initializing.
    goto :wait_for_ready
)

REM --- launch with console Python so redirected service logs are available ---
echo [CoPilot] Starting service (port %COPILOT_PORT%)...
cd /d "%COPILOT_DIR%"
start "CoPilot Service" /B "%COPILOT_DIR%\%COPILOT_CONSOLE_PYTHON%" -u -m uvicorn %COPILOT_SERVICE% --host %COPILOT_HOST% --port %COPILOT_PORT% > "%LOG%" 2>&1

:wait_for_ready
echo [CoPilot] Waiting for agent_ready=true. Streaming service log:
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0wait_copilot.ps1" -HostName "%COPILOT_HOST%" -Port %COPILOT_PORT% -LogPath "%LOG%" -TimeoutSeconds 480
if errorlevel 1 (
    echo [CoPilot] Service did not become ready after 480s. Check log:
    echo           %LOG%
    pause
    exit /b 1
)
goto :ready

:ready
echo.
echo [CoPilot] Agent is ready. /health:
powershell -NoProfile -Command "(Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://%COPILOT_HOST%:%COPILOT_PORT%/health).Content"
echo.
echo.
echo Logs:  %LOG%
echo Stop:  stop_copilot.bat
echo.
echo Try it:  python ask_copilot.py "How do I create a Buffer in SimTalk?"
echo.
pause
endlocal
