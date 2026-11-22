import os
from PySide6.QtCore import Qt, QRectF, QPointF, QTimer, QUrl, Signal, QVariantAnimation, QSize
from PySide6.QtGui import (QPainter, QColor, QLinearGradient, QPen, QFont, QPixmap, QBrush, QConicalGradient,
                           QPainterPath)
from PySide6.QtWidgets import (QFrame, QPushButton, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSlider,
                               QGraphicsDropShadowEffect, QFileDialog, QSizePolicy, QGridLayout)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QMediaDevices
from PySide6.QtMultimediaWidgets import QVideoWidget
from . import theme, icons
from .theme import PURPLE, VIOLET, BLUE, CYAN, PINK


def fmt_time(ms):
    s = max(0, int(ms / 1000))
    return f"{s // 60}:{s % 60:02d}"


def shadow(w, blur=30, dy=8, alpha=90, color=(0, 0, 0)):
    e = QGraphicsDropShadowEffect(w)
    e.setBlurRadius(blur); e.setOffset(0, dy); e.setColor(QColor(*color, alpha))
    w.setGraphicsEffect(e)


class Card(QFrame):
    def __init__(self, parent=None, shadow_on=True, name="card"):
        super().__init__(parent)
        self.setObjectName(name)
        if shadow_on:
            shadow(self)


def label(text, name=None, wrap=False):
    l = QLabel(text)
    if name:
        l.setObjectName(name)
    l.setWordWrap(wrap)
    return l


class GradientButton(QPushButton):
    def __init__(self, text, icon_name=None, colors=(PINK, VIOLET, BLUE), parent=None, height=46):
        super().__init__(text, parent)
        self.colors, self.icon_name, self._g = colors, icon_name, 0.0
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(height)
        self.setFont(QFont(self.font().family(), 11, QFont.Bold))
        self.anim = QVariantAnimation(self, duration=180, valueChanged=self._set_glow)

    def _set_glow(self, v):
        self._g = v; self.update()

    def enterEvent(self, e):
        self.anim.stop(); self.anim.setStartValue(self._g); self.anim.setEndValue(1.0); self.anim.start()

    def leaveEvent(self, e):
        self.anim.stop(); self.anim.setStartValue(self._g); self.anim.setEndValue(0.0); self.anim.start()

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect()).adjusted(4, 4, -4, -4)
        rad = 14
        if self.isEnabled():
            for i in range(5):  # glow
                c = QColor(self.colors[1]); c.setAlpha(int((18 + 30 * self._g) / (i + 1)))
                p.setPen(Qt.NoPen); p.setBrush(c)
                p.drawRoundedRect(r.adjusted(-i * 1.6, -i * 1.6, i * 1.6, i * 1.6), rad + i, rad + i)
            g = QLinearGradient(r.topLeft(), r.topRight())
            for i, col in enumerate(self.colors):
                c = QColor(col)
                if self._g:
                    c = c.lighter(100 + int(15 * self._g))
                g.setColorAt(i / max(1, len(self.colors) - 1), c)
            p.setBrush(g)
        else:
            p.setBrush(QColor(theme.c("card2")))
        p.setPen(Qt.NoPen); p.drawRoundedRect(r, rad, rad)
        p.setPen(QColor("white") if self.isEnabled() else QColor(theme.c("sub")))
        x = r.left()
        if self.icon_name:
            pm = icons.pix(self.icon_name, "#FFFFFF" if self.isEnabled() else theme.c("sub"), 20)
            tw = self.fontMetrics().horizontalAdvance(self.text())
            x = r.center().x() - (tw + 30) / 2
            p.drawPixmap(int(x), int(r.center().y() - 10), pm)
            p.drawText(QRectF(x + 30, r.top(), tw + 10, r.height()), Qt.AlignVCenter | Qt.AlignLeft, self.text())
        else:
            p.drawText(r, Qt.AlignCenter, self.text())


class IconButton(QPushButton):
    def __init__(self, name, tip="", size=22, parent=None):
        super().__init__(parent)
        self.setObjectName("icon"); self.name, self.size_ = name, size
        self.setToolTip(tip); self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(size + 16, size + 16); self.refresh()

    def set_name(self, n):
        self.name = n; self.refresh()

    def refresh(self):
        from .icons import icon
        self.setIcon(icon(self.name, theme.c("text"), self.size_)); self.setIconSize(QSize(self.size_, self.size_))


