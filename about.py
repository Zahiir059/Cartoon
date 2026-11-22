from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QLabel
from .. import art, APP_NAME, APP_VERSION
from ..widgets import Card, label


class AboutPage(QScrollArea):
    def __init__(self, ctx):
        super().__init__()
        self.setWidgetResizable(True); self.setFrameShape(QFrame.NoFrame)
        root = QWidget(); self.setWidget(root); v = QVBoxLayout(root); v.setContentsMargins(28, 22, 28, 28); v.setSpacing(16)
        v.addWidget(label("About", "h1"))
        c = Card(); l = QVBoxLayout(c); l.setContentsMargins(26, 22, 26, 24); l.setSpacing(10)
        im = QLabel(); im.setPixmap(art.render_hero(420, 190)); im.setAlignment(Qt.AlignLeft); l.addWidget(im)
        l.addWidget(label(f"{APP_NAME}  ·  v{APP_VERSION}", "h2"))
        l.addWidget(label("A desktop studio that turns short real-life clips into cartoon and anime animations using a cloud video-to-video AI model, "
                          "with a built-in FFmpeg video editor.", wrap=True))
        l.addWidget(label("• AI transformation is limited to 10-second clips.\n"
                          "• AI generation needs an internet connection and your own Replicate API key; without a key the app runs in clearly-labelled Demo Mode.\n"
                          "• Which controls appear depends on what the connected model genuinely supports.\n"
                          "• Editing, trimming, effects, audio mixing and export run locally with FFmpeg and work offline.", "sub", True))
        v.addWidget(c); v.addStretch()
