@echo off
setlocal

REM Fast app runner for machines already set up.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" src\app\main.py
    exit /b %ERRORLEVEL%
)

echo WARNING: .venv not found. Falling back to system Python.
echo If this fails on a new machine, run setup_and_run.bat first.
python src\app\main.py

endlocal
