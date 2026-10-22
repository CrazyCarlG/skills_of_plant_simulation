@echo off
REM ============================================================
REM  Stop Plant Simulation CoPilot service.
REM  Tries /shutdown first; falls back to killing pythonw.exe.
REM
REM  Paths come from ..\config\local.properties
REM ============================================================

setlocal

call "%~dp0..\config\load_paths.cmd"
if errorlevel 1 (
    pause
    exit /b 1
)

set "COPILOT_CONSOLE_PYTHON=%COPILOT_PYTHON:pythonw.exe=python.exe%"

echo [CoPilot] Requesting graceful shutdown on port %COPILOT_PORT%...
powershell -NoProfile -Command ^
    "try { (Invoke-WebRequest -UseBasicParsing -TimeoutSec 3 -Method POST http://%COPILOT_HOST%:%COPILOT_PORT%/shutdown).Content } catch { 'FALLBACK' }" ^
    > "%TEMP%\copilot_stop.txt" 2>nul
set /p RESULT=<"%TEMP%\copilot_stop.txt"

if /i not "%RESULT%"=="FALLBACK" (
    del "%TEMP%\copilot_stop.txt" 2>nul
    echo [CoPilot] Shutdown signal sent.
    timeout /t 2 /nobreak > nul
    goto :verify
)

echo [CoPilot] /shutdown did not respond, locating the CoPilot Uvicorn process...
powershell -NoProfile -Command ^
    "$python='%COPILOT_DIR%\%COPILOT_CONSOLE_PYTHON%'; $service='%COPILOT_SERVICE%'; Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -ieq $python -and $_.CommandLine -like ('*-m uvicorn ' + $service + '*') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"

:verify
del "%TEMP%\copilot_stop.txt" 2>nul
powershell -NoProfile -Command ^
    "try { (Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 http://%COPILOT_HOST%:%COPILOT_PORT%/health).StatusCode } catch { 0 }" ^
    > "%TEMP%\copilot_check.txt" 2>nul
set /p HTTP=<"%TEMP%\copilot_check.txt"
del "%TEMP%\copilot_check.txt" 2>nul

if "%HTTP%"=="200" (
    echo [CoPilot] Still running. Try manually: taskkill /F /IM pythonw.exe
) else (
    echo [CoPilot] Stopped.
)
pause
endlocal
