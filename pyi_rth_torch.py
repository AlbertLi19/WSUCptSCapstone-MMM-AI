"""
PyInstaller runtime hook for PyTorch DLL loading fix.
This MUST execute before any torch imports to set up DLL search paths.
"""
import os
import sys
import ctypes

# Add the application directory to PATH so DLLs can find dependencies
if hasattr(sys, '_MEIPASS'):
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
            os.add_dll_directory(system32)
            os.add_dll_directory(bundle_dir)
            os.add_dll_directory(torch_lib)
        except (OSError, FileNotFoundError):
            pass  # Directory might not exist yet
    
    # Method 3: Set the working directory temporarily during DLL load
    # This helps Windows find the DLLs during initialization
    try:
        original_cwd = os.getcwd()
        os.chdir(bundle_dir)
        # Directory will be changed back after import completes
    except:
        pass
