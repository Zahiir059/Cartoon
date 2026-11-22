"""All FFmpeg work: probing, preparing clips for the AI, editing, exporting."""
import os, re, subprocess, sys, threading
from .paths import ffmpeg_exe

NOWIN = 0x08000000 if os.name == "nt" else 0
VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".wmv", ".flv", ".mpg", ".mpeg", ".3gp"}
AUDIO_EXTS = {".mp3", ".wav", ".aac", ".m4a", ".ogg", ".flac"}
MAX_INPUT_BYTES = 500 * 1024 * 1024
MAX_AI_SECONDS = 10.0


class MediaError(Exception):
    pass


def _ff():
    ff = ffmpeg_exe()
    if not ff:
        raise MediaError("FFmpeg was not found. Reinstall the application.")
    return ff


def probe(path: str) -> dict:
    if not os.path.isfile(path):
        raise MediaError("File not found.")
    if os.path.splitext(path)[1].lower() not in VIDEO_EXTS:
        raise MediaError("Unsupported format. Supported: " + ", ".join(sorted(e[1:].upper() for e in VIDEO_EXTS)))
    if os.path.getsize(path) > MAX_INPUT_BYTES:
        raise MediaError("File is larger than 500 MB.")
    p = subprocess.run([_ff(), "-hide_banner", "-i", path], capture_output=True, text=True,
                       errors="replace", creationflags=NOWIN)
    e = p.stderr
    m = re.search(r"Duration:\s*(\d+):(\d+):([\d.]+)", e)
    v = re.search(r"Video:.*?\b(\d{2,5})x(\d{2,5})\b", e)
    if not m or not v:
        raise MediaError("This file is not a valid, playable video.")
    dur = int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3])
    w, h = int(v[1]), int(v[2])
    rot = re.search(r"rotation of (-?[\d.]+) degrees", e) or re.search(r"rotate\s*:\s*(-?\d+)", e)
    if rot and abs(int(float(rot[1]))) % 180 == 90:
        w, h = h, w
    fps = re.search(r"([\d.]+) fps", e)
    if dur <= 0:
        raise MediaError("Video has no duration.")
    return dict(duration=dur, width=w, height=h, fps=float(fps[1]) if fps else 0.0,
                has_audio="Audio:" in e, size=os.path.getsize(path))


def run_ffmpeg(args: list[str], total: float = 0, progress=None, cancel: threading.Event | None = None):
    cmd = [_ff(), "-y", "-hide_banner", "-loglevel", "error", "-nostats", "-progress", "pipe:1"] + args
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            errors="replace", creationflags=NOWIN)
    err_buf = []
    t = threading.Thread(target=lambda: err_buf.append(proc.stderr.read()), daemon=True)
    t.start()
    for line in proc.stdout:
        if cancel is not None and cancel.is_set():
            proc.kill()
            raise MediaError("Cancelled.")
        if line.startswith("out_time_us=") and total > 0 and progress:
            try:
                progress(min(99, int(int(line.split("=")[1]) / 1e6 / total * 100)))
            except ValueError:
                pass
    proc.wait()
    t.join(2)
    if proc.returncode != 0:
        tail = (err_buf[0] if err_buf else "").strip().splitlines()[-4:]
        raise MediaError("FFmpeg failed: " + " | ".join(tail))
    if progress:
        progress(100)


def thumbnail(src: str, dst: str, t: float = 0.3):
    run_ffmpeg(["-ss", f"{t:.2f}", "-i", src, "-frames:v", "1", "-vf", "scale=480:-2", dst])


def _geom_filters(rotate=0, aspect="Original", flip_h=False, flip_v=False):
    f = []
    if aspect and aspect != "Original":
        a, b = aspect.split(":")
        A = int(a) / int(b)
        f.append(f"crop='trunc(min(iw,ih*{A})/2)*2':'trunc(min(ih,iw/{A})/2)*2'")
    f += {0: [], 90: ["transpose=1"], 180: ["hflip", "vflip"], 270: ["transpose=2"]}[rotate % 360]
    if flip_h:
        f.append("hflip")
    if flip_v:
        f.append("vflip")
    return f