class SmallButton(QPushButton):
    def __init__(self, text, icon_name=None, danger=False, parent=None):
        super().__init__(text, parent)
        self.setObjectName("danger" if danger else "small")
        if danger:
            self.setStyleSheet("padding:5px 10px;border-radius:8px;font-size:12px;")
        self.setCursor(Qt.PointingHandCursor); self.icon_name = icon_name; self.refresh()

    def refresh(self):
        if self.icon_name:
            self.setIcon(icons.icon(self.icon_name, theme.c("text"), 16))


class Spinner(QWidget):
    def __init__(self, size=28, parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size); self.a = 0
        self.t = QTimer(self, interval=25, timeout=self._tick)
        self.setVisible(False)

    def _tick(self):
        self.a = (self.a + 9) % 360; self.update()

    def start(self):
        self.setVisible(True); self.t.start()

    def stop(self):
        self.t.stop(); self.setVisible(False)

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        g = QConicalGradient(self.rect().center(), -self.a)
        g.setColorAt(0, QColor(PINK)); g.setColorAt(.5, QColor(VIOLET)); g.setColorAt(1, QColor(CYAN))
        p.setPen(QPen(QBrush(g), 3.5, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(self.rect().adjusted(4, 4, -4, -4), self.a * 16, 260 * 16)


class GradientBox(QFrame):
    """Rounded gradient panel used for the hero banner."""
    def __init__(self, colors=(PURPLE, VIOLET, PINK), radius=24, parent=None):
        super().__init__(parent)
        self.colors, self.radius = colors, radius
        self.pix = None
        self.art_fn = None

    def resizeEvent(self, e):
        if self.art_fn:
            self.pix = self.art_fn(self.width(), self.height())
        super().resizeEvent(e)

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        r = QRectF(self.rect())
        path = QPainterPath(); path.addRoundedRect(r, self.radius, self.radius)
        p.setClipPath(path)
        g = QLinearGradient(r.topLeft(), r.bottomRight())
        for i, c in enumerate(self.colors):
            g.setColorAt(i / (len(self.colors) - 1), QColor(c))
        p.fillRect(r, g)
        if self.pix is not None:
            p.drawPixmap(int(r.width() - self.pix.width()) , int(r.height() - self.pix.height()), self.pix)


class DropZone(QFrame):
    fileDropped = Signal(str)
    clicked = Signal()

    def __init__(self, text="Drag & drop a video here\nor click to browse", parent=None):
        super().__init__(parent)
        self.setObjectName("drop"); self.setAcceptDrops(True); self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(220)
        lay = QVBoxLayout(self); lay.setAlignment(Qt.AlignCenter)
        ic = QLabel(); ic.setPixmap(icons.pix("upload", VIOLET, 54)); ic.setAlignment(Qt.AlignCenter)
        t = QLabel(text); t.setAlignment(Qt.AlignCenter); t.setObjectName("sub")
        t.setStyleSheet("font-size:14px;")
        lay.addWidget(ic); lay.addWidget(t)

    def mousePressEvent(self, e):
        self.clicked.emit()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        for u in e.mimeData().urls():
            if u.isLocalFile():
                self.fileDropped.emit(u.toLocalFile()); break


class RangeBar(QWidget):
    """Timeline with a draggable window. maxlen (seconds) caps the window length (10 s for the AI)."""
    changed = Signal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dur, self.a, self.b, self.maxlen, self.drag, self.off = 1.0, 0.0, 1.0, None, None, 0
        self.setMinimumHeight(54); self.setCursor(Qt.PointingHandCursor)

    def set_duration(self, d, maxlen=None):
        self.dur, self.maxlen = d, maxlen
        self.a, self.b = 0.0, min(d, maxlen) if maxlen else d
        self.update(); self.changed.emit(self.a, self.b)

    def set_range(self, a, b):
        self.a, self.b = a, b; self.update(); self.changed.emit(a, b)

    def _x(self, t):
        return 12 + (self.width() - 24) * t / max(self.dur, 1e-6)

    def _t(self, x):
        return min(self.dur, max(0.0, (x - 12) / max(1, self.width() - 24) * self.dur))

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing)
        y, h = 14, 22
        p.setPen(Qt.NoPen); p.setBrush(QColor(theme.c("card2")))
        p.drawRoundedRect(QRectF(12, y, self.width() - 24, h), 8, 8)
        x1, x2 = self._x(self.a), self._x(self.b)
        g = QLinearGradient(x1, 0, x2, 0); g.setColorAt(0, QColor(PINK)); g.setColorAt(1, QColor(VIOLET))
        p.setBrush(g); p.drawRoundedRect(QRectF(x1, y, max(4, x2 - x1), h), 8, 8)
        p.setBrush(QColor("white"))
        for x in (x1, x2):
            p.drawRoundedRect(QRectF(x - 4, y - 5, 8, h + 10), 4, 4)
        p.setPen(QColor(theme.c("sub"))); p.setFont(QFont(self.font().family(), 8))
        p.drawText(QRectF(12, y + h + 6, 200, 14), Qt.AlignLeft, f"{self.a:.1f}s")
        p.drawText(QRectF(self.width() - 212, y + h + 6, 200, 14), Qt.AlignRight, f"{self.b:.1f}s")
        p.drawText(QRectF(0, y + h + 6, self.width(), 14), Qt.AlignCenter, f"selected {self.b - self.a:.1f}s of {self.dur:.1f}s")

    def mousePressEvent(self, e):
        x = e.position().x()
        if abs(x - self._x(self.a)) < 12: self.drag = "a"
        elif abs(x - self._x(self.b)) < 12: self.drag = "b"
        elif self._x(self.a) < x < self._x(self.b): self.drag, self.off = "m", self._t(x) - self.a
        else:
            self.drag, L = "m", self.b - self.a
            self.off = L / 2
            self.mouseMoveEvent(e)

    def mouseMoveEvent(self, e):
        if not self.drag:
            return
        t = self._t(e.position().x())
        if self.drag == "a":
            self.a = min(t, self.b - 0.1)
            if self.maxlen: self.a = max(self.a, self.b - self.maxlen)
        elif self.drag == "b":
            self.b = max(t, self.a + 0.1)
            if self.maxlen: self.b = min(self.b, self.a + self.maxlen)
        else:
            L = self.b - self.a
            self.a = min(max(0.0, t - self.off), self.dur - L); self.b = self.a + L
        self.update(); self.changed.emit(self.a, self.b)

    def mouseReleaseEvent(self, e):
        self.drag = None


class _NullAudio:
    def setMuted(self, m): self._m = m
    def isMuted(self): return getattr(self, "_m", False)


class VideoPlayer(QWidget):
    """Video + transport controls. controls=False gives a bare video surface (used for side-by-side)."""
    positionChanged = Signal(int)

    def __init__(self, controls=True, parent=None):
        super().__init__(parent)
        self.player = QMediaPlayer(self)
        self.audio = _NullAudio()
        if not os.environ.get("CARTOON_NO_AUDIO") and not QMediaDevices.defaultAudioOutput().isNull():   # PCs without any audio device must not crash
            self.audio = QAudioOutput(self); self.player.setAudioOutput(self.audio)
        self.video = QVideoWidget(); self.video.setMinimumSize(240, 150)
        self.video.setStyleSheet("background:#000;")
        self.player.setVideoOutput(self.video)
        self.path = None
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(6)
        lay.addWidget(self.video, 1)
        self.slider = QSlider(Qt.Horizontal); self.time = QLabel("0:00 / 0:00"); self.time.setObjectName("sub")
        self.play_btn = IconButton("play", "Play / pause", 18)
        self.mute_btn = IconButton("volume", "Mute", 18)
        self.full_btn = IconButton("fullscreen", "Full screen", 18)
        row = QHBoxLayout(); row.setSpacing(4)
        for w in (self.play_btn, self.slider, self.time, self.mute_btn, self.full_btn):
            row.addWidget(w)
        self.bar = QWidget(); self.bar.setLayout(row); row.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.bar); self.bar.setVisible(controls)
        self.play_btn.clicked.connect(self.toggle)
        self.mute_btn.clicked.connect(lambda: self.audio.setMuted(not self.audio.isMuted()))
        self.full_btn.clicked.connect(lambda: self.video.setFullScreen(True))
        self.slider.sliderMoved.connect(self.player.setPosition)
        self.player.positionChanged.connect(self._pos)
        self.player.durationChanged.connect(lambda d: self.slider.setRange(0, d))
        self.player.playbackStateChanged.connect(
            lambda s: self.play_btn.set_name("pause" if s == QMediaPlayer.PlayingState else "play"))

    def _pos(self, p):
        if not self.slider.isSliderDown():
            self.slider.setValue(p)
        self.time.setText(f"{fmt_time(p)} / {fmt_time(self.player.duration())}")
        self.positionChanged.emit(p)

    def set_source(self, path):
        self.path = path
        self.player.setSource(QUrl.fromLocalFile(path) if path else QUrl())
        if path:
            self.player.pause()

    def clear(self):
        self.player.stop(); self.set_source(None)

    def toggle(self):
        if self.player.playbackState() == QMediaPlayer.PlayingState:
            self.player.pause()
        else:
            self.player.play()

    def refresh(self):
        for b in (self.play_btn, self.mute_btn, self.full_btn):
            b.refresh()


