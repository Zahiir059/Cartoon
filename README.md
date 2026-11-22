# Cartoon AI — video → cartoon studio (Windows 10/11)

## Get Cartoon.exe (pick one)
**A. On any Windows PC:** double-click `build_exe.bat` (needs Python 3.10–3.12 from python.org; the script does everything and self-tests the EXE).
Result: `dist\Cartoon.exe` — one file, no Python/FFmpeg/installer needed to *run* it.

**B. No Python at all:** push this folder to a GitHub repo → Actions → "Build Cartoon.exe" → Run workflow → download the `Cartoon.exe` artifact.

## Using it
* Without an API key the app runs in clearly labelled **Demo Mode** (placeholder clip, not AI).
* For real AI: Settings → paste a Replicate API token (replicate.com/account/api-tokens). Internet required; Replicate bills usage.
  Default model: `philz1337x/video-style-transfer` (changeable in Settings).
* AI clips are limited to 10 s (trim bar). Editor/export work offline.

## Layout
`main.py` · `cartoon_ai/` (ui pages, media.py = FFmpeg, providers/ = AI adapters, db.py = SQLite, secrets_store.py = Credential Manager)
New AI provider: subclass `providers.base.Provider`, register in `providers/__init__.py`.