def prepare_clip(src, dst, start, dur, rotate=0, aspect="Original", max_side=None, audio=True, progress=None):
    """Cut a segment (with optional crop/rotate); optionally downscale; optionally strip audio."""
    f = _geom_filters(rotate, aspect)
    if max_side:
        f.append(f"scale='if(gt(iw,ih),min({max_side},iw),-2)':'if(gt(iw,ih),-2,min({max_side},ih))'")
    f.append("scale=trunc(iw/2)*2:trunc(ih/2)*2")
    f.append("format=yuv420p")
    args = ["-ss", f"{start:.3f}", "-t", f"{dur:.3f}", "-i", src, "-vf", ",".join(f),
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20"]
    args += ["-c:a", "aac", "-b:a", "160k"] if audio else ["-an"]
    run_ffmpeg(args + ["-movflags", "+faststart", dst], dur, progress)


def mux_audio(video, audio_src, dst):
    run_ffmpeg(["-i", video, "-i", audio_src, "-map", "0:v:0", "-map", "1:a:0?", "-c:v", "copy",
                "-c:a", "aac", "-shortest", "-movflags", "+faststart", dst])


def split_at(src, t, dst1, dst2, total):
    run_ffmpeg(["-i", src, "-t", f"{t:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", dst1])
    run_ffmpeg(["-ss", f"{t:.3f}", "-i", src, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", dst2])


def make_demo_clip(dst, w, h, dur, progress=None):
    """Synthetic placeholder clip for Demo Mode. Clearly labelled; it is NOT derived from the user's video."""
    font = font_file()
    ff = f":fontfile='{_esc_path(font)}'" if font else ""
    vf = (f"drawbox=x=0:y=ih/2-60:w=iw:h=120:color=black@0.6:t=fill,"
          f"drawtext=text='DEMO SAMPLE':fontsize=h/12:fontcolor=white:x=(w-tw)/2:y=h/2-h/14{ff},"
          f"drawtext=text='Not AI generated':fontsize=h/20:fontcolor=#EC4899:x=(w-tw)/2:y=h/2+h/40{ff}")
    run_ffmpeg(["-f", "lavfi", "-i", f"testsrc2=size={w}x{h}:rate=24:duration={dur:.2f}", "-vf", vf,
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", dst], dur, progress)


def font_file():
    for f in (r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/System/Library/Fonts/Supplemental/Arial.ttf"):
        if os.path.exists(f):
            return f
    return None


def _esc_path(p):
    return p.replace("\\", "/").replace(":", "\\:")


def _esc_text(t):
    return (t.replace("\\", "\\\\").replace("'", "\u2019").replace(":", "\\:").replace("%", "\\%")
            .replace(",", "\\,").replace("\n", " "))


def _atempo(s):
    ch = []
    while s > 2.0:
        ch.append("atempo=2.0"); s /= 2
    while s < 0.5:
        ch.append("atempo=0.5"); s /= 0.5
    ch.append(f"atempo={s:.4f}")
    return ",".join(ch)


def apply_edit(src, dst, info, spec, progress=None):
    """Render the Video Editor timeline. `spec` keys are documented in pages/editor.py."""
    start = max(0.0, spec.get("start", 0.0))
    end = min(info["duration"], spec.get("end") or info["duration"])
    span = end - start
    if span <= 0.05:
        raise MediaError("Trim range is empty.")
    speed = spec.get("speed", 1.0)
    out_dur = span / speed

    v = _geom_filters(spec.get("rotate", 0), spec.get("aspect_crop", "Original"), spec.get("flip_h"), spec.get("flip_v"))
    c = spec.get("crop")
    if c:
        v.insert(0, f"crop='trunc(iw*{c[0]}/2)*2':'trunc(ih*{c[1]}/2)*2':'iw*{c[2]}':'ih*{c[3]}'")
    b, ct, sa = spec.get("brightness", 0.0), spec.get("contrast", 1.0), spec.get("saturation", 1.0)
    if (b, ct, sa) != (0.0, 1.0, 1.0):
        v.append(f"eq=brightness={b:.3f}:contrast={ct:.3f}:saturation={sa:.3f}")
    if abs(speed - 1) > 1e-3:
        v.append(f"setpts=PTS/{speed:.4f}")
    ea = spec.get("export_aspect", "Original")
    if ea != "Original":
        a, bb = ea.split(":")
        A = int(a) / int(bb)
        v.append(f"crop='trunc(min(iw,ih*{A})/2)*2':'trunc(min(ih,iw/{A})/2)*2'")
    eh = spec.get("export_height")
    if eh:
        v.append(f"scale='if(lt(iw,ih),{eh},-2)':'if(lt(iw,ih),-2,{eh})'")
    v.append("scale=trunc(iw/2)*2:trunc(ih/2)*2")

    font = font_file()
    items = [(t["text"], t["start"], t["end"], t.get("size", 36), t.get("pos", "Bottom"), False) for t in spec.get("texts", [])]
    items += [(s["text"], s["start"], s["end"], 30, "Bottom", True) for s in spec.get("subs", [])]
    if items and not font:
        raise MediaError("No system font found for text overlays.")
    for text, s, e, size, pos, box in items:
        y = {"Top": "h*0.06", "Center": "(h-th)/2", "Bottom": "h-th-h*0.07"}.get(pos, "h-th-h*0.07")
        v.append(f"drawtext=fontfile='{_esc_path(font)}':text='{_esc_text(text)}':fontsize=h*{size}/720:"
                 f"fontcolor=white:borderw=2:bordercolor=black@0.9:x=(w-tw)/2:y={y}"
                 + (":box=1:boxcolor=black@0.45:boxborderw=8" if box else "")
                 + f":enable='between(t,{s:.2f},{e:.2f})'")
    v.append("format=yuv420p")

    inputs = ["-ss", f"{start:.3f}", "-t", f"{span:.3f}", "-i", src,
              "-f", "lavfi", "-t", f"{out_dur:.3f}", "-i", "anullsrc=r=44100:cl=stereo"]
    fc = [f"[0:v]{','.join(v)}[vout]", "[1:a]anull[sil]"]
    labels = ["[sil]"]
    vol = spec.get("volume", 1.0)
    if info.get("has_audio") and not spec.get("mute"):
        fc.append(f"[0:a]{_atempo(speed)},volume={vol:.3f}[base]")
        labels.append("[base]")
    idx = 2
    for key in ("music", "voiceover", "sfx"):
        m = spec.get(key)
        if m and m.get("path"):
            inputs += ["-i", m["path"]]
            st, ln = m.get("trim_start", 0.0), m.get("trim_len") or out_dur
            delay = int(m.get("at", 0.0) * 1000)
            fc.append(f"[{idx}:a]atrim=start={st:.2f}:duration={ln:.2f},asetpts=PTS-STARTPTS,"
                      f"volume={m.get('volume', 1.0):.3f},adelay={delay}|{delay}[x{idx}]")
            labels.append(f"[x{idx}]")
            idx += 1
    args = inputs + ["-filter_complex", ";".join(fc), "-map", "[vout]"]
    if len(labels) > 1:
        fc[-1] += ""  # keep order
        args[args.index("-filter_complex") + 1] += f";{''.join(labels)}amix=inputs={len(labels)}:duration=first:normalize=0[aout]"
        args += ["-map", "[aout]", "-c:a", "aac", "-b:a", "160k"]
    else:
        args[args.index("-filter_complex") + 1] = args[args.index("-filter_complex") + 1].replace(";[1:a]anull[sil]", "")
        args += ["-an"]
    args += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-t", f"{out_dur:.3f}", "-movflags", "+faststart", dst]
    run_ffmpeg(args, out_dur, progress)
