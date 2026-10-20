@echo off
REM ============================================================
REM  Start Plant Simulation CoPilot service (background, no console)
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

set "LOG_DIR=%COPILOT_DIR%\%COPILOT_LOG_SUBDIR%"
set "LOG=%LOG_DIR%\%COPILOT_LOG_FILE%"

REM --- preflight ---
if not exist "%COPILOT_DIR%\%COPILOT_PYTHON%" (
    echo [error] Embedded Python not found at:
    echo         %COPILOT_DIR%\%COPILOT_PYTHON%
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
    "try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://%COPILOT_HOST%:%COPILOT_PORT%/health; if($r.StatusCode -eq 200){'RUNNING'} else {'DOWN'} } catch { 'DOWN' }" ^
    > "%TEMP%\copilot_check.txt" 2>nul
set /p STATUS=<"%TEMP%\copilot_check.txt"
if /i "%STATUS%"=="RUNNING" (
    echo [CoPilot] Already running on port %COPILOT_PORT%.
    echo.
    powershell -NoProfile -Command "(Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://%COPILOT_HOST%:%COPILOT_PORT%/health).Content"
    echo.
    del "%TEMP%\copilot_check.txt" 2>nul
    pause
    exit /b 0
)
del "%TEMP%\copilot_check.txt" 2>nul

REM --- launch (pythonw = no console window; correct entry point = uvicorn) ---
echo [CoPilot] Starting service (port %COPILOT_PORT%)...
cd /d "%COPILOT_DIR%"
start "CoPilot Service" /B "%COPILOT_DIR%\%COPILOT_PYTHON%" -m uvicorn %COPILOT_SERVICE% --host %COPILOT_HOST% --port %COPILOT_PORT% > "%LOG%" 2>&1

REM --- wait for service to bind (torch + arctic-embed model load takes 3-5 min on first run) ---
echo [CoPilot] Waiting for service to become ready...
set /a TRIES=0
:wait_loop
set /a TRIES+=1
if %TRIES% GTR 240 (
    echo [CoPilot] Service did not respond after 480s. Check log:
    echo           %LOG%
    pause
    exit /b 1
)
REM Use ping for sleep (works in both cmd and Git Bash; avoid 'timeout' which clashes with GNU coreutils)
ping -n 3 127.0.0.1 > nul
powershell -NoProfile -Command ^
    "try { (Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://%COPILOT_HOST%:%COPILOT_PORT%/health).StatusCode } catch { 0 }" ^
    > "%TEMP%\copilot_check.txt" 2>nul
set /p HTTP=<"%TEMP%\copilot_check.txt"
del "%TEMP%\copilot_check.txt" 2>nul
if "%HTTP%"=="200" goto :ready
<nul set /p "=."
set /a STATUS_REMAINDER=TRIES %% 5
if %STATUS_REMAINDER% EQU 0 (
    echo.
    echo [CoPilot] Still starting (check %TRIES%/240). Model/index loading or MCP connection may take time.
    echo           Log: %LOG%
)
goto :wait_loop

:ready
echo.
echo [CoPilot] Service is up. /health:
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
