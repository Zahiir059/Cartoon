import threading
from PySide6.QtCore import QThread, Signal
from .providers import ProviderError


class FuncWorker(QThread):
    """Runs fn(progress_cb, cancel_event) off the UI thread."""
    progress = Signal(int, str)
    done = Signal(object)
    failed = Signal(str, bool)   # message, retryable

    def __init__(self, fn, parent=None):
        super().__init__(parent)
        self.fn = fn
        self.cancel_event = threading.Event()

    def cancel(self):
        self.cancel_event.set()

    def run(self):
        try:
            res = self.fn(lambda p, m="": self.progress.emit(int(p), m), self.cancel_event)
            self.done.emit(res)
        except ProviderError as e:
            self.failed.emit(str(e), e.retryable)
        except Exception as e:  # noqa
            self.failed.emit(str(e) or e.__class__.__name__, False)
