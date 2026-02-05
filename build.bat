@echo off
REM Build script for creating the Segmentation App executable with auto-update support (Windows)

echo ==========================================
echo Building Segmentation App Executable
echo ==========================================

REM Check if PyInstaller is installed
where pyinstaller >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
)

REM Use local venv if available
if exist .venv\Scripts\python.exe (
    echo Using local virtual environment...
    set PYTHON_CMD=.venv\Scripts\python.exe
) else (
    set PYTHON_CMD=python
)

REM Check Python version
%PYTHON_CMD% -c "import sys; exit(1) if sys.version_info[:3] == (3, 10, 0) else exit(0)"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo WARNING: You are using Python 3.10.0.
    echo This version has a known bug that causes PyInstaller to fail with "IndexError: tuple index out of range".
    echo If the build fails, please upgrade to Python 3.10.1 or later.
    echo.
    timeout /t 5
)

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
REM Clean pycache
echo Cleaning __pycache__...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d"

REM Build using the custom Windows spec file
if exist SegmentationApp-Windows.spec (
    echo Using custom Windows spec file ^(with matplotlib backend exclusions^)...
    %PYTHON_CMD% -m PyInstaller SegmentationApp-Windows.spec
) else (
    echo ERROR: SegmentationApp-Windows.spec not found!
    echo Please ensure the spec file exists in the project root.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Build Complete!
echo ==========================================
echo Executable location: dist\SegmentationApp.exe
echo.
echo To run the app with auto-update:
echo   dist\SegmentationApp.exe --auto-update
echo.
echo To run without auto-update:
echo   dist\SegmentationApp.exe
echo.
pause
