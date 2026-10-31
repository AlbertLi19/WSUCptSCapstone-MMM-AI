"""Ensure release checks reject broken executables and preserve useful errors."""

import importlib.util
import json
import os
from pathlib import Path
import sys

import pytest

import bundle_smoke_test


def test_missing_import_is_reported_with_failing_stage(tmp_path, monkeypatch):
    def checks(check):
        def broken_import():
            raise ModuleNotFoundError("No module named 'backports'")
        check("packaging", broken_import)

    monkeypatch.setattr(bundle_smoke_test, "run_checks", checks)
    report = tmp_path / "report.json"
    assert bundle_smoke_test.main(["--smoke-test-report", str(report)]) == 1
    result = json.loads(report.read_text())
    assert result["status"] == "failed"
    assert result["current_check"] == "packaging"
    assert "No module named 'backports'" in result["traceback"]


runner_path = Path(__file__).resolve().parents[1] / "scripts/smoke_test_executable.py"
spec = importlib.util.spec_from_file_location("smoke_runner", runner_path)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


@pytest.fixture
def executable(tmp_path):
    if os.name == "nt":
        pytest.skip("Fake executable uses a POSIX shebang; real EXE is tested by the release job")

    def create(code):
        path = tmp_path / "fake-app"
        path.write_text(f"#!{sys.executable}\n" + code)
        path.chmod(0o755)
        return path
    return create


def test_executable_runs_outside_checkout_with_isolated_profile(tmp_path, executable, monkeypatch):
    monkeypatch.setenv("PYTHONPATH", str(Path.cwd()))
    app = executable('''
import json, os, pathlib, sys
assert pathlib.Path.cwd() != pathlib.Path(sys.argv[0]).parent
assert "PYTHONPATH" not in os.environ
assert "PYTHONHOME" not in os.environ
assert os.environ["HF_HUB_OFFLINE"] == "1"
assert pathlib.Path(os.environ["LOCALAPPDATA"]).is_relative_to(pathlib.Path.cwd())
pathlib.Path(sys.argv[-1]).write_text(json.dumps({"status": "passed", "frozen": True}))
''')
    runner.run(app, tmp_path / "report.json")


@pytest.mark.parametrize("status,frozen,exit_code", [
    ("failed", True, 1), ("passed", True, 1), ("passed", False, 0), ("running", True, 0),
])
def test_rejects_failure_nonfrozen_or_incomplete_report(tmp_path, executable, status, frozen, exit_code):
    result = json.dumps({"status": status, "frozen": frozen})
    app = executable(f"import pathlib, sys\npathlib.Path(sys.argv[-1]).write_text({result!r})\nsys.exit({exit_code})\n")
    with pytest.raises(RuntimeError, match="failed its smoke test"):
        runner.run(app, tmp_path / "report.json")


def test_runtime_hook_crash_cannot_reuse_stale_success(tmp_path, executable):
    report = tmp_path / "report.json"
    report.write_text('{"status": "passed", "frozen": true}')
    app = executable("raise ModuleNotFoundError(\"No module named 'backports'\")\n")
    with pytest.raises(RuntimeError, match="without a smoke report"):
        runner.run(app, report)
    assert not report.exists()


def test_hung_executable_fails_with_timeout(tmp_path, executable):
    app = executable("import time\ntime.sleep(30)\n")
    with pytest.raises(RuntimeError, match="timed out"):
        runner.run(app, tmp_path / "report.json", timeout=0.1)
