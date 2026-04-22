@echo off
REM =====================================================================
REM geniriclaw -- start bot in foreground (Windows)
REM Activates venv, sets UTF-8 mode, runs `geniriclaw`.
REM First run triggers the onboarding wizard.
REM =====================================================================
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\geniriclaw.exe" (
    echo [ERROR] geniriclaw not installed. Run install.bat first.
    pause
    exit /b 1
)

REM Force UTF-8 to prevent rich/console encoding errors on Windows cp1251
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

echo [geniriclaw] Starting... (Ctrl+C to stop)
echo.

".venv\Scripts\geniriclaw.exe" %*

endlocal
