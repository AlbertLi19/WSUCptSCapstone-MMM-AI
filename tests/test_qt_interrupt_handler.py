"""Check real SIGINT delivery in an isolated Qt event loop."""

import os
from pathlib import Path
import subprocess
import sys

import pytest

pytest.importorskip("PyQt5")


@pytest.mark.parametrize("busy", [False, True])
def test_interrupt_closes_after_model_work_and_restores_handler(busy):
    app_path = Path(__file__).resolve().parents[1] / "src/app"
    script = '''
import os
import signal
import sys
import time
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from utility.qt_interrupt_handler import QtInterruptHandler

app = QApplication([])
window = QMainWindow()
figure = Figure()
canvas = FigureCanvasQTAgg(figure)
figure.subplots().plot([0, 1, 2], [0, 2, 3])
window.setCentralWidget(canvas)
window.show()
state = {"busy": sys.argv[1] == "True", "closed": False}
started = time.monotonic()
previous = signal.getsignal(signal.SIGINT)

def close():
    assert not state["busy"]
    if sys.argv[1] == "True":
        assert time.monotonic() - started >= 0.25
    state["closed"] = True
    window.close()

with QtInterruptHandler(app, close, lambda: not state["busy"]):
    QTimer.singleShot(25, lambda: os.kill(os.getpid(), signal.SIGINT))
    QTimer.singleShot(75, lambda: os.kill(os.getpid(), signal.SIGINT))
    QTimer.singleShot(250, lambda: state.update(busy=False))
    QTimer.singleShot(2000, app.quit)
    canvas.draw_idle()
    app.exec()

assert state["closed"], "SIGINT did not close the window"
assert signal.getsignal(signal.SIGINT) == previous
'''
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONPATH=str(app_path))
    result = subprocess.run(
        [sys.executable, "-c", script, str(busy)],
        env=env, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "KeyboardInterrupt" not in result.stderr
