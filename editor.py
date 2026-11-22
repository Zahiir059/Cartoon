"""Video Editor. FFmpeg does all the work; `build_spec()` produces the dict documented in media.apply_edit."""
import os, shutil, time, uuid
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame, QComboBox, QSlider, QCheckBox,
                               QTabWidget, QMessageBox, QTableWidget, QTableWidgetItem, QDoubleSpinBox, QFileDialog, QHeaderView,
                               QLineEdit, QGridLayout, QProgressBar)
from .. import media
from ..jobs import FuncWorker
from ..paths import library_dir, temp_dir
from ..widgets import Card, GradientButton, SmallButton, RangeBar, VideoPlayer, Spinner, label


def hslider(lo, hi, val, fmt=lambda v: str(v)):
    s = QSlider(Qt.Horizontal); s.setRange(lo, hi); s.setValue(val)
    l = label(fmt(val), "sub"); l.setMinimumWidth(48); s.valueChanged.connect(lambda v: l.setText(fmt(v)))
    w = QWidget(); r = QHBoxLayout(w); r.setContentsMargins(0, 0, 0, 0); r.addWidget(s, 1); r.addWidget(l)
    w.slider = s
    return w


class AudioSource(QWidget):
    """A pick-a-file row with volume (and optional start time)."""
    def __init__(self, title, timed=False, trim=False):
        super().__init__()
        self.path = ""; lay = QVBoxLayout(self); lay.setContentsMargins(0, 4, 0, 4); lay.setSpacing(4)
        top = QHBoxLayout(); top.addWidget(label(title)); self.name = label("none", "sub"); top.addWidget(self.name, 1)
        pick = SmallButton("Choose…"); clr = SmallButton("Clear"); top.addWidget(pick); top.addWidget(clr); lay.addLayout(top)
        self.vol = hslider(0, 200, 100, lambda v: f"{v}%"); lay.addWidget(self.vol)
        row = QHBoxLayout(); self.at = self.ts = self.tl = None
        if timed:
            self.at = QDoubleSpinBox(); self.at.setRange(0, 600); self.at.setSuffix(" s"); row.addWidget(label("Starts at", "sub")); row.addWidget(self.at)
        if trim:
            self.ts = QDoubleSpinBox(); self.ts.setRange(0, 3600); self.ts.setSuffix(" s")
            self.tl = QDoubleSpinBox(); self.tl.setRange(0, 3600); self.tl.setSuffix(" s"); self.tl.setSpecialValueText("full")
            row.addWidget(label("Trim from", "sub")); row.addWidget(self.ts); row.addWidget(label("length", "sub")); row.addWidget(self.tl)
        row.addStretch(); lay.addLayout(row)
        pick.clicked.connect(self._pick); clr.clicked.connect(self._clear)

    def _pick(self):
        f, _ = QFileDialog.getOpenFileName(self, "Choose audio", "", "Audio (*.mp3 *.wav *.aac *.m4a *.ogg *.flac *.mp4 *.mov)")
        if f:
            self.path = f; self.name.setText(os.path.basename(f))

    def _clear(self):
        self.path = ""; self.name.setText("none")

    def spec(self):
        if not self.path:
            return None
        d = dict(path=self.path, volume=self.vol.slider.value() / 100)
        if self.at: d["at"] = self.at.value()
        if self.ts: d["trim_start"] = self.ts.value(); d["trim_len"] = self.tl.value() or None
        return d


