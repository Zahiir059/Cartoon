"""Procedural cartoon artwork for style cards and the hero banner (no external image files)."""
import math, random
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import (QPixmap, QPainter, QColor, QLinearGradient, QRadialGradient, QPen, QBrush,
                           QPainterPath, QPolygonF, QFont)

# id: (bg1, bg2, skin, hair, iris, outline, fx)
PAL = {
    "anime": ("#8B5CF6", "#EC4899", "#FFE0CF", "#2A2A5A", "#22D3EE", None, "sparkle"),
    "cartoon3d": ("#3B82F6", "#22D3EE", "#FFC9A8", "#8B4A2B", "#3B2A1A", None, "gloss"),
    "cartoon2d": ("#FACC15", "#FB923C", "#FFD9B8", "#1F1F1F", "#1F1F1F", "#111111", "flat"),
    "manga": ("#F5F5F5", "#BDBDBD", "#FFFFFF", "#111111", "#111111", "#111111", "speed"),
    "comic": ("#FDE047", "#EF4444", "#FFD3B0", "#B45309", "#1D4ED8", "#111111", "halftone"),
    "cyberpunk": ("#1B0B3A", "#0E7490", "#E8C8FF", "#EC4899", "#22D3EE", None, "neon"),
    "fantasy": ("#312E81", "#A78BFA", "#FFE4D6", "#E5E7EB", "#34D399", None, "stars"),
    "watercolor": ("#FBCFE8", "#BAE6FD", "#FFE8DC", "#C084FC", "#60A5FA", None, "wash"),
    "clay": ("#FDBA74", "#F59E0B", "#F6B38E", "#7C3F1D", "#2B1B10", None, "clay"),
    "pixel": ("#22C55E", "#0EA5E9", "#FFD9B0", "#5B3A1E", "#111111", None, "pixel"),
    "retro": ("#F97316", "#0F766E", "#FDE6C8", "#222222", "#222222", "#222222", "rays"),
    "chibi": ("#F9A8D4", "#C4B5FD", "#FFE6D8", "#F472B6", "#7C3AED", None, "chibi"),
    "cinematic": ("#0F172A", "#B45309", "#F3CBB0", "#111827", "#38BDF8", None, "cine"),
    "pencil": ("#FAFAFA", "#D4D4D8", "#FFFFFF", "#52525B", "#52525B", "#3F3F46", "hatch"),
    "lowpoly": ("#6366F1", "#22D3EE", "#FFCFA8", "#1E3A8A", "#0EA5E9", None, "poly"),
}


def _bg(p, w, h, c1, c2):
    g = QLinearGradient(0, 0, w, h); g.setColorAt(0, QColor(c1)); g.setColorAt(1, QColor(c2))
    p.fillRect(0, 0, w, h, g)


