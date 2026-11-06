"""
Launcher script that prepares native libraries and starts the application.
This should be the entry point for the executable.
"""
import ctypes
import os
import sys
from datetime import datetime
from pathlib import Path

# Add the app directory to the path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))


def _log_preload_event(message: str) -> None:
    """Persist diagnostic info for DLL preload issues."""
    try:
        from utility.app_paths import app_data_root
        log_root = app_data_root() / "logs"
        log_root.mkdir(parents=True, exist_ok=True)
        log_path = log_root / "preload.log"
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(f"[{timestamp}] {message}\n")
    except Exception:
        # Logging must never block startup; swallow any failure.
        pass
    if os.getenv("LOG_TORCH_DLL_PRELOAD") == "1":
        print(f"[preload] {message}")


def preload_torch_native_libs() -> None:
    """Eagerly load critical torch DLLs when running as a frozen exe."""
    if os.name != "nt":
        return

    is_frozen = getattr(sys, "frozen", False)
    force_enabled = os.getenv("FORCE_TORCH_DLL_PRELOAD") == "1"
    if not is_frozen and not force_enabled:
        return

    _log_preload_event("Torch DLL preload enabled")

    base_dirs = []
    if is_frozen:
        base_dirs.append(Path(getattr(sys, "_MEIPASS", app_dir)))
    if force_enabled:
        try:
            import torch

            base_dirs.append(Path(torch.__file__).resolve().parent)
        except Exception:
            pass

    torch_lib_dir = None
    for base in base_dirs:
        candidate = base / "torch" / "lib"
        if candidate.exists():
            torch_lib_dir = candidate
            break

    if not torch_lib_dir:
        _log_preload_event("torch/lib directory not located; skipping")
        return

    try:
        os.add_dll_directory(str(torch_lib_dir))
        _log_preload_event(f"Added {torch_lib_dir} via os.add_dll_directory")
    except (AttributeError, FileNotFoundError, OSError) as err:
        _log_preload_event(f"add_dll_directory failed: {err}")

    path_before = os.environ.get("PATH", "")
    path_parts = path_before.split(os.pathsep) if path_before else []
    if str(torch_lib_dir) not in path_parts:
        os.environ["PATH"] = str(torch_lib_dir) + (os.pathsep + path_before if path_before else "")
        _log_preload_event(f"Prepended {torch_lib_dir} to PATH")

    # Try to preload VC++ Runtime DLLs first (for PyInstaller bundles)
    # These MUST be loaded before torch's c10.dll initialization
    if hasattr(sys, "_MEIPASS"):
        base_dir = Path(sys._MEIPASS)
        
        # Add System32 to DLL search path for VC++ Runtime DLLs
        system32 = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "System32"
        if system32.exists():
            try:
                os.add_dll_directory(str(system32))
                _log_preload_event(f"Added {system32} to DLL search path for VC++ Runtime")
            except (AttributeError, OSError) as err:
                _log_preload_event(f"Failed to add {system32} to DLL search path: {err}")
        
        # Preload VC++ Runtime DLLs using ctypes
        vc_dlls = ["msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll"]
        for dll_name in vc_dlls:
            loaded = False
            for search_dir in [system32, base_dir, torch_lib_dir]:
                dll_path = search_dir / dll_name
                if dll_path.exists():
                    try:
                        ctypes.CDLL(str(dll_path))
                        _log_preload_event(f"Loaded VC++ Runtime: {dll_name} from {search_dir}")
                        loaded = True
                        break
                    except OSError as e:
                        _log_preload_event(f"Failed to load {dll_name} from {search_dir}: {e}")
                        continue
            if not loaded:
                _log_preload_event(f"WARNING: Could not load {dll_name} from any location")
        
        # Also add base directory to DLL search path
        try:
            os.add_dll_directory(str(base_dir))
            _log_preload_event(f"Added {base_dir} to DLL search path")
        except (AttributeError, OSError) as err:
            _log_preload_event(f"Failed to add {base_dir} to DLL search path: {err}")

    critical_dlls = [
        "torch_global_deps.dll",
        "libiomp5md.dll",
        "c10.dll",
        "torch_cpu.dll",
        "torch.dll",
        "torch_python.dll",
        "libiompstubs5md.dll",
        "shm.dll",
        "uv.dll",
    ]

    for dll_name in critical_dlls:
        dll_path = torch_lib_dir / dll_name
        if not dll_path.exists():
            continue
        try:
            ctypes.CDLL(str(dll_path))
            _log_preload_event(f"Loaded {dll_name}")
        except OSError as err:
            warning = f"Unable to preload {dll_name}: {err}"
            print(f"WARNING: {warning}")  # Removed emoji to avoid encoding error
            _log_preload_event(warning)


def main():
    """Main launcher function"""
    from utility.app_paths import configure_portable_caches
    configure_portable_caches()
    if "--smoke-test" in sys.argv:
        # Run inside the real frozen executable, after PyInstaller's runtime hooks.
        from bundle_smoke_test import main as smoke_main
        sys.exit(smoke_main())

    print("=" * 60)
    print("Impurity Segmentation App - Starting...")
    print("=" * 60)

    preload_torch_native_libs()
    
    # Start directly; the application does not check for updates.
    from main import main as app_main
    app_main()


if __name__ == "__main__":
    main()
