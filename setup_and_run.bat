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
    echo Install 64-bit Python 3.11 or 3.12 and check "Add python.exe to PATH", then rerun.
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

%PYTHON_CMD% -c "import sys; sys.exit(0 if sys.version_info[:2] in ((3, 11), (3, 12)) else 1)"
if errorlevel 1 (
    echo ERROR: The virtual environment must use Python 3.11 or 3.12.
    exit /b 1
)

echo Upgrading pip ...
%PYTHON_CMD% -m pip install --upgrade pip
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed while upgrading pip tooling.
    pause
    exit /b 1
)

echo Installing matching CPU-only PyTorch libraries ...
%PYTHON_CMD% -m pip install torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 exit /b 1

echo Installing project dependencies from requirements.txt ...
%PIP_CMD% install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Dependency installation failed.
    echo Tip: rerun this script, or install failing packages manually.
    pause
    exit /b 1
)

%PYTHON_CMD% -m pip check
if errorlevel 1 exit /b 1

echo Launching application ...
%PYTHON_CMD% src\app\main.py

endlocal
