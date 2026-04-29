@echo off
setlocal

REM One-command bootstrap for new Windows machines:
REM - creates/uses .venv
REM - installs dependencies
REM - launches the app

echo ==========================================
echo Segmentation App: Setup and Run
echo ==========================================

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not on PATH.
    echo Install Python 3.10+ and check "Add python.exe to PATH", then rerun.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment in .venv ...
    python -m venv .venv
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
)

set "PYTHON_CMD=.venv\Scripts\python.exe"
set "PIP_CMD=.venv\Scripts\pip.exe"

echo Upgrading pip/setuptools/wheel ...
%PYTHON_CMD% -m pip install --upgrade pip setuptools wheel
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed while upgrading pip tooling.
    pause
    exit /b 1
)

echo Installing project dependencies from requirements.txt ...
%PIP_CMD% install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Dependency installation failed.
    echo Tip: rerun this script, or install failing packages manually.
    pause
    exit /b 1
)

echo Launching application ...
%PYTHON_CMD% src\app\main.py

endlocal
