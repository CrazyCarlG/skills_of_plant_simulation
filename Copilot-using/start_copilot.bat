@echo off
REM ============================================================
REM  Start Plant Simulation CoPilot service (background, no console)
REM  Double-click to run.
REM ============================================================

setlocal

REM --- paths (edit if you installed CoPilot elsewhere) ---
set "COPILOT_DIR=C:\ProgramFiles\Siemens\TecnomatixPlantSimulation2606\Copilot"
set "PORT=8002"
set "LOG_DIR=%COPILOT_DIR%\logs"

REM --- preflight ---
if not exist "%COPILOT_DIR%\python-3.14.5-embed\pythonw.exe" (
    echo [error] Embedded Python not found at:
    echo         %COPILOT_DIR%\python-3.14.5-embed\pythonw.exe
    echo         Run setup.bat first.
    pause
    exit /b 1
)
if not exist "%COPILOT_DIR%\copilot_service.py" (
    echo [error] copilot_service.py not found at:
    echo         %COPILOT_DIR%
    pause
    exit /b 1
)
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "LOG=%LOG_DIR%\copilot.log"

REM --- already-running check ---
powershell -NoProfile -Command ^
    "try { $r=Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://localhost:%PORT%/health; if($r.StatusCode -eq 200){'RUNNING'} else {'DOWN'} } catch { 'DOWN' }" ^
    > "%TEMP%\copilot_check.txt" 2>nul
set /p STATUS=<"%TEMP%\copilot_check.txt"
if /i "%STATUS%"=="RUNNING" (
    echo [CoPilot] Already running on port %PORT%.
    echo.
    powershell -NoProfile -Command "(Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://localhost:%PORT%/health).Content"
    echo.
    del "%TEMP%\copilot_check.txt" 2>nul
    pause
    exit /b 0
)
del "%TEMP%\copilot_check.txt" 2>nul

REM --- launch (pythonw = no console window; correct entry point = uvicorn) ---
echo [CoPilot] Starting service (port %PORT%)...
cd /d "%COPILOT_DIR%"
start "CoPilot Service" /B "" "%COPILOT_DIR%\python-3.14.5-embed\pythonw.exe" -m uvicorn copilot_service:app --host 127.0.0.1 --port %PORT% > "%LOG%" 2>&1

REM --- wait for service to bind (RAG indices + embedding model take 5-15s on first run) ---
echo [CoPilot] Waiting for service to become ready...
set /a TRIES=0
:wait_loop
set /a TRIES+=1
if %TRIES% GTR 60 (
    echo [CoPilot] Service did not respond after 120s. Check log:
    echo           %LOG%
    pause
    exit /b 1
)
REM Use ping for sleep (works in both cmd and Git Bash; avoid 'timeout' which clashes with GNU coreutils)
ping -n 3 127.0.0.1 > nul
powershell -NoProfile -Command ^
    "try { (Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://localhost:%PORT%/health).StatusCode } catch { 0 }" ^
    > "%TEMP%\copilot_check.txt" 2>nul
set /p HTTP=<"%TEMP%\copilot_check.txt"
del "%TEMP%\copilot_check.txt" 2>nul
if "%HTTP%"=="200" goto :ready
goto :wait_loop

:ready
echo.
echo [CoPilot] Service is up. /health:
powershell -NoProfile -Command "(Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://localhost:%PORT%/health).Content"
echo.
echo.
echo Logs:  %LOG%
echo Stop:  stop_copilot.bat
echo.
echo Try it:  python ask_copilot.py "How do I create a Buffer in SimTalk?"
echo.
pause
endlocal
