#!/bin/bash
# Build script for creating the Segmentation App executable with auto-update support

set -e  # Exit on any error

echo "=========================================="
echo "Building Segmentation App Executable"
echo "=========================================="

# Deactivate conda if active
if command -v conda &> /dev/null; then
    conda deactivate 2>/dev/null || true
fi

# Activate capstoneENV
if [ -f "/Users/nicholaslopez/capstoneENV/bin/activate" ]; then
    echo "Activating capstoneENV..."
    source /Users/nicholaslopez/capstoneENV/bin/activate
else
    echo "ERROR: capstoneENV not found!"
    echo "Please create it with: python3 -m venv /Users/nicholaslopez/capstoneENV"
    exit 1
fi

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "PyInstaller not found. Installing..."
    pip install pyinstaller
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build dist
rm -f *.spec

# Create the spec file if it doesn't exist
if [ ! -f "launcher.spec" ]; then
    echo "Generating spec file..."
    pyinstaller --name=SegmentationApp \
                --onedir \
                --windowed \
                --add-data="src/app/analysis_scripts:analysis_scripts" \
                --add-data="src/app/Databases:Databases" \
                --add-data="version.txt:." \
                --hidden-import=PyQt5 \
                --hidden-import=numpy \
                --hidden-import=pandas \
                --hidden-import=matplotlib \
                --hidden-import=cv2 \
                --hidden-import=sklearn \
                --hidden-import=scipy \
                --hidden-import=PIL \
                --hidden-import=torch \
                --hidden-import=transformers \
                --hidden-import=requests \
                --hidden-import=skimage \
                --hidden-import=skimage.morphology \
                --hidden-import=skimage.measure \
                --hidden-import=fitter \
                src/app/launcher.py
else
    echo "Using existing launcher.spec file..."
    pyinstaller launcher.spec
fi

echo ""
echo "=========================================="
echo "Build Complete!"
echo "=========================================="
echo "Executable location: dist/SegmentationApp/"
echo ""
echo "To run the app with auto-update:"
echo "  ./dist/SegmentationApp/SegmentationApp --auto-update"
echo ""
echo "To run without auto-update:"
echo "  ./dist/SegmentationApp/SegmentationApp"
echo ""
