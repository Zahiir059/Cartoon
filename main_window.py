from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QColor, QRadialGradient, QLinearGradient, QFont, QPixmap, QIcon
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton, QStackedWidget,
                               QButtonGroup, QMenu, QApplication)
from . import theme, icons, art, paths, APP_NAME
from .context import Ctx
from .widgets import IconButton, SmallButton, VideoPlayer, GradientButton
from .pages.home import HomePage
from .pages.studio import StudioPage
from .pages.styles import StylesPage
from .pages.editor import EditorPage
from .pages.library import CreationsPage, PreviewDialog
from .pages.settings import SettingsPage
from .pages.about import AboutPage
from .theme import PURPLE, VIOLET, BLUE, CYAN, PINK
from . import media

NAV = [("home", "Home Dashboard", "home"), ("studio", "AI Video Studio", "studio"), ("styles", "Animation Styles", "styles"),
       ("editor", "Video Editor", "editor"), ("creations", "My Creations", "folder"), ("settings", "Settings", "settings"),
       ("about", "About", "info")]


class Root(QWidget):
    def paintEvent(self, e):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(theme.c("bg")))
        g = QRadialGradient(self.width() * .85, 0, self.width() * .55)
        g.setColorAt(0, QColor(139, 92, 246, 55 if theme.mode() == "dark" else 40)); g.setColorAt(1, QColor(139, 92, 246, 0))
        p.fillRect(self.rect(), g)
        g2 = QRadialGradient(0, self.height(), self.width() * .45)
        g2.setColorAt(0, QColor(236, 72, 153, 35 if theme.mode() == "dark" else 25)); g2.setColorAt(1, QColor(236, 72, 153, 0))
        p.fillRect(self.rect(), g2)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ctx = Ctx()
        theme.set_mode(self.ctx.settings.get("theme"))
        self.setWindowTitle(f"{APP_NAME} — Turn Your Videos Into Art"); self.resize(1360, 860); self.setMinimumSize(1100, 700)
        self.setWindowIcon(QIcon(art.render_style_art("anime", 128, 128))); self.setAcceptDrops(True)
        root = Root(); root.setObjectName("root"); self.setCentralWidget(root)
        outer = QVBoxLayout(root); outer.setContentsMargins(0, 0, 0, 0); outer.setSpacing(0)

        # header
        hd = QFrame(); hd.setObjectName("header"); hd.setFixedHeight(66); h = QHBoxLayout(hd); h.setContentsMargins(22, 0, 18, 0)
        logo = QLabel(); logo.setPixmap(art.render_style_art("anime", 80, 80).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setStyleSheet("border-radius:12px;")
        name = QLabel(f'<span style="font-size:21px;font-weight:900;color:{PINK};">Cartoon</span>'
                      f'<span style="font-size:21px;font-weight:900;color:{VIOLET};"> AI</span>')
        sub = QLabel("Premium AI Video Studio"); sub.setObjectName("sub")
        h.addWidget(logo); h.addSpacing(8); h.addWidget(name); h.addSpacing(10); h.addWidget(sub); h.addStretch()
        self.theme_btn = IconButton("sun", "Toggle dark / light mode", 22); self.set_btn = IconButton("settings", "Settings", 22)
        self.prof_btn = IconButton("user", "Profile", 22)
        for b in (self.theme_btn, self.set_btn, self.prof_btn):
            h.addWidget(b)
        outer.addWidget(hd)

        body = QHBoxLayout(); body.setSpacing(0); outer.addLayout(body, 1)
        sb = QFrame(); sb.setObjectName("sidebar"); sb.setFixedWidth(240); s = QVBoxLayout(sb); s.setContentsMargins(0, 18, 0, 18); s.setSpacing(4)
        self.group = QButtonGroup(self); self.group.setExclusive(True); self.nav = {}
        for i, (key, title, ic) in enumerate(NAV):
            b = QPushButton("   " + title); b.setObjectName("nav"); b.setCheckable(True); b.setCursor(Qt.PointingHandCursor)
            b.setIconSize(QSize(22, 22)); b.setMinimumHeight(48); self.group.addButton(b, i); s.addWidget(b); self.nav[key] = (b, ic)
            b.clicked.connect(lambda _, k=key: self.go(k))
        s.addStretch()
        self.mode_lbl = QLabel(); self.mode_lbl.setWordWrap(True); self.mode_lbl.setContentsMargins(18, 0, 14, 0); self.mode_lbl.setObjectName("sub")
        s.addWidget(self.mode_lbl); body.addWidget(sb)

        self.stack = QStackedWidget(); body.addWidget(self.stack, 1)
        ctx = self.ctx
        self.pages = {}
        def preview(p):
            PreviewDialog(p, self).exec()
        self.pages["home"] = HomePage(ctx, preview); self.pages["studio"] = StudioPage(ctx); self.pages["styles"] = StylesPage(ctx)
        self.pages["editor"] = EditorPage(ctx); self.pages["creations"] = CreationsPage(ctx, preview)
        self.pages["settings"] = SettingsPage(ctx); self.pages["about"] = AboutPage(ctx)
        self.pages["settings"].theme_cb = self.set_theme
        for k, _, _ in NAV:
            self.stack.addWidget(self.pages[k])

        ctx.navigate.connect(self.go)
        ctx.open_studio.connect(lambda f: (self.go("studio"), self.pages["studio"].load_video(f)))
        ctx.open_editor.connect(lambda f, pid: (self.go("editor"), self.pages["editor"].load(f, pid)))
        ctx.release.connect(lambda: (self.pages["studio"].release_files(), self.pages["editor"].release_files()))
        self.theme_btn.clicked.connect(lambda: self.set_theme("light" if theme.mode() == "dark" else "dark"))
        self.set_btn.clicked.connect(lambda: self.go("settings"))
        self.prof_btn.clicked.connect(self.profile_menu)
        self.apply_theme(); self.go("home")

    def go(self, key):
        self.stack.setCurrentWidget(self.pages[key])
        self.nav[key][0].setChecked(True)
        pg = self.pages[key]
        if hasattr(pg, "refresh"):
            pg.refresh()
        self._mode_label()

    def _mode_label(self):
        prov = self.ctx.provider()
        self.mode_lbl.setText("🎭 Demo Mode\nNo AI service connected" if prov.is_demo else "🟢 AI service connected")

    def set_theme(self, m):
        self.ctx.settings.set("theme", m); theme.set_mode(m); self.apply_theme()

    def apply_theme(self):
        QApplication.instance().setStyleSheet(theme.qss())
        self.theme_btn.set_name("sun" if theme.mode() == "dark" else "moon")
        for key, (b, ic) in self.nav.items():
            b.setIcon(icons.icon(ic, "#FFFFFF" if b.isChecked() else theme.c("sub"), 22))
        self.group.buttonToggled.connect(self._nav_icons) if not getattr(self, "_conn", False) else None
        self._conn = True
        for w in self.findChildren(IconButton) + self.findChildren(SmallButton) + self.findChildren(VideoPlayer):
            w.refresh()
        for pg in self.pages.values():
            if hasattr(pg, "refresh"):
                pg.refresh()
        self.centralWidget().update()

    def _nav_icons(self, *_):
        for key, (b, ic) in self.nav.items():
            b.setIcon(icons.icon(ic, "#FFFFFF" if b.isChecked() else theme.c("sub"), 22))

    def profile_menu(self):
        m = QMenu(self); m.addAction("Local profile — no account needed").setEnabled(False)
        m.addAction("Settings").triggered.connect(lambda: self.go("settings")); m.addAction("About").triggered.connect(lambda: self.go("about"))
        m.exec(self.prof_btn.mapToGlobal(self.prof_btn.rect().bottomLeft()))

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        for u in e.mimeData().urls():
            if u.isLocalFile() and u.toLocalFile().lower().endswith(tuple(media.VIDEO_EXTS)):
                self.ctx.open_studio.emit(u.toLocalFile()); break

    def closeEvent(self, e):
        self.ctx.release.emit()
        paths.clean_temp()
        super().closeEvent(e)