def _char(p, cx, cy, r, skin, hair, iris, outline, chibi=False, gloss=False):
    pen = QPen(QColor(outline), max(1.5, r * .06)) if outline else Qt.NoPen
    p.setPen(pen)
    # body
    p.setBrush(QColor(hair).lighter(130) if not chibi else QColor(iris))
    bw = r * (1.3 if chibi else 2.1)
    p.drawEllipse(QPointF(cx, cy + r * (1.55 if chibi else 1.9)), bw, r * (.8 if chibi else 1.1))
    rr = r * (1.25 if chibi else 1.0)
    p.setBrush(QColor(hair)); p.drawEllipse(QPointF(cx, cy - rr * .05), rr * 1.08, rr * 1.12)   # back hair
    p.setBrush(QColor(skin)); p.drawEllipse(QPointF(cx, cy + rr * .08), rr * .92, rr * .96)      # face
    if gloss:
        g = QRadialGradient(cx - rr * .3, cy - rr * .3, rr); g.setColorAt(0, QColor(255, 255, 255, 140)); g.setColorAt(1, QColor(255, 255, 255, 0))
        p.setBrush(g); p.drawEllipse(QPointF(cx, cy + rr * .08), rr * .92, rr * .96)
    # fringe
    p.setBrush(QColor(hair)); path = QPainterPath()
    path.moveTo(cx - rr * .95, cy - rr * .05); path.quadTo(cx - rr * .3, cy - rr * 1.3, cx + rr * .95, cy - rr * .05)
    path.quadTo(cx + rr * .5, cy - rr * .55, cx + rr * .1, cy - rr * .25); path.quadTo(cx - rr * .3, cy - rr * .6, cx - rr * .95, cy - rr * .05)
    p.drawPath(path)
    # eyes
    ey = cy + rr * .12; es = rr * (.3 if chibi else .22)
    for s in (-1, 1):
        ex = cx + s * rr * .42
        p.setPen(Qt.NoPen); p.setBrush(Qt.white); p.drawEllipse(QPointF(ex, ey), es * .95, es * 1.2)
        p.setBrush(QColor(iris)); p.drawEllipse(QPointF(ex, ey + es * .1), es * .7, es * .95)
        p.setBrush(QColor("#111")); p.drawEllipse(QPointF(ex, ey + es * .1), es * .35, es * .5)
        p.setBrush(Qt.white); p.drawEllipse(QPointF(ex - es * .25, ey - es * .3), es * .22, es * .22)
        p.setBrush(QColor(255, 120, 140, 110)); p.drawEllipse(QPointF(ex + s * es * .2, ey + es * 1.5), es * .7, es * .4)
    p.setPen(QPen(QColor("#7A2E3A"), max(1.5, rr * .04), Qt.SolidLine, Qt.RoundCap))
    p.setBrush(Qt.NoBrush); p.drawArc(QRectF(cx - rr * .16, cy + rr * .45, rr * .32, rr * .2), 200 * 16, 140 * 16)


def _star(p, x, y, r, col):
    p.setPen(Qt.NoPen); p.setBrush(QColor(col)); path = QPainterPath()
    path.moveTo(x, y - r); path.quadTo(x, y, x + r, y); path.quadTo(x, y, x, y + r); path.quadTo(x, y, x - r, y); path.quadTo(x, y, x, y - r)
    p.drawPath(path)