class CompareView(QWidget):
    """Original and cartoon side by side, driven by one transport bar."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.a, self.b = VideoPlayer(False), VideoPlayer(False)
        self.b.audio.setMuted(True)
        lay = QVBoxLayout(self); lay.setContentsMargins(0, 0, 0, 0)
        row = QHBoxLayout()
        for cap, w in (("Original", self.a), ("Cartoon", self.b)):
            col = QVBoxLayout(); l = QLabel(cap); l.setObjectName("chip"); l.setAlignment(Qt.AlignCenter)
            col.addWidget(l, 0, Qt.AlignHCenter); col.addWidget(w, 1); row.addLayout(col)
        lay.addLayout(row, 1)
        self.play = IconButton("play", "Play both", 18); self.slider = QSlider(Qt.Horizontal)
        bar = QHBoxLayout(); bar.addWidget(self.play); bar.addWidget(self.slider); lay.addLayout(bar)
        self.play.clicked.connect(self.toggle)
        self.a.player.durationChanged.connect(lambda d: self.slider.setRange(0, d))
        self.a.player.positionChanged.connect(lambda p: None if self.slider.isSliderDown() else self.slider.setValue(p))
        self.slider.sliderMoved.connect(lambda v: (self.a.player.setPosition(v), self.b.player.setPosition(v)))

    def set_sources(self, orig, cartoon):
        self.a.set_source(orig); self.b.set_source(cartoon)

    def toggle(self):
        if self.a.player.playbackState() == QMediaPlayer.PlayingState:
            self.a.player.pause(); self.b.player.pause(); self.play.set_name("play")
        else:
            self.b.player.setPosition(self.a.player.position())
            self.a.player.play(); self.b.player.play(); self.play.set_name("pause")

    def clear(self):
        self.a.clear(); self.b.clear()


def pick_file(parent, title, filt):
    f, _ = QFileDialog.getOpenFileName(parent, title, "", filt)
    return f


def clear_layout(layout):
    """Remove and dispose of every widget in a layout immediately (hidden + unparented first)."""
    while layout.count():
        it = layout.takeAt(0)
        w = it.widget()
        if w:
            w.hide(); w.setParent(None); w.deleteLater()


class CoverLabel(QWidget):
    """Image that fills its box (center-cropped, rounded) without ever forcing a minimum width."""
    def __init__(self, pix=None, height=140, radius=12, smooth=True, placeholder="No thumbnail"):
        super().__init__()
        self.pix, self.radius, self.smooth, self.ph = pix, radius, smooth, placeholder
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.Antialiasing); p.setRenderHint(QPainter.SmoothPixmapTransform, self.smooth)
        path = QPainterPath(); path.addRoundedRect(QRectF(self.rect()), self.radius, self.radius); p.setClipPath(path)
        if self.pix is None or self.pix.isNull():
            p.fillRect(self.rect(), QColor(theme.c("card2"))); p.setPen(QColor(theme.c("sub")))
            p.drawText(self.rect(), Qt.AlignCenter, self.ph); return
        sc = max(self.width() / self.pix.width(), self.height() / self.pix.height())
        w, h = self.pix.width() * sc, self.pix.height() * sc
        p.drawPixmap(QRectF((self.width() - w) / 2, (self.height() - h) / 2, w, h), self.pix, QRectF(self.pix.rect()))
