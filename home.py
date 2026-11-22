import os
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap, QFont
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QGridLayout, QFrame, QPushButton)
from .. import art, icons, theme
from ..widgets import Card, GradientButton, GradientBox, SmallButton, label, clear_layout, CoverLabel
from ..styles_data import STYLES, STYLE_BY_ID, POPULAR
from ..theme import PURPLE, VIOLET, BLUE, CYAN, PINK


class ActionCard(Card):
    clicked = Signal()

    def __init__(self, icon_name, title, desc, accent):
        super().__init__()
        self.setCursor(Qt.PointingHandCursor); self.setMinimumHeight(110)
        lay = QHBoxLayout(self); lay.setContentsMargins(18, 14, 18, 14); lay.setSpacing(14)
        ic = QLabel(); ic.setFixedSize(52, 52); ic.setAlignment(Qt.AlignCenter)
        ic.setStyleSheet(f"background:qlineargradient(x1:0,y1:0,x2:1,y2:1,stop:0 {accent[0]},stop:1 {accent[1]});border-radius:16px;")
        ic.setPixmap(icons.pix(icon_name, "#FFFFFF", 28))
        col = QVBoxLayout(); col.setSpacing(2)
        t = label(title); t.setStyleSheet("font-size:15px;font-weight:700;"); d = label(desc, "sub", True)
        col.addStretch(); col.addWidget(t); col.addWidget(d); col.addStretch()
        lay.addWidget(ic); lay.addLayout(col, 1)

    def mousePressEvent(self, e):
        self.clicked.emit()


class StyleCard(Card):
    selected = Signal(str)

    def __init__(self, sid, compact=False, active=False):
        super().__init__()
        s = STYLE_BY_ID[sid]; self.sid = sid
        lay = QVBoxLayout(self); lay.setContentsMargins(10, 10, 10, 12); lay.setSpacing(6)
        lay.addWidget(CoverLabel(art.render_style_art(sid, 360, 200), 150 if not compact else 110, smooth=(sid != "pixel")))
        n = label(s[1]); n.setStyleSheet("font-size:15px;font-weight:700;")
        lay.addWidget(n)
        if not compact:
            d = label(s[2], "sub", True); d.setMinimumHeight(36); lay.addWidget(d)
        self.btn = SmallButton("Select style")
        self.btn.clicked.connect(lambda: self.selected.emit(sid))
        lay.addWidget(self.btn)
        self.set_active(active)

    def set_active(self, a):
        self.btn.setText("✓ Selected" if a else "Select style")
        self.setStyleSheet(f"QFrame#card{{border:2px solid {PINK if a else theme.c('border')};}}")

    def mousePressEvent(self, e):
        self.selected.emit(self.sid)


class ProjectCard(Card):
    def __init__(self, ctx, p, on_preview, on_edit, extra=None):
        super().__init__()
        lay = QVBoxLayout(self); lay.setContentsMargins(10, 10, 10, 12); lay.setSpacing(6)
        pm = QPixmap(p["thumb"]) if p.get("thumb") and os.path.isfile(p["thumb"]) else None
        lay.addWidget(CoverLabel(pm, 120))
        n = label(p["name"] or "Untitled"); n.setStyleSheet("font-weight:700;font-size:14px;")
        lay.addWidget(n)
        chips = QHBoxLayout(); chips.setSpacing(6)
        st = p["status"] or ""
        for txt, col in ((p["style"] or "", VIOLET), (st, CYAN if st == "Completed" else (PINK if st == "Failed" else BLUE)),
                         ("DEMO" if p.get("demo") else "", PINK)):
            if txt:
                c = QLabel(txt); c.setObjectName("chip")
                c.setStyleSheet(f"background:{theme.c('card2')};color:{col};border-radius:10px;padding:3px 10px;font-size:11px;font-weight:700;")
                chips.addWidget(c)
        chips.addStretch(); lay.addLayout(chips)
        row = QHBoxLayout(); row.setSpacing(6)
        b1 = SmallButton("Preview", "play"); b2 = SmallButton("Edit", "edit")
        b1.clicked.connect(lambda: on_preview(p)); b2.clicked.connect(lambda: on_edit(p))
        ok = bool(p.get("output_path") and os.path.isfile(p["output_path"]))
        b1.setEnabled(ok); b2.setEnabled(ok)
        row.addWidget(b1); row.addWidget(b2)
        if extra:
            for w in extra(p):
                row.addWidget(w)
        row.addStretch(); lay.addLayout(row)


