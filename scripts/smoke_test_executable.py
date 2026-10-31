"""Run a frozen executable in isolation and require a successful smoke report."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile


def run(executable, report, timeout=300):
    executable = Path(executable).resolve(strict=True)
    report = Path(report).resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    # An old successful report must never hide a startup failure on a rerun.
    report.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix="segmentation-smoke-") as directory:
        root = Path(directory).resolve()
        profile = root / "profile"
        local = profile / "AppData" / "Local"
        local.mkdir(parents=True)
        env = dict(os.environ, USERPROFILE=str(profile), HOME=str(profile),
                   LOCALAPPDATA=str(local), QT_QPA_PLATFORM="offscreen",
                   HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1")
        # Do not allow the source checkout or installed Python packages to mask
        # missing files in the bundle. Native modules load from the bundle itself.
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
        process = subprocess.Popen(
            [str(executable), "--smoke-test", "--smoke-test-report", str(report)],
            cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, errors="replace",
        )
        try:
            stdout, stderr = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            # A windowed runtime-hook error can open a dialog before Python starts.
            if os.name == "nt":
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               capture_output=True, check=False)
            else:
                process.kill()
            process.communicate()
            raise RuntimeError(f"Executable smoke test timed out after {timeout}s")
    if stdout:
        print(stdout)
    if stderr:
        print(stderr)
    if not report.exists():
        raise RuntimeError(f"Executable exited with {process.returncode} without a smoke report; check runtime hooks/DLLs")
    result = json.loads(report.read_text(encoding="utf-8"))
    print(json.dumps(result, indent=2))
    if process.returncode != 0 or result.get("status") != "passed" or result.get("frozen") is not True:
        raise RuntimeError("Packaged executable failed its smoke test; see the report above")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    run(args.executable, args.report)
