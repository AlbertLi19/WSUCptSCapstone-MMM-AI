"""
PyInstaller runtime hook for PyTorch DLL loading fix.
This MUST execute before any torch imports to set up DLL search paths.
"""
import os
import sys
import ctypes

# Keep DLL search-directory handles alive for the lifetime of the process.
_dll_directory_handles = []

# Add the application directory to PATH so DLLs can find dependencies
if os.name == 'nt' and hasattr(sys, '_MEIPASS'):
    # Running as PyInstaller bundle
    bundle_dir = sys._MEIPASS
    torch_lib = os.path.join(bundle_dir, 'torch', 'lib')
    
    # CRITICAL FIX: Load VC++ Runtime DLLs from System32 FIRST
    # This is the Windows System32 directory where the actual VC++ Runtime lives
    system32 = os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), 'System32')
    
    # Preload VC++ Runtime DLLs from System32 into the process
    vc_dlls = ['msvcp140.dll', 'vcruntime140.dll', 'vcruntime140_1.dll']
    for dll_name in vc_dlls:
        try:
            dll_path = os.path.join(system32, dll_name)
            if os.path.exists(dll_path):
                ctypes.CDLL(dll_path)
        except:
            pass
    
    # CRITICAL: Set DLL search paths BEFORE any imports
    # Method 1: Add System32 FIRST, then bundle dirs
    old_path = os.environ.get('PATH', '')
    os.environ['PATH'] = system32 + os.pathsep + bundle_dir + os.pathsep + torch_lib + os.pathsep + old_path
    
    # Method 2: Add to DLL directory search (Python 3.8+)
    if hasattr(os, 'add_dll_directory'):
        try:
            for directory in (system32, bundle_dir, torch_lib):
                if os.path.isdir(directory):
                    _dll_directory_handles.append(os.add_dll_directory(directory))
        except (OSError, FileNotFoundError):
            pass  # Directory might not exist yet
