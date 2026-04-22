@echo off
REM =====================================================================
REM geniriclaw -- installer (Windows)
REM Creates .venv, installs package in editable mode with all deps.
REM Re-run safe: skips venv creation if already exists.
REM =====================================================================
setlocal
cd /d "%~dp0"

echo.
echo [geniriclaw] Installation starting...
echo [geniriclaw] Location: %CD%
echo.

REM --- Check Python ---
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    echo         Install Python 3.11+ from https://www.python.org/downloads/
    goto :fail
)

for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo [geniriclaw] Python version: %PYVER%

REM --- Create venv if missing ---
if not exist ".venv\Scripts\python.exe" (
    echo [geniriclaw] Creating virtual environment in .venv\ ...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv.
        goto :fail
    )
) else (
    echo [geniriclaw] .venv already exists -- reusing.
)

REM --- Upgrade pip ---
echo [geniriclaw] Upgrading pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet

REM --- Install package ---
echo [geniriclaw] Installing geniriclaw in editable mode (may take 1-3 min)...
".venv\Scripts\python.exe" -m pip install -e .
if errorlevel 1 (
    echo [ERROR] pip install failed.
    goto :fail
)

echo.
echo =====================================================================
echo [OK] geniriclaw installed successfully.
echo.
echo Next steps:
echo   1. Run:    run.bat
echo   2. Stop:   stop.bat
echo =====================================================================
echo.
endlocal
pause
exit /b 0

:fail
echo.
echo =====================================================================
echo [FAIL] Installation aborted.
echo =====================================================================
endlocal
pause
exit /b 1