class EditorPage(QScrollArea):
    def __init__(self, ctx):
        super().__init__()
        self.ctx = ctx; self.src = None; self.info = None; self.pid = 0; self.worker = None; self.preview_file = None
        self.setWidgetResizable(True); self.setFrameShape(QFrame.NoFrame)
        root = QWidget(); self.setWidget(root)
        v = QVBoxLayout(root); v.setContentsMargins(28, 22, 28, 28); v.setSpacing(14)
        top = QHBoxLayout(); top.addWidget(label("Video Editor", "h1")); top.addStretch()
        self.open_btn = SmallButton("Open video…", "upload"); top.addWidget(self.open_btn); v.addLayout(top)
        self.title = label("Open a video or choose one from My Creations to start editing.", "sub", True); v.addWidget(self.title)
        cols = QHBoxLayout(); cols.setSpacing(18); v.addLayout(cols)

        left = Card(shadow_on=False); ll = QVBoxLayout(left); ll.setContentsMargins(18, 16, 18, 16)
        self.player = VideoPlayer(); self.player.video.setMinimumHeight(300); ll.addWidget(self.player, 1)
        self.trim = RangeBar(); ll.addWidget(self.trim)
        tr = QHBoxLayout()
        b1 = SmallButton("Start = playhead"); b2 = SmallButton("End = playhead"); self.split_btn = SmallButton("Split at playhead", "editor")
        for b in (b1, b2, self.split_btn): tr.addWidget(b)
        tr.addStretch(); ll.addLayout(tr)
        self.back_btn = SmallButton("← Back to source video"); self.back_btn.setVisible(False); ll.addWidget(self.back_btn)
        cols.addWidget(left, 3)

        right = Card(shadow_on=False); right.setFixedWidth(440); rl = QVBoxLayout(right); rl.setContentsMargins(14, 14, 14, 16)
        self.tabs = QTabWidget(); self.tabs.setUsesScrollButtons(False); self.tabs.setStyleSheet("QTabBar::tab{padding:7px 8px;margin-right:0px;}"); rl.addWidget(self.tabs, 1); cols.addWidget(right, 0, Qt.AlignTop)

        # Transform
        t = QWidget(); tl = QVBoxLayout(t); tl.setSpacing(6)
        self.rot = QComboBox(); self.rot.addItems(["No rotation", "Rotate 90°", "Rotate 180°", "Rotate 270°"])
        self.fh = QCheckBox("Flip horizontally"); self.fv = QCheckBox("Flip vertically")
        self.zoom = hslider(20, 100, 100, lambda v: f"{v}%"); self.panx = hslider(0, 100, 50, lambda v: f"{v}%"); self.pany = hslider(0, 100, 50, lambda v: f"{v}%")
        self.aspect = QComboBox(); self.aspect.addItems(["Original", "1:1", "16:9", "9:16", "4:5"])
        for w in (label("Rotate", "sub"), self.rot, self.fh, self.fv, label("Crop: visible area (zoom)", "sub"), self.zoom,
                  label("Crop: horizontal position", "sub"), self.panx, label("Crop: vertical position", "sub"), self.pany,
                  label("Crop to aspect ratio", "sub"), self.aspect):
            tl.addWidget(w)
        tl.addStretch(); self.tabs.addTab(t, "Transform")

        # Color & speed
        c = QWidget(); cl = QVBoxLayout(c); cl.setSpacing(6)
        self.speed = QDoubleSpinBox(); self.speed.setRange(0.25, 4.0); self.speed.setSingleStep(0.25); self.speed.setValue(1.0); self.speed.setSuffix("×")
        pr = QHBoxLayout()
        for txt, val in (("Slow-mo 0.5×", .5), ("Normal", 1.0), ("Fast 2×", 2.0)):
            b = SmallButton(txt); b.clicked.connect(lambda _, x=val: self.speed.setValue(x)); pr.addWidget(b)
        self.bri = hslider(-50, 50, 0, lambda v: f"{v / 100:+.2f}"); self.con = hslider(50, 200, 100, lambda v: f"{v / 100:.2f}")
        self.sat = hslider(0, 300, 100, lambda v: f"{v / 100:.2f}")
        for w in (label("Speed", "sub"), self.speed, pr, label("Brightness", "sub"), self.bri, label("Contrast", "sub"), self.con,
                  label("Saturation", "sub"), self.sat):
            cl.addWidget(w) if isinstance(w, QWidget) else cl.addLayout(w)
        cl.addStretch(); self.tabs.addTab(c, "Color")

        # Text overlays
        self.text_tbl = self._table(["Text", "Start s", "End s", "Size", "Position"]); self.tabs.addTab(self._table_tab(
            self.text_tbl, lambda: self._add_text(), "Text appears on the output timeline. Size is relative to a 720p frame."), "Text")
        self.sub_tbl = self._table(["Start s", "End s", "Subtitle"]); self.tabs.addTab(self._table_tab(
            self.sub_tbl, lambda: self._add_sub(), "Automatic speech-to-text is not included in this build: type your subtitle lines manually."), "Subs")

        # Audio
        a = QWidget(); al = QVBoxLayout(a); al.setSpacing(4)
        self.mute = QCheckBox("Remove original audio"); self.vol = hslider(0, 200, 100, lambda v: f"{v}%")
        self.music = AudioSource("Background music", timed=True, trim=True); self.vo = AudioSource("Voiceover (recorded file)", timed=True)
        self.sfx = AudioSource("Sound effect", timed=True)
        for w in (self.mute, label("Original audio volume", "sub"), self.vol, self.music, self.vo, self.sfx):
            al.addWidget(w)
        al.addStretch(); self.tabs.addTab(a, "Audio")

        # Export
        e = QWidget(); el = QVBoxLayout(e); el.setSpacing(6)
        self.res = QComboBox(); self.easpect = QComboBox(); self.easpect.addItems(["Original", "16:9", "9:16", "1:1"])
        for w in (label("Resolution (shorter side)", "sub"), self.res, label("Aspect ratio", "sub"), self.easpect,
                  label("Only resolutions up to the video's own size are offered — upscaling adds no real detail.", "sub")):
            el.addWidget(w)
        el.itemAt(el.count() - 1).widget().setWordWrap(True)
        self.exp_btn = GradientButton("Export MP4…", "download"); el.addSpacing(8); el.addWidget(self.exp_btn); el.addStretch()
        self.tabs.addTab(e, "Export")

        bt = QHBoxLayout()
        self.prev_btn = SmallButton("Render preview", "play"); self.save_btn = SmallButton("Save to My Creations", "check")
        bt.addWidget(self.prev_btn); bt.addWidget(self.save_btn); rl.addLayout(bt)
        sr = QHBoxLayout(); self.spin = Spinner(22); self.status = label("", "sub", True); sr.addWidget(self.spin); sr.addWidget(self.status, 1); rl.addLayout(sr)
        self.bar = QProgressBar(); self.bar.setVisible(False); rl.addWidget(self.bar)

        self.open_btn.clicked.connect(self.browse); b1.clicked.connect(self._set_start); b2.clicked.connect(self._set_end)
        self.split_btn.clicked.connect(self.split); self.back_btn.clicked.connect(self._back)
        self.prev_btn.clicked.connect(self.preview); self.save_btn.clicked.connect(self.save); self.exp_btn.clicked.connect(self.export)
        self._enable(False)

    # -------------------------------------------------------------- tables
    def _table(self, cols):
        t = QTableWidget(0, len(cols)); t.setHorizontalHeaderLabels(cols); t.verticalHeader().setVisible(False)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch); t.setMinimumHeight(180); return t

    def _table_tab(self, tbl, add, note):
        w = QWidget(); l = QVBoxLayout(w); n = label(note, "sub", True); n.setStyleSheet("font-size:11px;"); l.addWidget(n); l.addWidget(tbl)
        r = QHBoxLayout(); a = SmallButton("Add line", "plus"); d = SmallButton("Remove selected", "trash", danger=True)
        a.clicked.connect(add); d.clicked.connect(lambda: [tbl.removeRow(i.row()) for i in sorted(tbl.selectionModel().selectedRows(), key=lambda x: -x.row())])
        r.addWidget(a); r.addWidget(d); r.addStretch(); l.addLayout(r); return w

    def _add_text(self):
        t = self.text_tbl; r = t.rowCount(); t.insertRow(r)
        for i, v in enumerate(["Your text", "0", str(round(min(3, (self.info or {"duration": 3})["duration"]), 1)), "36", "Bottom"]):
            t.setItem(r, i, QTableWidgetItem(v))

    def _add_sub(self):
        t = self.sub_tbl; r = t.rowCount(); t.insertRow(r)
        s = (self.player.player.position() / 1000) - self.trim.a if self.info else 0
        for i, v in enumerate([f"{max(0, s):.1f}", f"{max(0, s) + 2:.1f}", "Subtitle text"]):
            t.setItem(r, i, QTableWidgetItem(v))

    # -------------------------------------------------------------- loading
    def _enable(self, on):
        for w in (self.tabs, self.prev_btn, self.save_btn, self.split_btn, self.trim):
            w.setEnabled(on)

    def browse(self):
        f, _ = QFileDialog.getOpenFileName(self, "Open video", "", "Videos (*.mp4 *.mov *.mkv *.avi *.webm *.m4v *.wmv *.flv *.mpg *.mpeg *.3gp)")
        if f:
            self.load(f, 0)

    def load(self, path, pid=0):
        try:
            info = media.probe(path)
        except media.MediaError as e:
            QMessageBox.warning(self, "Cannot open video", str(e)); return
        self.src, self.info, self.pid = path, info, pid
        self.player.set_source(path); self.trim.set_duration(info["duration"]); self.back_btn.setVisible(False)
        self.title.setText(f"Editing: {os.path.basename(path)}  ·  {info['duration']:.1f}s  ·  {info['width']}×{info['height']}")
        self.res.clear(); self.res.addItem("Original size", 0)
        for h in (480, 720, 1080):
            if h <= min(info["width"], info["height"]):
                self.res.addItem(f"{h}p", h)
        self._enable(True)

    def _set_start(self): self.trim.set_range(min(self.player.player.position() / 1000, self.trim.b - .1), self.trim.b)
    def _set_end(self): self.trim.set_range(self.trim.a, max(self.player.player.position() / 1000, self.trim.a + .1))

    def _back(self):
        if self.src:
            self.player.set_source(self.src); self.back_btn.setVisible(False)

    # -------------------------------------------------------------- spec
    def build_spec(self, export=False):
        def num(it, d=0.0):
            try:
                return float(it.text())
            except (ValueError, AttributeError):
                raise media.MediaError("Please check the numeric values in the Text/Subtitle tables.")
        z = self.zoom.slider.value() / 100
        spec = dict(start=self.trim.a, end=self.trim.b, rotate=[0, 90, 180, 270][self.rot.currentIndex()],
                    flip_h=self.fh.isChecked(), flip_v=self.fv.isChecked(), aspect_crop=self.aspect.currentText(),
                    speed=self.speed.value(), brightness=self.bri.slider.value() / 100, contrast=self.con.slider.value() / 100,
                    saturation=self.sat.slider.value() / 100, mute=self.mute.isChecked(), volume=self.vol.slider.value() / 100,
                    music=self.music.spec(), voiceover=self.vo.spec(), sfx=self.sfx.spec())
        if z < 1:
            spec["crop"] = (z, z, (1 - z) * self.panx.slider.value() / 100, (1 - z) * self.pany.slider.value() / 100)
        t = self.text_tbl
        spec["texts"] = [dict(text=t.item(r, 0).text(), start=num(t.item(r, 1)), end=num(t.item(r, 2)), size=int(num(t.item(r, 3), 36)),
                              pos=t.item(r, 4).text().capitalize()) for r in range(t.rowCount()) if t.item(r, 0)]
        s = self.sub_tbl
        spec["subs"] = [dict(start=num(s.item(r, 0)), end=num(s.item(r, 1)), text=s.item(r, 2).text()) for r in range(s.rowCount()) if s.item(r, 2)]
        if export:
            spec["export_height"] = self.res.currentData() or None
            spec["export_aspect"] = self.easpect.currentText()
        return spec

    # -------------------------------------------------------------- background rendering
    def _run(self, fn, done, busy_msg):
        if self.worker and self.worker.isRunning():
            return
        self._enable(False); self.spin.start(); self.bar.setVisible(True); self.bar.setValue(0); self.status.setText(busy_msg)
        self.worker = FuncWorker(fn, self)
        self.worker.progress.connect(lambda p, m: self.bar.setValue(p))
        self.worker.done.connect(lambda r: (self._idle(), done(r)))
        self.worker.failed.connect(lambda m, rt: (self._idle(), self.status.setText("❌ " + m)))
        self.worker.start()

    def _idle(self):
        self.spin.stop(); self.bar.setVisible(False); self._enable(True)

    def preview(self):
        try:
            spec = self.build_spec()
        except media.MediaError as e:
            self.status.setText("❌ " + str(e)); return
        dst = str(temp_dir() / f"edit_{uuid.uuid4().hex[:8]}.mp4"); src, info = self.src, self.info
        def done(_):
            self.preview_file = dst; self.player.set_source(dst); self.back_btn.setVisible(True); self.status.setText("Preview ready.")
        self._run(lambda p, c: media.apply_edit(src, dst, info, spec, lambda x: p(x)), done, "Rendering preview…")

    def save(self):
        try:
            spec = self.build_spec()
        except media.MediaError as e:
            self.status.setText("❌ " + str(e)); return
        d = library_dir() / f"e{int(time.time() * 1000)}"; d.mkdir(parents=True); dst = str(d / "edit.mp4")
        src, info = self.src, self.info
        name = os.path.splitext(os.path.basename(src))[0] + " (edited)"
        def job(p, c):
            media.apply_edit(src, dst, info, spec, lambda x: p(x)); return self.ctx.make_thumb(dst)
        def done(th):
            self.ctx.db.add(name=name, style="Edited", status="Completed", original_path=src if self.pid == 0 else "", output_path=dst,
                            thumb=th, kind="edit")
            self.ctx.projects_changed.emit(); self.status.setText("Saved to My Creations.")
        self._run(job, done, "Saving edit…")

    def export(self):
        f, _ = QFileDialog.getSaveFileName(self, "Export MP4", "export.mp4", "MP4 video (*.mp4)")
        if not f:
            return
        try:
            spec = self.build_spec(export=True)
        except media.MediaError as e:
            self.status.setText("❌ " + str(e)); return
        src, info = self.src, self.info
        self._run(lambda p, c: media.apply_edit(src, f, info, spec, lambda x: p(x)), lambda _: self.status.setText(f"Exported to {f}"), "Exporting…")

    def split(self):
        t = self.player.player.position() / 1000
        if not self.src or t < .2 or t > self.info["duration"] - .2:
            self.status.setText("Move the playhead inside the video first."); return
        d = library_dir() / f"s{int(time.time() * 1000)}"; d.mkdir(parents=True); a, b = str(d / "part1.mp4"), str(d / "part2.mp4")
        src, total, base = self.src, self.info["duration"], os.path.splitext(os.path.basename(self.src))[0]
        def job(p, c):
            media.split_at(src, t, a, b, total); return self.ctx.make_thumb(a), self.ctx.make_thumb(b)
        def done(th):
            for nm, f, tt in ((f"{base} – part 1", a, th[0]), (f"{base} – part 2", b, th[1])):
                self.ctx.db.add(name=nm, style="Split", status="Completed", output_path=f, thumb=tt, kind="edit")
            self.ctx.projects_changed.emit(); self.status.setText("Split into two clips — saved in My Creations.")
        self._run(job, done, "Splitting…")

    def release_files(self):
        self.player.clear()
