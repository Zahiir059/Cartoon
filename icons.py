"""Vector icons drawn with QPainter on a 24x24 grid (no image assets needed)."""
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPixmap, QPainter, QPen, QColor, QIcon, QPainterPath, QPolygonF


def _star(p, cx, cy, r):
    path = QPainterPath()
    pts = [(cx, cy - r), (cx + r * .28, cy - r * .28), (cx + r, cy), (cx + r * .28, cy + r * .28),
           (cx, cy + r), (cx - r * .28, cy + r * .28), (cx - r, cy), (cx - r * .28, cy - r * .28)]
    path.moveTo(*pts[0])
    for x, y in pts[1:]:
        path.lineTo(x, y)
    path.closeSubpath()
    p.drawPath(path)


def draw(name, p: QPainter, color, theme_bg="#808080"):
    pen = QPen(QColor(color), 1.8, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen); p.setBrush(Qt.NoBrush)
    L = p.drawLine
    if name == "home":
        p.drawPolyline(QPolygonF([QPointF(3, 11), QPointF(12, 3), QPointF(21, 11)]))
        p.drawPolyline(QPolygonF([QPointF(5, 10), QPointF(5, 21), QPointF(19, 21), QPointF(19, 10)]))
        p.drawRect(QRectF(10, 14, 4, 7))
    elif name == "studio":
        p.drawRoundedRect(QRectF(3, 5, 18, 14), 3, 3)
        p.setBrush(QColor(color)); p.drawPolygon(QPolygonF([QPointF(10, 9), QPointF(10, 15), QPointF(15, 12)]))
    elif name == "styles":
        p.drawEllipse(QRectF(3, 3, 18, 18))
        p.setBrush(QColor(color))
        for x, y in ((8, 9), (12, 7), (16, 10), (9, 15)):
            p.drawEllipse(QPointF(x, y), 1.4, 1.4)
    elif name == "editor":
        p.drawEllipse(QPointF(6, 7), 2.6, 2.6); p.drawEllipse(QPointF(6, 17), 2.6, 2.6)
        L(8, 8.5, 20, 18); L(8, 15.5, 20, 6)
    elif name == "folder":
        p.drawPolyline(QPolygonF([QPointF(3, 7), QPointF(3, 19), QPointF(21, 19), QPointF(21, 9), QPointF(11, 9), QPointF(9, 6), QPointF(3, 6), QPointF(3, 7)]))
    elif name == "settings":
        for y, x in ((6, 8), (12, 16), (18, 10)):
            L(3, y, 21, y); p.setBrush(QColor(color)); p.drawEllipse(QPointF(x, y), 2.4, 2.4); p.setBrush(Qt.NoBrush)
    elif name == "info":
        p.drawEllipse(QRectF(3, 3, 18, 18)); L(12, 11, 12, 17); p.drawPoint(QPointF(12, 7.5))
    elif name == "user":
        p.drawEllipse(QPointF(12, 8), 4, 4)
        path = QPainterPath(); path.moveTo(4, 21); path.cubicTo(4, 13, 20, 13, 20, 21); p.drawPath(path)
    elif name == "upload":
        L(12, 16, 12, 4); L(12, 4, 7, 9); L(12, 4, 17, 9); L(4, 20, 20, 20)
    elif name == "download":
        L(12, 4, 12, 16); L(12, 16, 7, 11); L(12, 16, 17, 11); L(4, 20, 20, 20)
    elif name == "play":
        p.setBrush(QColor(color)); p.drawPolygon(QPolygonF([QPointF(7, 4), QPointF(7, 20), QPointF(20, 12)]))
    elif name == "pause":
        p.setBrush(QColor(color)); p.drawRect(QRectF(6, 4, 4, 16)); p.drawRect(QRectF(14, 4, 4, 16))
    elif name == "heart":
        path = QPainterPath(); path.moveTo(12, 20); path.cubicTo(-4, 9, 6, 0, 12, 7); path.cubicTo(18, 0, 28, 9, 12, 20); p.drawPath(path)
    elif name == "heart_fill":
        path = QPainterPath(); path.moveTo(12, 20); path.cubicTo(-4, 9, 6, 0, 12, 7); path.cubicTo(18, 0, 28, 9, 12, 20)
        p.setBrush(QColor(color)); p.drawPath(path)
    elif name == "trash":
        L(4, 7, 20, 7); p.drawPolyline(QPolygonF([QPointF(6, 7), QPointF(7, 21), QPointF(17, 21), QPointF(18, 7)]))
        L(9, 4, 15, 4); L(10, 11, 10, 17); L(14, 11, 14, 17)
    elif name == "edit":
        L(4, 20, 8, 19); L(8, 19, 19, 8); L(4, 20, 5, 16); L(5, 16, 16, 5); L(16, 5, 19, 8)
    elif name == "sparkle":
        p.setBrush(QColor(color)); _star(p, 11, 12, 8); _star(p, 19, 5, 3)
    elif name == "fullscreen":
        for a in ((4, 9, 4, 4, 9, 4), (15, 4, 20, 4, 20, 9), (20, 15, 20, 20, 15, 20), (9, 20, 4, 20, 4, 15)):
            p.drawPolyline(QPolygonF([QPointF(a[0], a[1]), QPointF(a[2], a[3]), QPointF(a[4], a[5])]))
    elif name == "sun":
        import math
        p.drawEllipse(QPointF(12, 12), 4, 4)
        for i in range(8):
            a = i * math.pi / 4
            L(12 + 7 * math.cos(a), 12 + 7 * math.sin(a), 12 + 9.5 * math.cos(a), 12 + 9.5 * math.sin(a))
    elif name == "moon":
        path = QPainterPath(); path.moveTo(19, 14); path.cubicTo(10, 20, 3, 10, 10, 4); path.cubicTo(8, 12, 13, 17, 19, 14); p.drawPath(path)
    elif name == "refresh":
        p.drawArc(QRectF(4, 4, 16, 16), 40 * 16, 270 * 16); L(19, 3, 19, 8); L(19, 8, 14, 8)
    elif name == "volume":
        p.drawPolygon(QPolygonF([QPointF(4, 9), QPointF(8, 9), QPointF(13, 5), QPointF(13, 19), QPointF(8, 15), QPointF(4, 15)]))
        p.drawArc(QRectF(11, 8, 8, 8), -60 * 16, 120 * 16)
    elif name == "check":
        p.drawPolyline(QPolygonF([QPointF(5, 13), QPointF(10, 18), QPointF(19, 6)]))
    elif name == "plus":
        L(12, 5, 12, 19); L(5, 12, 19, 12)
    elif name == "compare":
        p.drawRect(QRectF(3, 5, 8, 14)); p.drawRect(QRectF(13, 5, 8, 14))
    elif name == "stop":
        p.setBrush(QColor(color)); p.drawRoundedRect(QRectF(6, 6, 12, 12), 2, 2)


def pix(name, color="#FFFFFF", size=22, dpr=2.0):
    pm = QPixmap(int(size * dpr), int(size * dpr)); pm.setDevicePixelRatio(dpr); pm.fill(Qt.transparent)
    p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing)
    p.scale(size / 24, size / 24); draw(name, p, color); p.end()
    return pm


def icon(name, color="#FFFFFF", size=22):
    return QIcon(pix(name, color, size))
