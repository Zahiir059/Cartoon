import threading
from dataclasses import dataclass


class ProviderError(Exception):
    def __init__(self, msg, retryable=False):
        super().__init__(msg)
        self.retryable = retryable


@dataclass
class AIParams:
    style_id: str
    prompt: str            # full prompt (style + user)
    negative: str
    style_intensity: int   # 0-100
    detail: int            # 0-100
    out_side: int          # longest output side in px (512/768/1024)
    width: int             # prepared input width
    height: int


class Provider:
    id = "base"
    name = "Base"
    is_demo = False
    #: ids of UI controls this provider/model genuinely supports
    controls: frozenset = frozenset()
    #: longest-side output sizes (px) the provider can produce
    quality_options = ()

    def configured(self) -> bool:
        return True

    def run(self, video_path: str, params: AIParams, dest: str, progress, cancel: threading.Event) -> str:
        raise NotImplementedError
