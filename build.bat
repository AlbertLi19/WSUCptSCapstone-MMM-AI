@echo off
REM Build script for creating the Segmentation App executable with auto-update support (Windows)

echo ==========================================
echo Building Segmentation App Executable
echo ==========================================

REM Use local venv if available
if exist .venv\Scripts\python.exe (
    echo Using local virtual environment...
    set PYTHON_CMD=.venv\Scripts\python.exe
) else (
    set PYTHON_CMD=python
)

REM Fail early instead of attempting incompatible SciPy/NumPy installations.
%PYTHON_CMD% -c "import sys; sys.exit(0 if sys.version_info[:2] in ((3, 11), (3, 12)) else 1)"
if errorlevel 1 (
    echo ERROR: Use 64-bit Python 3.11 or 3.12 with the current requirements.
    exit /b 1
)

REM Use the same compatible packaging tools and CPU libraries as release CI.
%PYTHON_CMD% -m pip install torch==2.8.0 torchvision==0.23.0 --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 exit /b 1
%PYTHON_CMD% -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
%PYTHON_CMD% -m pip check
if errorlevel 1 exit /b 1

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
    if errorlevel 1 exit /b 1
) else (
    echo ERROR: SegmentationApp-Windows.spec not found!
    echo Please ensure the spec file exists in the project root.
    pause
    exit /b 1
)

REM Do not distribute a bundle that cannot start or load its required modules.
%PYTHON_CMD% scripts\smoke_test_executable.py dist\SegmentationApp.exe --report test-results\frozen-smoke.json
if errorlevel 1 exit /b 1

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
