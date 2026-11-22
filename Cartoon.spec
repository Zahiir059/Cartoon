# PyInstaller spec -> a single windowed Cartoon.exe (one-file). Build with:  pyinstaller Cartoon.spec
import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas, binaries, hidden = [], [], []
for pkg in ("imageio_ffmpeg",):                      # bundles the FFmpeg binary
    d, b, h = collect_all(pkg); datas += d; binaries += b; hidden += h
hidden += collect_submodules("keyring.backends")     # Windows Credential Manager backend
hidden += ["win32ctypes.pywin32.pywintypes", "win32ctypes.pywin32.win32cred"] if sys.platform == "win32" else []

excludes = ["tkinter", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtQuick", "PySide6.QtQml",
            "PySide6.Qt3DCore", "PySide6.QtDesigner", "PySide6.QtCharts", "PySide6.QtSql", "PySide6.QtTest",
            "PySide6.QtBluetooth", "PySide6.QtPdf", "PySide6.QtSensors", "PySide6.QtSerialPort", "numpy", "matplotlib", "PIL"]

a = Analysis(["main.py"], pathex=["."], binaries=binaries, datas=datas, hiddenimports=hidden, excludes=excludes, noarchive=False)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name="Cartoon", debug=False, strip=False, upx=False,
          console=False, icon="assets/icon.ico" if sys.platform == "win32" else None,
          runtime_tmpdir=None, disable_windowed_traceback=False)
