import os, sys

if sys.platform == "win32":   # crisp text on high-DPI screens, own taskbar identity
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("CartoonAI.Studio.1")
    except Exception:
        pass


def main():
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    app = QApplication(sys.argv)
    app.setApplicationName("Cartoon AI")
    from cartoon_ai import paths
    paths.clean_temp()
    from cartoon_ai.main_window import MainWindow
    w = MainWindow()
    w.show()
    if os.environ.get("CARTOON_SELFTEST"):      # used by the build script to prove the packaged app starts
        from PySide6.QtCore import QTimer
        def report():
            for k in ("home", "studio", "styles", "editor", "creations", "settings", "about"):
                w.go(k); app.processEvents()
            ff = paths.ffmpeg_exe()
            print("SELFTEST OK | ffmpeg:", bool(ff), "| provider:", w.ctx.provider().name, flush=True)
            app.quit()
        QTimer.singleShot(1200, report)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
