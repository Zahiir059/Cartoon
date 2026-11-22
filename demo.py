import threading, time
from .base import Provider, AIParams
from .. import media


class DemoProvider(Provider):
    id = "demo"
    name = "Demo Mode (no AI)"
    is_demo = True
    controls = frozenset()
    quality_options = ((512, "Demo"),)

    def run(self, video_path, params: AIParams, dest, progress, cancel: threading.Event):
        info = media.probe(video_path)
        for i, msg in enumerate(["Demo: preparing sample…", "Demo: rendering placeholder…"]):
            progress(10 + i * 20, msg)
            time.sleep(0.6)
        media.make_demo_clip(dest, info["width"] // 2 * 2, info["height"] // 2 * 2, min(info["duration"], 10),
                             lambda p: progress(30 + int(p * 0.65), "Demo: rendering placeholder…"))
        progress(100, "Demo sample ready (NOT AI generated)")
        return dest
