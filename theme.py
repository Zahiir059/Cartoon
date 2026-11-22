PURPLE, VIOLET, BLUE, CYAN, PINK = "#5425D6", "#8B5CF6", "#3B82F6", "#22D3EE", "#EC4899"
DARK = dict(bg="#10111B", card="#1C1D2B", card2="#252638", text="#FFFFFF", sub="#A5A8C0",
            border="#2D2F47", input="#151624", hover="#2A2B40")
LIGHT = dict(bg="#F2F1FB", card="#FFFFFF", card2="#ECEAF8", text="#1B1B2F", sub="#5F6280",
             border="#DCD8F0", input="#F7F6FD", hover="#E6E3F6")
_mode = "dark"


def set_mode(m):
    global _mode
    _mode = m


def mode():
    return _mode


def c(key):
    return (DARK if _mode == "dark" else LIGHT)[key]


def qss():
    t = DARK if _mode == "dark" else LIGHT
    return f"""
* {{ font-family: 'Segoe UI','Inter','Helvetica Neue',Arial,sans-serif; font-size: 13px; color: {t['text']}; }}
QWidget#root, QStackedWidget, QScrollArea, QScrollArea > QWidget > QWidget {{ background: transparent; }}
QToolTip {{ background: {t['card2']}; color: {t['text']}; border: 1px solid {PINK}; padding: 6px; border-radius: 6px; }}
QLabel {{ background: transparent; }}
QLabel#h1 {{ font-size: 26px; font-weight: 800; }}
QLabel#h2 {{ font-size: 18px; font-weight: 700; }}
QLabel#sub {{ color: {t['sub']}; }}
QLabel#chip {{ background: {t['card2']}; border-radius: 10px; padding: 3px 10px; font-size: 11px; font-weight: 600; }}
QLabel#banner {{ background: rgba(236,72,153,0.16); border: 1px solid {PINK}; border-radius: 12px; padding: 10px 14px; }}
QLabel#banner_ok {{ background: rgba(34,211,238,0.12); border: 1px solid {CYAN}; border-radius: 12px; padding: 10px 14px; }}
QFrame#card {{ background: {t['card']}; border: 1px solid {t['border']}; border-radius: 18px; }}
QFrame#card2 {{ background: {t['card2']}; border-radius: 14px; }}
QFrame#header {{ background: {t['card']}; border-bottom: 1px solid {t['border']}; }}
QFrame#sidebar {{ background: {t['card']}; border-right: 1px solid {t['border']}; }}
QFrame#drop {{ background: {t['input']}; border: 2px dashed {VIOLET}; border-radius: 18px; }}
QFrame#drop:hover {{ border-color: {PINK}; background: {t['card2']}; }}
QPushButton {{ background: {t['card2']}; border: 1px solid {t['border']}; border-radius: 10px; padding: 8px 16px; font-weight: 600; }}
QPushButton:hover {{ background: {t['hover']}; border-color: {VIOLET}; }}
QPushButton:checked {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {PURPLE}, stop:1 {VIOLET}); border-color: {VIOLET}; color: white; }}
QPushButton:disabled {{ color: {t['sub']}; background: {t['card']}; }}
QPushButton#nav {{ text-align: left; padding: 12px 16px; border: none; border-left: 4px solid transparent;
    border-radius: 0 12px 12px 0; background: transparent; font-size: 14px; color: {t['sub']}; margin-right: 10px; }}
QPushButton#nav:hover {{ background: {t['hover']}; color: {t['text']}; }}
QPushButton#nav:checked {{ color: #FFFFFF; border-left: 4px solid {PINK};
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {PURPLE}, stop:1 {VIOLET}); }}
QPushButton#icon {{ background: transparent; border: none; padding: 6px; border-radius: 12px; }}
QPushButton#icon:hover {{ background: {t['hover']}; }}
QPushButton#small {{ padding: 5px 10px; border-radius: 8px; font-size: 12px; }}
QPushButton#danger:hover {{ background: #B91C1C; border-color: #B91C1C; color: white; }}
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTableWidget {{
    background: {t['input']}; border: 1px solid {t['border']}; border-radius: 10px; padding: 7px 10px;
    selection-background-color: {VIOLET}; }}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{ border: 1px solid {VIOLET}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{ background: {t['card']}; border: 1px solid {t['border']}; selection-background-color: {VIOLET}; outline: none; }}
QHeaderView::section {{ background: {t['card2']}; border: none; padding: 6px; font-weight: 600; }}
QTableWidget {{ gridline-color: {t['border']}; }}
QSlider::groove:horizontal {{ height: 6px; background: {t['card2']}; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {PINK}, stop:1 {VIOLET}); border-radius: 3px; }}
QSlider::handle:horizontal {{ background: white; width: 16px; height: 16px; margin: -5px 0; border-radius: 8px; border: 2px solid {VIOLET}; }}
QProgressBar {{ background: {t['card2']}; border-radius: 7px; height: 14px; text-align: center; font-size: 10px; font-weight: 700; }}
QProgressBar::chunk {{ border-radius: 7px; background: qlineargradient(x1:0,y1:0,x2:1,y2:0, stop:0 {PINK}, stop:0.5 {VIOLET}, stop:1 {CYAN}); }}
QTabWidget::pane {{ border: none; }}
QTabBar::tab {{ background: transparent; padding: 8px 14px; border-radius: 10px; color: {t['sub']}; font-weight: 600; margin-right: 2px; }}
QTabBar::tab:selected {{ background: {t['card2']}; color: {t['text']}; }}
QTabBar::tab:hover {{ color: {t['text']}; }}
QCheckBox {{ spacing: 8px; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 5px; border: 2px solid {VIOLET}; background: transparent; }}
QCheckBox::indicator:checked {{ background: {VIOLET}; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {t['border']}; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {VIOLET}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar:horizontal {{ height: 10px; background: transparent; }}
QScrollBar::handle:horizontal {{ background: {t['border']}; border-radius: 5px; }}
QMenu {{ background: {t['card']}; border: 1px solid {t['border']}; border-radius: 10px; padding: 6px; }}
QMenu::item {{ padding: 8px 18px; border-radius: 6px; }}
QMenu::item:selected {{ background: {VIOLET}; }}
QDialog, QMessageBox, QInputDialog {{ background: {t['bg']}; }}
"""
