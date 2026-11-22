import os, shutil
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame, QGridLayout, QLineEdit, QPushButton,
                               QDialog, QTabWidget, QInputDialog, QMessageBox, QFileDialog, QButtonGroup)
from .home import ProjectCard
from .. import theme
from ..widgets import clear_layout, SmallButton, VideoPlayer, CompareView, label, Card, GradientButton, IconButton


class PreviewDialog(QDialog):
    def __init__(self, p, parent=None):
        super().__init__(parent)
        self.setWindowTitle(p["name"]); self.resize(900, 600)
        l = QVBoxLayout(self); tabs = QTabWidget(); l.addWidget(tabs)
        self.players = []
        out, orig = p.get("output_path"), p.get("original_path")
        has_o, has_c = bool(orig and os.path.isfile(orig)), bool(out and os.path.isfile(out))
        if has_c:
            a = VideoPlayer(); a.set_source(out); tabs.addTab(a, "Result"); self.players.append(a)
        if has_o:
            b = VideoPlayer(); b.set_source(orig); tabs.addTab(b, "Original"); self.players.append(b)
        if has_o and has_c:
            c = CompareView(); c.set_sources(orig, out); tabs.addTab(c, "Side by side"); self.players.append(c)

    def done(self, r):
        for p in self.players:
            p.clear()
        super().done(r)


class CreationsPage(QScrollArea):
    def __init__(self, ctx, preview_cb):
        super().__init__()
        self.ctx, self.filt = ctx, "all"
        self.setWidgetResizable(True); self.setFrameShape(QFrame.NoFrame)
        root = QWidget(); self.setWidget(root)
        v = QVBoxLayout(root); v.setContentsMargins(28, 22, 28, 28); v.setSpacing(14)
        v.addWidget(label("My Creations", "h1"))
        row = QHBoxLayout(); self.search = QLineEdit(); self.search.setPlaceholderText("🔍  Search by name or style…"); self.search.setMinimumHeight(38)
        row.addWidget(self.search, 1); self.btns = {}
        grp = QButtonGroup(self)
        for key, txt in (("all", "All"), ("generated", "AI generated"), ("originals", "Originals"), ("edited", "Edited"), ("favorites", "Favorites")):
            b = QPushButton(txt); b.setCheckable(True); b.setCursor(Qt.PointingHandCursor); grp.addButton(b); row.addWidget(b); self.btns[key] = b
            b.clicked.connect(lambda _, k=key: self._set(k))
        self.btns["all"].setChecked(True); v.addLayout(row)
        self.grid = QGridLayout(); self.grid.setSpacing(16); v.addLayout(self.grid); v.addStretch()
        self.search.textChanged.connect(self.reload); ctx.projects_changed.connect(self.reload)
        self.preview_cb = lambda p: self.preview(p); self.reload()

    def _set(self, k):
        self.filt = k; self.reload()

    def preview(self, p):
        PreviewDialog(p, self).exec()

    def reload(self):
        clear_layout(self.grid)
        items = self.ctx.db.list(self.search.text().strip(), self.filt)
        if not items:
            m = label("Nothing here yet.", "sub"); m.setAlignment(Qt.AlignCenter); self.grid.addWidget(m, 0, 0); return
        cols = 4
        for i, p in enumerate(items):
            self.grid.addWidget(ProjectCard(self.ctx, p, self.preview_cb, lambda pp: self.ctx.open_editor.emit(pp["output_path"], pp["id"]),
                                            extra=self._extra), i // cols, i % cols)
        for i in range(cols):
            self.grid.setColumnStretch(i, 1)

    def _extra(self, p):
        fav = IconButton("heart_fill" if p["favorite"] else "heart", "Favorite", 16)
        fav.clicked.connect(lambda: (self.ctx.db.update(p["id"], favorite=0 if p["favorite"] else 1), self.reload()))
        exp = IconButton("download", "Export a copy", 16); exp.clicked.connect(lambda: self.export(p))
        ren = IconButton("edit", "Rename", 16); ren.clicked.connect(lambda: self.rename(p))
        dele = IconButton("trash", "Delete", 16); dele.clicked.connect(lambda: self.delete(p))
        exp.setEnabled(bool(p.get("output_path") and os.path.isfile(p["output_path"])))
        return [fav, ren, exp, dele]

    def rename(self, p):
        n, ok = QInputDialog.getText(self, "Rename", "New name:", text=p["name"])
        if ok and n.strip():
            self.ctx.db.update(p["id"], name=n.strip()); self.reload()

    def export(self, p):
        f, _ = QFileDialog.getSaveFileName(self, "Export MP4", (p["name"] or "video") + ".mp4", "MP4 video (*.mp4)")
        if f:
            shutil.copyfile(p["output_path"], f)

    def delete(self, p):
        if QMessageBox.question(self, "Delete", f"Delete “{p['name']}” and its files?") == QMessageBox.Yes:
            self.ctx.release.emit()
            self.ctx.db.delete(p["id"]); self.reload(); self.ctx.projects_changed.emit()

    def refresh(self):
        self.reload()