def render_style_art(style_id, w=300, h=190) -> QPixmap:
    bg1, bg2, skin, hair, iris, outline, fx = PAL[style_id]
    scale = 1
    W, H = w, h
    if fx == "pixel":
        W, H = max(40, w // 6), max(25, h // 6)
    pm = QPixmap(W, H); pm.fill(Qt.transparent)
    p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing, fx != "pixel")
    rnd = random.Random(style_id)
    _bg(p, W, H, bg1, bg2)
    if fx == "rays":
        p.setPen(Qt.NoPen); p.setBrush(QColor(255, 255, 255, 40))
        for i in range(0, 360, 30):
            poly = QPolygonF([QPointF(W / 2, H * .6), QPointF(W / 2 + math.cos(math.radians(i)) * W, H * .6 + math.sin(math.radians(i)) * W),
                              QPointF(W / 2 + math.cos(math.radians(i + 15)) * W, H * .6 + math.sin(math.radians(i + 15)) * W)])
            p.drawPolygon(poly)
    if fx == "poly":
        for _ in range(26):
            pts = [QPointF(rnd.random() * W, rnd.random() * H) for _ in range(3)]
            p.setBrush(QColor(255, 255, 255, rnd.randint(15, 60))); p.setPen(Qt.NoPen); p.drawPolygon(QPolygonF(pts))
    if fx == "neon":
        p.setPen(QPen(QColor(236, 72, 153, 160), 1.5))
        for i in range(0, 12):
            y = H * .65 + (i ** 1.7) * 2.2
            p.drawLine(0, int(y), W, int(y))
        for i in range(-8, 9):
            p.drawLine(int(W / 2 + i * 6), int(H * .65), int(W / 2 + i * 40), H)
        p.setPen(QPen(QColor("#22D3EE"), 2)); p.drawRect(int(W * .05), int(H * .1), int(W * .12), int(H * .5))
        p.drawRect(int(W * .83), int(H * .2), int(W * .1), int(H * .4))
    if fx == "wash":
        for _ in range(9):
            p.setPen(Qt.NoPen); p.setBrush(QColor(rnd.choice(["#F9A8D4", "#A5B4FC", "#99F6E4", "#FDE68A"]) + "").lighter(110))
            c = p.brush().color(); c.setAlpha(90); p.setBrush(c)
            p.drawEllipse(QPointF(rnd.random() * W, rnd.random() * H), rnd.randint(20, 55), rnd.randint(15, 40))
    if fx == "halftone":
        p.setPen(Qt.NoPen); p.setBrush(QColor(0, 0, 0, 45))
        for yy in range(0, H, 9):
            for xx in range(0, W, 9):
                rr = 3.2 * (1 - xx / W) + .3
                p.drawEllipse(QPointF(xx + (yy // 9 % 2) * 4.5, yy), rr, rr)
    if fx == "speed":
        p.setPen(QPen(QColor(0, 0, 0, 110), 1.2))
        for i in range(60):
            a = rnd.random() * math.tau
            p.drawLine(QPointF(W / 2 + math.cos(a) * W * .45, H / 2 + math.sin(a) * H * .5), QPointF(W / 2 + math.cos(a) * W, H / 2 + math.sin(a) * W))
    if fx == "stars":
        for _ in range(16):
            _star(p, rnd.random() * W, rnd.random() * H * .7, rnd.randint(3, 8), "#FDE68A")
        p.setBrush(QColor("#FDE68A")); p.setPen(Qt.NoPen); p.drawEllipse(QPointF(W * .85, H * .22), 16, 16)
    cx, cy = W * .5, H * .46
    r = min(W, H) * (.25 if fx != "chibi" else .21)
    _char(p, cx, cy, r, skin, hair, iris, outline, chibi=(fx == "chibi"), gloss=(fx in ("gloss", "clay")))
    if fx == "sparkle":
        for _ in range(9):
            _star(p, rnd.random() * W, rnd.random() * H, rnd.randint(4, 10), "#FFFFFF")
    if fx == "hatch":
        p.setPen(QPen(QColor(60, 60, 70, 110), 1))
        for i in range(-H, W, 7):
            p.drawLine(i, 0, i + H, H)
    if fx == "cine":
        p.fillRect(0, 0, W, int(H * .12), Qt.black); p.fillRect(0, int(H * .88), W, H, Qt.black)
        g = QRadialGradient(W * .8, H * .3, W * .35); g.setColorAt(0, QColor(255, 220, 160, 170)); g.setColorAt(1, QColor(255, 220, 160, 0))
        p.fillRect(0, 0, W, H, g)
    if fx == "clay":
        p.setPen(Qt.NoPen); p.setBrush(QColor(255, 255, 255, 60)); p.drawEllipse(QPointF(W * .2, H * .2), 18, 10)
    if fx == "halftone":
        f = QFont("Impact", int(H * .14)); p.setFont(f); p.setPen(QColor("#111")); p.drawText(int(W * .04), int(H * .2), "POW!")
    p.end()
    if fx == "pixel":
        pm = pm.scaled(w, h, Qt.IgnoreAspectRatio, Qt.FastTransformation)
    return pm


def render_hero(w, h) -> QPixmap:
    pm = QPixmap(w, h); pm.fill(Qt.transparent)
    p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
    rnd = random.Random(7)
    for _ in range(14):
        p.setPen(Qt.NoPen); col = QColor(rnd.choice(["#22D3EE", "#EC4899", "#FFFFFF", "#3B82F6"])); col.setAlpha(50)
        p.setBrush(col); p.drawEllipse(QPointF(rnd.random() * w, rnd.random() * h), rnd.randint(8, 40), rnd.randint(8, 40))
    sc = h / 260
    for (dx, dy, s, key) in ((.2, .62, .72, "cartoon3d"), (.78, .62, .72, "chibi"), (.5, .5, 1.0, "anime")):
        _, _, skin, hair, iris, outline, fx = PAL[key]
        _char(p, w * dx, h * dy * .9, 56 * sc * s, skin, hair, iris, outline, chibi=(key == "chibi"), gloss=(key == "cartoon3d"))
    for _ in range(14):
        _star(p, rnd.random() * w, rnd.random() * h, rnd.randint(4, 11), "#FFFFFF")
    p.end()
    return pm
