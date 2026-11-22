import os, sys, subprocess
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QLineEdit, QMessageBox, QFileDialog)
from .. import secrets_store, theme, paths, media, APP_NAME, APP_VERSION
from ..providers import ReplicateProvider, ProviderError
from ..widgets import Card, GradientButton, SmallButton, label


class SettingsPage(QScrollArea):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx; self.setWidgetResizable(True); self.setFrameShape(QFrame.NoFrame)
        root = QWidget(); self.setWidget(root)
        v = QVBoxLayout(root); v.setContentsMargins(28, 22, 28, 28); v.setSpacing(16)
        v.addWidget(label("Settings", "h1"))

        # appearance
        c = Card(); l = QVBoxLayout(c); l.setContentsMargins(20, 16, 20, 18)
        l.addWidget(label("Appearance", "h2")); r = QHBoxLayout()
        self.dark, self.light = SmallButton("🌙  Dark mode"), SmallButton("☀️  Light mode")
        for b in (self.dark, self.light):
            r.addWidget(b)
        r.addStretch(); l.addLayout(r); v.addWidget(c)
        self.dark.clicked.connect(lambda: self.set_theme("dark")); self.light.clicked.connect(lambda: self.set_theme("light"))

        # AI provider
        c = Card(); l = QVBoxLayout(c); l.setContentsMargins(20, 16, 20, 18); l.setSpacing(8)
        l.addWidget(label("AI service (Replicate)", "h2"))
        self.state = label("", "banner", True); l.addWidget(self.state)
        l.addWidget(label("Cartoon AI sends your selected clip to a cloud video-to-video model and downloads the result. This needs an internet "
                          "connection and a Replicate account (usage is billed by Replicate). Get a key at replicate.com/account/api-tokens, "
                          "paste it below and press Save. The key is stored in the Windows Credential Manager — never in a file or in the app.", "sub", True))
        self.key = QLineEdit(); self.key.setEchoMode(QLineEdit.Password); self.key.setPlaceholderText("r8_…  (paste your Replicate API token)")
        self.key.setMinimumHeight(38); l.addWidget(self.key)
        r = QHBoxLayout(); sv = GradientButton("Save key", "check", height=40); rm = SmallButton("Remove key", "trash", danger=True)
        ts = SmallButton("Test connection", "refresh"); ob = SmallButton("Get a key ↗")
        for b in (sv, ts, rm, ob):
            r.addWidget(b)
        r.addStretch(); l.addLayout(r)
        l.addWidget(label("Model (owner/name or owner/name:version)", "sub")); self.model = QLineEdit(ctx.settings.get("model")); self.model.setMinimumHeight(38)
        self.model.editingFinished.connect(lambda: ctx.settings.set("model", self.model.text().strip()))
        l.addWidget(self.model); v.addWidget(c)
        sv.clicked.connect(self.save_key); rm.clicked.connect(self.remove_key); ts.clicked.connect(self.test)
        ob.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://replicate.com/account/api-tokens")))

        # storage
        c = Card(); l = QVBoxLayout(c); l.setContentsMargins(20, 16, 20, 18); l.setSpacing(8)
        l.addWidget(label("Storage & tools", "h2"))
        ff = paths.ffmpeg_exe()
        l.addWidget(label(f"FFmpeg: {'ready (bundled)' if ff else 'NOT FOUND'}", "sub"))
        l.addWidget(label(f"Library & database: {paths.data_dir()}", "sub", True))
        r = QHBoxLayout(); o = SmallButton("Open data folder", "folder"); cl = SmallButton("Clear temporary files", "trash")
        r.addWidget(o); r.addWidget(cl); r.addStretch(); l.addLayout(r); v.addWidget(c); v.addStretch()
        o.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(paths.data_dir()))))
        cl.clicked.connect(lambda: (paths.clean_temp(), QMessageBox.information(self, APP_NAME, "Temporary files cleared.")))
        self.theme_cb = None; self.refresh()

    def set_theme(self, m):
        self.ctx.settings.set("theme", m); self.theme_cb(m) if self.theme_cb else None

    def refresh(self):
        prov = self.ctx.provider()
        if prov.is_demo:
            self.state.setObjectName("banner"); self.state.setText("🎭  Demo Mode is active — no API key configured. Outputs are placeholders, not AI generated.")
        else:
            self.state.setObjectName("banner_ok"); self.state.setText("✅  API key found. Real AI generation is enabled.")
        self.state.style().unpolish(self.state); self.state.style().polish(self.state)

    def save_key(self):
        t = self.key.text().strip()
        if not t:
            return
        where = secrets_store.set_token(t); self.key.clear(); self.refresh()
        QMessageBox.information(self, APP_NAME, "Key saved to the Windows Credential Manager." if where == "vault"
                                else "No secure credential store available — the key is kept in memory for this session only.")

    def remove_key(self):
        secrets_store.delete_token(); self.refresh()

    def test(self):
        try:
            ReplicateProvider(self.ctx.settings).test_connection()
            QMessageBox.information(self, APP_NAME, "Connection successful — the key is valid.")
        except ProviderError as e:
            QMessageBox.warning(self, APP_NAME, str(e))
