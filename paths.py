"""Filesystem locations. Everything lives under %APPDATA%/CartoonAI (or ~/.local/share on Linux)."""
import os, shutil, sys
from pathlib import Path


def data_dir() -> Path:
    base = os.environ.get("APPDATA") or str(Path.home() / ".local" / "share")
    p = Path(base) / "CartoonAI"
    p.mkdir(parents=True, exist_ok=True)
    return p


def library_dir() -> Path:
    p = data_dir() / "library"
    p.mkdir(exist_ok=True)
    return p


def temp_dir() -> Path:
    p = data_dir() / "tmp"
    p.mkdir(exist_ok=True)
    return p


def thumbs_dir() -> Path:
    p = data_dir() / "thumbs"
    p.mkdir(exist_ok=True)
    return p


def clean_temp():
    """Remove every temporary file (called at startup and exit)."""
    t = data_dir() / "tmp"
    if t.exists():
        shutil.rmtree(t, ignore_errors=True)
    t.mkdir(exist_ok=True)


def ffmpeg_exe() -> str | None:
    try:
        import imageio_ffmpeg
        exe = imageio_ffmpeg.get_ffmpeg_exe()
        if exe and os.path.exists(exe):
            return exe
    except Exception:
        pass
    return shutil.which("ffmpeg")
