import os, shutil, time, uuid
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QComboBox, QSlider,
                               QTextEdit, QCheckBox, QProgressBar, QTabWidget, QStackedWidget, QMessageBox, QGridLayout, QPushButton)
from .. import media, theme, icons
from ..jobs import FuncWorker
from ..paths import library_dir, temp_dir
from ..providers import AIParams
from ..styles_data import STYLE_BY_ID
from ..widgets import (Card, GradientButton, SmallButton, DropZone, RangeBar, VideoPlayer, CompareView, Spinner,
                       label, pick_file)
from ..theme import PINK, VIOLET, CYAN


class StudioPage(QScrollArea):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx; self.src = None; self.info = None; self.worker = None; self.busy = False
        self.cur_pid = 0; self.cur_paths = None
        self.setWidgetResizable(True); self.setFrameShape(QFrame.NoFrame)
        root = QWidget(); self.setWidget(root)
        v = QVBoxLayout(root); v.setContentsMargins(28, 22, 28, 28); v.setSpacing(14)
        v.addWidget(label("AI Video Studio", "h1"))
        self.banner = label("", "banner", True); v.addWidget(self.banner)

        cols = QHBoxLayout(); cols.setSpacing(18); v.addLayout(cols)
        left = QVBoxLayout(); left.setSpacing(18); cols.addLayout(left, 3)

        # ---------------- original
        oc = Card(shadow_on=False); ol = QVBoxLayout(oc); ol.setContentsMargins(18, 16, 18, 16)
        top = QHBoxLayout(); top.addWidget(label("1 · Original video", "h2")); top.addStretch()
        self.replace_btn = SmallButton("Replace", "upload"); self.remove_btn = SmallButton("Remove", "trash", danger=True)
        top.addWidget(self.replace_btn); top.addWidget(self.remove_btn); ol.addLayout(top)
        self.src_stack = QStackedWidget(); ol.addWidget(self.src_stack)
        self.drop = DropZone(); self.src_stack.addWidget(self.drop)
        sv = QWidget(); svl = QVBoxLayout(sv); svl.setContentsMargins(0, 0, 0, 0)
        self.player = VideoPlayer(); self.player.video.setMinimumHeight(240); svl.addWidget(self.player, 1)
        self.info_lbl = label("", "sub"); svl.addWidget(self.info_lbl)
        self.warn = label("", "banner", True); svl.addWidget(self.warn)
        self.range = RangeBar(); svl.addWidget(self.range)
        opts = QHBoxLayout()
        self.rot = QComboBox(); self.rot.addItems(["No rotation", "Rotate 90°", "Rotate 180°", "Rotate 270°"])
        self.crop = QComboBox(); self.crop.addItems(["Original", "1:1", "16:9", "9:16", "4:5"])
        opts.addWidget(label("Rotate", "sub")); opts.addWidget(self.rot); opts.addWidget(label("Crop to", "sub")); opts.addWidget(self.crop)
        opts.addWidget(label("(applied when generating)", "sub")); opts.addStretch(); svl.addLayout(opts)
        self.src_stack.addWidget(sv); left.addWidget(oc)

        # ---------------- output
        out = Card(shadow_on=False); oul = QVBoxLayout(out); oul.setContentsMargins(18, 16, 18, 16)
        oul.addWidget(label("3 · Cartoon result", "h2"))
        self.out_stack = QStackedWidget(); oul.addWidget(self.out_stack)
        ph = QLabel("Your cartoon video will appear here"); ph.setAlignment(Qt.AlignCenter); ph.setObjectName("sub")
        ph.setMinimumHeight(220); self.out_stack.addWidget(ph)
        self.tabs = QTabWidget(); self.out_player = VideoPlayer(); self.compare = CompareView()
        self.tabs.addTab(self.out_player, "Cartoon"); self.tabs.addTab(self.compare, "Side by side")
        self.out_stack.addWidget(self.tabs)
        row = QHBoxLayout()
        self.regen_btn = SmallButton("Regenerate", "refresh"); self.fav_btn = SmallButton("Save to favorites", "heart")
        self.edit_btn = SmallButton("Open in editor", "edit"); self.exp_btn = SmallButton("Export MP4…", "download")
        for b in (self.regen_btn, self.fav_btn, self.edit_btn, self.exp_btn):
            row.addWidget(b); b.setEnabled(False)
        row.addStretch(); oul.addLayout(row); left.addWidget(out); left.addStretch()

        # ---------------- controls
        cc = Card(shadow_on=False); cc.setFixedWidth(370); cols.addWidget(cc, 0, Qt.AlignTop)
        cl = QVBoxLayout(cc); cl.setContentsMargins(18, 16, 18, 18); cl.setSpacing(8)
        cl.addWidget(label("2 · Style & AI controls", "h2"))
        sr = QHBoxLayout(); self.style_lbl = label(""); self.style_lbl.setStyleSheet("font-weight:800;font-size:15px;")
        ch = SmallButton("Change"); ch.clicked.connect(lambda: ctx.navigate.emit("styles"))
        sr.addWidget(label("Style:", "sub")); sr.addWidget(self.style_lbl, 1); sr.addWidget(ch); cl.addLayout(sr)

        self.adv = QWidget(); al = QVBoxLayout(self.adv); al.setContentsMargins(0, 0, 0, 0); al.setSpacing(8); cl.addWidget(self.adv)

        def slider(title, tip, default):
            r = QHBoxLayout(); l = label(title); val = label(str(default), "sub")
            s = QSlider(Qt.Horizontal); s.setRange(0, 100); s.setValue(default); s.setToolTip(tip)
            s.valueChanged.connect(lambda x: val.setText(str(x)))
            r.addWidget(l); r.addStretch(); r.addWidget(val); al.addLayout(r); al.addWidget(s); return s, l
        self.s_int, self.l_int = slider("Style Intensity", "How strongly the model follows the style prompt (maps to the model's cfg_scale).", 40)
        self.s_det, self.l_det = slider("Detail Enhancement", "More denoising steps → finer detail, slower and costlier.", 40)
        al.addWidget(label("Output quality", "sub")); self.quality = QComboBox(); al.addWidget(self.quality)
        al.addWidget(label("Custom AI prompt (added to the style prompt)", "sub"))
        self.prompt = QTextEdit(); self.prompt.setFixedHeight(64); self.prompt.setPlaceholderText("e.g. a girl dancing in a sunny park, smiling")
        al.addWidget(self.prompt)
        al.addWidget(label("Negative prompt", "sub")); self.neg = QTextEdit(); self.neg.setFixedHeight(54)
        self.neg.setPlaceholderText("things to avoid, e.g. blurry, extra fingers"); al.addWidget(self.neg)
        self.keep_audio = QCheckBox("Keep original audio"); self.keep_audio.setChecked(True); cl.addWidget(self.keep_audio)
        self.note = label("", "sub", True); self.note.setStyleSheet("font-size:11px;"); cl.addWidget(self.note)
        self.gen = GradientButton("Generate Cartoon", "sparkle", height=52); cl.addWidget(self.gen)
        self.cancel_btn = SmallButton("Cancel job", "stop"); self.cancel_btn.setVisible(False); cl.addWidget(self.cancel_btn)
        pr = QHBoxLayout(); self.spin = Spinner(26); self.status = label("", "sub", True)
        pr.addWidget(self.spin); pr.addWidget(self.status, 1); cl.addLayout(pr)
        self.bar = QProgressBar(); self.bar.setVisible(False); cl.addWidget(self.bar)

        # ---------------- wiring
        self.drop.fileDropped.connect(self.load_video); self.drop.clicked.connect(self.browse)
        self.replace_btn.clicked.connect(self.browse); self.remove_btn.clicked.connect(self.remove)
        self.range.changed.connect(self._range_changed)
        self.gen.clicked.connect(self.generate); self.regen_btn.clicked.connect(self.generate)
        self.cancel_btn.clicked.connect(lambda: self.worker and self.worker.cancel())
        self.fav_btn.clicked.connect(self.fav); self.edit_btn.clicked.connect(self.to_editor); self.exp_btn.clicked.connect(self.export)
        ctx.style_changed.connect(self._style); self._style(ctx.selected_style)
        self.sync_provider(); self._update_gen()

    # ------------------------------------------------------------------ provider state
    def sync_provider(self):
        prov = self.ctx.provider(); self.prov = prov
        self.quality.clear()
        for px, txt in prov.quality_options:
            self.quality.addItem(txt, px)
        if prov.is_demo:
            self.banner.setObjectName("banner")
            self.banner.setText("🎭  DEMO MODE — no AI service is connected. Results are labelled placeholder samples and are NOT generated "
                                "from your video. To get real AI cartoons, add a Replicate API key in Settings (internet required).")
        else:
            self.banner.setObjectName("banner_ok")
            self.banner.setText(f"✅  Connected to {prov.name}. Videos are uploaded to the AI service for processing — an internet connection is required.")
        self.banner.setStyleSheet("")  # re-polish for objectName change
        self.banner.style().unpolish(self.banner); self.banner.style().polish(self.banner)
        self.adv.setVisible(not prov.is_demo)   # never show controls that nothing is behind
        self.note.setText("Demo Mode: AI controls (style intensity, detail, prompts, quality) appear once an AI service is connected." if prov.is_demo else
                          "Only controls supported by the connected model are shown. Face / character / motion preservation, "
                          "palette and lighting sliders are intentionally absent: this model doesn't expose them.")

    def refresh(self):
        self.sync_provider(); self._update_gen()

    def _style(self, sid):
        self.style_lbl.setText(STYLE_BY_ID[sid][1])

    # ------------------------------------------------------------------ source handling
    def browse(self):
        f = pick_file(self, "Choose a video", "Videos (*.mp4 *.mov *.mkv *.avi *.webm *.m4v *.wmv *.flv *.mpg *.mpeg *.3gp);;All files (*)")
        if f:
            self.load_video(f)

    def load_video(self, path):
        try:
            info = media.probe(path)
        except media.MediaError as e:
            QMessageBox.warning(self, "Cannot open video", str(e)); return
        self.src, self.info = path, info
        self.player.set_source(path)
        self.range.set_duration(info["duration"], media.MAX_AI_SECONDS)
        self.info_lbl.setText(f"{os.path.basename(path)}  ·  {info['duration']:.1f}s  ·  {info['width']}×{info['height']}  ·  "
                              f"{info['fps']:.0f} fps  ·  {info['size'] / 1e6:.1f} MB")
        self.src_stack.setCurrentIndex(1); self._update_gen()

    def remove(self):
        self.player.clear(); self.src = self.info = None; self.src_stack.setCurrentIndex(0); self._update_gen()

    def _range_changed(self, a, b):
        if self.info:
            self.player.player.setPosition(int(a * 1000))
            if self.info["duration"] > media.MAX_AI_SECONDS + 0.05:
                self.warn.setText(f"This video is {self.info['duration']:.1f}s. AI transformation is limited to 10 seconds — "
                                  f"drag the window above to choose the segment ({b - a:.1f}s selected).")
                self.warn.setVisible(True)
            else:
                self.warn.setVisible(False)
        self._update_gen()

    def _update_gen(self):
        ok = bool(self.src) and not self.busy and (self.range.b - self.range.a) <= media.MAX_AI_SECONDS + 0.05
        self.gen.setEnabled(ok); self.regen_btn.setEnabled(ok and self.cur_pid > 0)
        self.remove_btn.setEnabled(not self.busy); self.replace_btn.setEnabled(not self.busy)
        if not self.src:
            self.warn.setVisible(False)

    # ------------------------------------------------------------------ generation
    def generate(self):
        if not self.src or self.busy:
            return
        a, b = self.range.a, self.range.b
        if b - a > media.MAX_AI_SECONDS + 0.05:
            QMessageBox.warning(self, "Too long", "Select a segment of 10 seconds or less."); return
        prov = self.ctx.provider(); self.prov = prov
        st = STYLE_BY_ID[self.ctx.selected_style]
        user_p, user_n = self.prompt.toPlainText().strip(), self.neg.toPlainText().strip()
        prompt = ", ".join(x for x in (st[3], user_p) if x)
        neg = ", ".join(x for x in (st[4], user_n) if x)
        quality = self.quality.currentData() or 512
        rot = [0, 90, 180, 270][self.rot.currentIndex()]; aspect = self.crop.currentText()
        d = library_dir() / f"p{int(time.time() * 1000)}"; d.mkdir(parents=True, exist_ok=True)
        orig, raw, final = str(d / "original.mp4"), str(d / "cartoon_raw.mp4"), str(d / "cartoon.mp4")
        prep = str(temp_dir() / f"prep_{uuid.uuid4().hex[:8]}.mp4")
        src, keep = self.src, self.keep_audio.isChecked()
        name = f"{os.path.splitext(os.path.basename(src))[0]} – {st[1]}"
        intensity, detail = self.s_int.value(), self.s_det.value()
        pid = self.ctx.db.add(name=name, style=st[1], status="Processing", original_path=orig, prompt=user_p,
                              provider=prov.id, demo=int(prov.is_demo), kind="ai",
                              params=dict(intensity=intensity, detail=detail, quality=quality, negative=user_n))
        self.cur_pid = pid; self.cur_paths = (orig, final)
        self.ctx.projects_changed.emit()

        def job(progress, cancel):
            progress(2, "Preparing your clip…")
            media.prepare_clip(src, orig, a, b - a, rot, aspect, None, True, lambda p: progress(2 + p * .05, "Preparing your clip…"))
            oinfo = media.probe(orig)
            media.prepare_clip(src, prep, a, b - a, rot, aspect, quality, False)
            pinfo = media.probe(prep)
            params = AIParams(self.ctx.selected_style, prompt, neg, intensity, detail, quality, pinfo["width"], pinfo["height"])
            res = prov.run(prep, params, raw, progress, cancel)
            if keep and oinfo["has_audio"] and not prov.is_demo:
                progress(97, "Adding original audio…")
                media.mux_audio(res, orig, final)
            else:
                shutil.move(res, final)
            media.probe(final)   # validate the file we got back
            return dict(thumb=self.ctx.make_thumb(final))

        self._set_busy(True, "Starting…")
        self.worker = FuncWorker(job, self)
        self.worker.progress.connect(lambda p, m: self._progress(p, m))
        self.worker.done.connect(lambda r: self._done(pid, r, prep, raw))
        self.worker.failed.connect(lambda m, rt: self._failed(pid, m, rt, prep))
        self.worker.start()

    def _set_busy(self, b, msg=""):
        self.busy = b; self.spin.start() if b else self.spin.stop()
        self.bar.setVisible(b); self.cancel_btn.setVisible(b and not self.prov.is_demo)
        if b:
            self.bar.setValue(0); self.status.setText(msg)
        self._update_gen()

    def _progress(self, p, m):
        self.bar.setValue(p)
        if m:
            self.status.setText(m)

    def _cleanup(self, *files):
        for f in files:
            try:
                os.remove(f)
            except OSError:
                pass

    def _done(self, pid, res, prep, raw):
        self._cleanup(prep, raw)
        orig, final = self.cur_paths
        self.ctx.db.update(pid, status="Completed", output_path=final, thumb=res["thumb"], error="")
        self._set_busy(False)
        self.status.setText("✅ Done." + ("  (Demo placeholder – not AI generated)" if self.prov.is_demo else ""))
        self.out_stack.setCurrentIndex(1); self.out_player.set_source(final); self.compare.set_sources(orig, final)
        for b in (self.fav_btn, self.edit_btn, self.exp_btn):
            b.setEnabled(True)
        self.fav_btn.setText("Save to favorites"); self._update_gen()
        self.ctx.projects_changed.emit()

    def _failed(self, pid, msg, retryable, prep):
        self._cleanup(prep)
        self.ctx.db.update(pid, status="Failed", error=msg)
        self._set_busy(False)
        self.status.setText("❌ " + msg + ("  — you can press Regenerate to retry." if retryable else ""))
        self.regen_btn.setEnabled(bool(self.src)); self.ctx.projects_changed.emit()

    # ------------------------------------------------------------------ result actions
    def fav(self):
        if self.cur_pid:
            p = self.ctx.db.get(self.cur_pid); nv = 0 if p["favorite"] else 1
            self.ctx.db.update(self.cur_pid, favorite=nv)
            self.fav_btn.setText("★ In favorites" if nv else "Save to favorites"); self.ctx.projects_changed.emit()

    def to_editor(self):
        if self.cur_paths:
            self.ctx.open_editor.emit(self.cur_paths[1], self.cur_pid)

    def export(self):
        from PySide6.QtWidgets import QFileDialog
        if not self.cur_paths:
            return
        f, _ = QFileDialog.getSaveFileName(self, "Export MP4", "cartoon.mp4", "MP4 video (*.mp4)")
        if f:
            shutil.copyfile(self.cur_paths[1], f); self.status.setText(f"Exported to {f}")

    def load_external(self, path):
        self.load_video(path)

    def release_files(self):
        self.out_player.clear(); self.compare.clear()