class HomePage(QScrollArea):
    def __init__(self, ctx, preview_cb):
        super().__init__()
        self.ctx, self.preview_cb = ctx, preview_cb
        self.setWidgetResizable(True); self.setFrameShape(QFrame.NoFrame)
        root = QWidget(); self.setWidget(root)
        v = QVBoxLayout(root); v.setContentsMargins(28, 22, 28, 28); v.setSpacing(22)

        # ---- hero
        self.hero = GradientBox((PURPLE, VIOLET, PINK)); self.hero.setMinimumHeight(290)
        self.hero.art_fn = lambda w, h: art.render_hero(min(560, int(w * .5)), h)
        h = QHBoxLayout(self.hero); h.setContentsMargins(40, 30, 40, 30)
        col = QVBoxLayout(); col.setSpacing(10)
        tag = label("✨  AI VIDEO-TO-CARTOON STUDIO"); tag.setStyleSheet("font-size:11px;font-weight:800;letter-spacing:2px;color:#FFFFFFCC;")
        t = label("Turn Your Videos Into Art"); t.setStyleSheet("font-size:38px;font-weight:900;color:white;")
        d = label("Transform ordinary videos into extraordinary animations", wrap=True)
        d.setStyleSheet("font-size:16px;color:#FFFFFFDD;")
        self.cta = GradientButton("Create Cartoon Video", "sparkle", colors=(PINK, "#F472B6", BLUE), height=54)
        self.cta.setFixedWidth(280)
        col.addStretch(); col.addWidget(tag); col.addWidget(t); col.addWidget(d); col.addSpacing(8); col.addWidget(self.cta); col.addStretch()
        h.addLayout(col, 3); h.addStretch(2)
        v.addWidget(self.hero)
        self.cta.clicked.connect(lambda: ctx.navigate.emit("studio"))

        # ---- quick actions
        v.addWidget(label("Quick Actions", "h2"))
        g = QGridLayout(); g.setSpacing(16)
        acts = [("upload", "Upload Video", "Pick a clip from your computer (max 10 s for AI)", (BLUE, CYAN), lambda: ctx.navigate.emit("studio")),
                ("styles", "Choose Animation Style", "Browse all 15 looks", (VIOLET, PINK), lambda: ctx.navigate.emit("styles")),
                ("folder", "My Creations", "Your generated & saved videos", (PURPLE, VIOLET), lambda: ctx.navigate.emit("creations")),
                ("editor", "Video Editor", "Trim, crop, add text, music & more", (PINK, "#F97316"), lambda: ctx.navigate.emit("editor"))]
        for i, (ic, tt, dd, acc, fn) in enumerate(acts):
            c = ActionCard(ic, tt, dd, acc); c.clicked.connect(fn); g.addWidget(c, 0, i)
        v.addLayout(g)

        # ---- popular styles
        top = QHBoxLayout(); top.addWidget(label("Popular Styles", "h2")); top.addStretch()
        more = SmallButton("See all 15 →"); more.clicked.connect(lambda: ctx.navigate.emit("styles")); top.addWidget(more)
        v.addLayout(top)
        self.pop = QGridLayout(); self.pop.setSpacing(16)
        self.pop_cards = []
        for i, sid in enumerate(POPULAR):
            c = StyleCard(sid, compact=True, active=(sid == ctx.selected_style))
            c.selected.connect(self._pick); self.pop.addWidget(c, 0, i); self.pop_cards.append(c)
        v.addLayout(self.pop)

        # ---- recent
        v.addWidget(label("Recent Projects", "h2"))
        self.recent = QGridLayout(); self.recent.setSpacing(16); v.addLayout(self.recent); v.addStretch()
        ctx.projects_changed.connect(self.reload); ctx.style_changed.connect(self._sync)
        self.reload()

    def _pick(self, sid):
        self.ctx.select_style(sid); self.ctx.navigate.emit("studio")

    def _sync(self, sid):
        for c in self.pop_cards:
            c.set_active(c.sid == sid)

    def reload(self):
        clear_layout(self.recent)
        items = self.ctx.db.list(limit=4)
        if not items:
            card = Card(); l = QVBoxLayout(card); l.setContentsMargins(30, 30, 30, 30)
            m = label("No projects yet — upload a video in the AI Video Studio and your creations will appear here.", "sub", True)
            m.setAlignment(Qt.AlignCenter); l.addWidget(m); self.recent.addWidget(card, 0, 0, 1, 4); return
        for i, p in enumerate(items):
            self.recent.addWidget(ProjectCard(self.ctx, p, self.preview_cb,
                                              lambda pp: self.ctx.open_editor.emit(pp["output_path"], pp["id"])), 0, i)
        for i in range(4):
            self.recent.setColumnStretch(i, 1)

    def refresh(self):
        self.reload()
