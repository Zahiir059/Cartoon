import os, time
from PySide6.QtCore import QObject, Signal
from .settings import Settings
from .db import DB
from .providers import active_provider
from .paths import thumbs_dir
from . import media


class Ctx(QObject):
    projects_changed = Signal()
    theme_changed = Signal()
    navigate = Signal(str)
    open_studio = Signal(str)
    open_editor = Signal(str, int)
    style_changed = Signal(str)
    release = Signal()

    def __init__(self):
        super().__init__()
        self.settings = Settings()
        self.db = DB()
        self.selected_style = "anime"

    def provider(self):
        return active_provider(self.settings)

    def select_style(self, sid):
        self.selected_style = sid
        self.style_changed.emit(sid)

    def make_thumb(self, video):
        out = str(thumbs_dir() / f"t{int(time.time() * 1000)}.jpg")
        try:
            media.thumbnail(video, out)
            return out
        except Exception:
            return ""
