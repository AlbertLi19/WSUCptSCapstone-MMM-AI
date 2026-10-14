"""Deliver terminal interrupts through Qt's normal window shutdown path."""

import signal

from PyQt5.QtCore import QTimer


class QtInterruptHandler:
    def __init__(self, app, close_window, can_close=lambda: True):
        self._close_window = close_window
        self._can_close = can_close
        self._requested = False
        self._previous_handler = None
        # Periodically return control to Python so signals are handled even
        # when Qt is idle. The signal handler itself only sets a flag.
        self._timer = QTimer(app)
        self._timer.setInterval(100)
        self._timer.timeout.connect(self._process_interrupt)

    def _request_interrupt(self, signum, frame):
        self._requested = True

    def _process_interrupt(self):
        if self._requested and self._can_close():
            self._requested = False
            self._close_window()

    def __enter__(self):
        self._previous_handler = signal.signal(signal.SIGINT, self._request_interrupt)
        self._timer.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._timer.stop()
        signal.signal(signal.SIGINT, self._previous_handler)
        self._timer.deleteLater()
