@echo off
REM =====================================================================
REM geniriclaw -- stop running bot (Windows)
REM Uses `geniriclaw stop` which kills bot + Docker sandbox if any.
REM =====================================================================
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\geniriclaw.exe" (
    echo [ERROR] geniriclaw not installed. Run install.bat first.
    pause
    exit /b 1
)

set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo [geniriclaw] Stopping bot...
".venv\Scripts\geniriclaw.exe" stop
if errorlevel 1 (
    echo [geniriclaw] No running bot found, or stop failed.
)

endlocal
pause
