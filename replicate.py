"""Replicate (https://replicate.com) provider.

Default model: philz1337x/video-style-transfer (AnimateDiff-based video-to-video).
The model's real input schema is downloaded at run time and only inputs that the model
actually declares are sent, so swapping the model slug in Settings cannot send bogus fields.
"""
import os, threading, time
import requests
from .base import Provider, ProviderError, AIParams
from .. import secrets_store, settings as _s

API = "https://api.replicate.com/v1"


class ReplicateProvider(Provider):
    id = "replicate"
    name = "Replicate (cloud AI)"
    # Controls that map to genuine inputs of the default model.
    controls = frozenset({"prompt", "negative", "style_intensity", "detail", "quality"})
    quality_options = ((512, "Fast – 512 px"), (768, "Balanced – 768 px"), (1024, "High – 1024 px"))

    def __init__(self, settings: _s.Settings):
        self.settings = settings

    def configured(self):
        return bool(secrets_store.get_token("replicate"))

    # ---- HTTP helper with retry on transient failures
    def _req(self, s, method, url, tries=3, **kw):
        last = None
        for i in range(tries):
            try:
                r = s.request(method, url, timeout=(15, 120), **kw)
            except (requests.ConnectionError, requests.Timeout) as e:
                last = ProviderError("Network error – check your internet connection.", True)
                time.sleep(1.5 * (i + 1))
                continue
            if r.status_code in (429, 500, 502, 503, 504):
                last = ProviderError(f"AI service is busy ({r.status_code}). Please retry.", True)
                time.sleep(2 * (i + 1))
                continue
            if r.status_code == 401:
                raise ProviderError("The API key was rejected (401). Check it in Settings.")
            if r.status_code == 402:
                raise ProviderError("The AI service reports a billing problem (402). Add credit to your account.")
            if r.status_code == 404:
                raise ProviderError("Model not found (404). Check the model name in Settings.")
            if r.status_code >= 400:
                detail = ""
                try:
                    detail = r.json().get("detail", "")
                except Exception:
                    pass
                raise ProviderError(f"AI service error {r.status_code}: {detail or r.text[:200]}")
            return r
        raise last or ProviderError("Unknown network failure.", True)

    def _session(self):
        tok = secrets_store.get_token("replicate")
        if not tok:
            raise ProviderError("No API key configured.")
        s = requests.Session()
        s.headers["Authorization"] = f"Bearer {tok}"
        return s

    def test_connection(self):
        s = self._session()
        self._req(s, "GET", f"{API}/account", tries=1)
        return True

    def _resolve(self, s):
        slug = self.settings.get("model").strip()
        if ":" in slug:
            slug, ver = slug.split(":", 1)
            data = self._req(s, "GET", f"{API}/models/{slug}/versions/{ver}").json()
            vid = data["id"]
        else:
            data = self._req(s, "GET", f"{API}/models/{slug}").json()
            data = data.get("latest_version") or {}
            vid = data.get("id")
            if not vid:
                raise ProviderError("This model has no published version.")
        try:
            props = set(data["openapi_schema"]["components"]["schemas"]["Input"]["properties"])
        except Exception:
            props = set()
        return vid, props

    def run(self, video_path, p: AIParams, dest, progress, cancel: threading.Event):
        s = self._session()
        progress(4, "Uploading video…")
        with open(video_path, "rb") as f:
            up = self._req(s, "POST", f"{API}/files", files={"content": (os.path.basename(video_path), f, "video/mp4")}).json()
        file_url = up["urls"]["get"]
        if cancel.is_set():
            raise ProviderError("Cancelled.")
        progress(12, "Contacting AI model…")
        version, props = self._resolve(s)

        # map app controls -> model inputs
        scale = p.out_side / max(p.width, p.height)
        ow, oh = (max(64, int(p.width * scale) // 8 * 8), max(64, int(p.height * scale) // 8 * 8))
        inp = {
            "video": file_url,
            "prompt": p.prompt,
            "negative_prompt": p.negative,
            "cfg_scale": round(1.5 + p.style_intensity / 100 * 5.5, 2),      # prompt adherence
            "num_inference_steps": int(8 + p.detail / 100 * 17),             # 8..25
            "input_width": p.width // 8 * 8, "input_height": p.height // 8 * 8,
            "output_width": ow, "output_height": oh,
        }
        if props:
            inp = {k: v for k, v in inp.items() if k in props}
        pred = self._req(s, "POST", f"{API}/predictions", json={"version": version, "input": inp}).json()
        get_url, cancel_url = pred["urls"]["get"], pred["urls"].get("cancel")
        progress(18, "Queued on AI service…")

        t0 = time.time()
        while True:
            if cancel.is_set():
                if cancel_url:
                    try:
                        s.post(cancel_url, timeout=15)
                    except Exception:
                        pass
                raise ProviderError("Cancelled.")
            if time.time() - t0 > 25 * 60:
                raise ProviderError("The AI job timed out after 25 minutes.", True)
            time.sleep(3)
            pr = self._req(s, "GET", get_url).json()
            st = pr.get("status")
            if st == "succeeded":
                break
            if st in ("failed", "canceled"):
                raise ProviderError(f"AI processing {st}: {pr.get('error') or 'no details provided'}", st == "failed")
            logs = (pr.get("logs") or "").strip().splitlines()
            pct = 20 + min(70, int((time.time() - t0) / 3))   # time-based; model gives no % in a stable field
            progress(pct, ("Processing: " + logs[-1][:70]) if logs else ("Starting model…" if st == "starting" else "Processing…"))

        out = pr.get("output")
        url = out[0] if isinstance(out, list) and out else out
        if not isinstance(url, str):
            raise ProviderError("The AI service returned no video.")
        progress(92, "Downloading result…")
        try:
            with requests.get(url, stream=True, timeout=(15, 120)) as r:
                r.raise_for_status()
                with open(dest, "wb") as f:
                    for chunk in r.iter_content(1 << 16):
                        f.write(chunk)
        except requests.RequestException as e:
            raise ProviderError(f"Could not download the generated video: {e}", True)
        progress(100, "Done")
        return dest
