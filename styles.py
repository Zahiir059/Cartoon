from PySide6.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QScrollArea, QFrame
from PySide6.QtCore import Qt
from .home import StyleCard
from ..widgets import label, GradientButton
from ..styles_data import STYLES


class StylesPage(QScrollArea):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx; self.setWidgetResizable(True); self.setFrameShape(QFrame.NoFrame)
        root = QWidget(); self.setWidget(root)
        v = QVBoxLayout(root); v.setContentsMargins(28, 22, 28, 28); v.setSpacing(14)
        v.addWidget(label("Animation Styles", "h1"))
        v.addWidget(label("Choose the look of your cartoon. The style adds a tuned prompt that guides the AI model; "
                          "you can extend it with your own prompt in the AI Studio.", "sub", True))
        g = QGridLayout(); g.setSpacing(16); self.cards = []
        for i, s in enumerate(STYLES):
            c = StyleCard(s[0], active=(s[0] == ctx.selected_style)); c.selected.connect(self.pick)
            g.addWidget(c, i // 4, i % 4); self.cards.append(c)
        for i in range(4):
            g.setColumnStretch(i, 1)
        v.addLayout(g)
        self.go = GradientButton("Continue to AI Studio", "sparkle"); self.go.setFixedWidth(280)
        self.go.clicked.connect(lambda: ctx.navigate.emit("studio"))
        v.addWidget(self.go, 0, Qt.AlignRight); v.addStretch()
        ctx.style_changed.connect(self.sync)

    def pick(self, sid):
        self.ctx.select_style(sid)

    def sync(self, sid):
        for c in self.cards:
            c.set_active(c.sid == sid)
