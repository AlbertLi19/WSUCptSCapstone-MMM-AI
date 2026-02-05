# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
import os
import torch

# Custom spec file for Windows build with matplotlib backend exclusions

block_cipher = None

# Collect all torch dependencies (binaries, datas, hiddenimports)
torch_datas, torch_binaries, torch_hiddenimports = collect_all('torch')

# Dynamically locate torch lib directory and critical DLLs
torch_root = os.path.dirname(torch.__file__)
torch_lib_dir = os.path.join(torch_root, 'lib')

# List of critical PyTorch DLLs that must be bundled
critical_dlls = [
    'asmjit.dll',
    'c10.dll',
    'fbgemm.dll',
    'libiomp5md.dll',
    'libiompstubs5md.dll',
    'shm.dll',
    'torch.dll',
    'torch_cpu.dll',
    'torch_global_deps.dll',
    'torch_python.dll',
    'uv.dll',
]

# Add all critical DLLs to binaries list
# CRITICAL FIX: Place DLLs in BOTH root and torch/lib directories
# Windows searches in multiple locations, and different import paths need different locations
additional_binaries = []

# Add Microsoft Visual C++ Runtime DLLs (CRITICAL for c10.dll to initialize)
vc_runtime_dlls = [
    'C:\\Windows\\System32\\msvcp140.dll',
    'C:\\Windows\\System32\\vcruntime140.dll',
    'C:\\Windows\\System32\\vcruntime140_1.dll',
]
for dll_path in vc_runtime_dlls:
    if os.path.exists(dll_path):
        dll_name = os.path.basename(dll_path)
        # Add to root for immediate availability
        additional_binaries.append((dll_path, '.'))
        # ALSO add to torch/lib where torch DLLs are
        additional_binaries.append((dll_path, 'torch/lib'))
        print(f"Adding VC++ Runtime {dll_name} to bundle")

# Add PyTorch DLLs
for dll_name in critical_dlls:
    dll_path = os.path.join(torch_lib_dir, dll_name)
    if os.path.exists(dll_path):
        # Add to root directory
        additional_binaries.append((dll_path, '.'))
        # ALSO add to torch/lib directory (where torch expects them)
        additional_binaries.append((dll_path, 'torch/lib'))
        print(f"Adding {dll_name} to bundle (root and torch/lib)")
    else:
        print(f"WARNING: {dll_name} not found at {dll_path}")

# Exclude problematic matplotlib backends that cause PyInstaller issues
excluded_modules = [
    'matplotlib.backends.backend_gtk3',
    'matplotlib.backends.backend_gtk3agg',
    'matplotlib.backends.backend_gtk3cairo',
    'matplotlib.backends.backend_gtk4',
    'matplotlib.backends.backend_gtk4agg',
    'matplotlib.backends.backend_gtk4cairo',
    'matplotlib.backends.backend_wx',
    'matplotlib.backends.backend_wxagg',
    'matplotlib.backends.backend_tkagg',
    'matplotlib.backends.backend_tk',
    'matplotlib.backends.backend_qt4',
    'matplotlib.backends.backend_qt4agg',
    'matplotlib.backends.backend_pyside',
    'matplotlib.backends.backend_pyside2',
    'matplotlib.backends.backend_pyside6',
    'matplotlib.backends.backend_macosx',
    'matplotlib.backends.backend_cocoaagg',
    'matplotlib.backends.backend_cairo',
    'tkinter',
    'test',
    'tests',
    'numpy.tests',
    'pandas.tests',
    'scipy.tests',
    'matplotlib.tests',
    'sklearn.tests',
]

a = Analysis(
    ['src\\app\\launcher.py'],
    pathex=[],
    binaries=torch_binaries + additional_binaries,
    datas=[
        ('src\\app\\analysis_scripts', 'analysis_scripts'),
        ('src\\app\\Databases', 'Databases'),
        ('version.txt', '.'),
        ('pyi_rth_torch.py', '.'),
    ] + torch_datas,
    hiddenimports=[
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'pyqtgraph',
        'pyqtgraph.exporters',
        'pyqtgraph.graphicsItems',
        'numpy',
        'pandas',
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends.backend_qt5agg',
        'matplotlib.backends.backend_agg',
        'cv2',
        'sklearn',
        'sklearn.neighbors',
        'sklearn.model_selection',
        'scipy',
        'scipy.stats',
        'scipy.spatial',
        'PIL',
        'PIL.Image',
        'torch',
        'transformers',
        'requests',
        'skimage',
        'skimage.morphology',
        'skimage.measure',
        'skimage.filters',
        'skimage.segmentation',
        'fitter',
        'loguru',
    ] + torch_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['pyi_rth_torch.py'],
    excludes=excluded_modules,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SegmentationApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
