import sqlite3, time, json, os
from .paths import data_dir

COLS = ["id", "name", "created", "style", "status", "original_path", "output_path", "thumb",
        "favorite", "prompt", "params", "provider", "demo", "kind", "error"]


class DB:
    def __init__(self):
        self.con = sqlite3.connect(str(data_dir() / "projects.db"), check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        self.con.execute("""CREATE TABLE IF NOT EXISTS projects(
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, created REAL, style TEXT, status TEXT,
            original_path TEXT, output_path TEXT, thumb TEXT, favorite INTEGER DEFAULT 0,
            prompt TEXT, params TEXT, provider TEXT, demo INTEGER DEFAULT 0, kind TEXT DEFAULT 'ai', error TEXT)""")
        self.con.commit()

    def add(self, **kw) -> int:
        kw.setdefault("created", time.time())
        kw.setdefault("status", "Queued")
        if isinstance(kw.get("params"), dict):
            kw["params"] = json.dumps(kw["params"])
        keys = [k for k in kw if k in COLS]
        cur = self.con.execute(f"INSERT INTO projects({','.join(keys)}) VALUES({','.join('?'*len(keys))})",
                               [kw[k] for k in keys])
        self.con.commit()
        return cur.lastrowid

    def update(self, pid: int, **kw):
        keys = [k for k in kw if k in COLS and k != "id"]
        if not keys:
            return
        self.con.execute(f"UPDATE projects SET {','.join(k+'=?' for k in keys)} WHERE id=?",
                         [kw[k] for k in keys] + [pid])
        self.con.commit()

    def get(self, pid: int):
        r = self.con.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
        return dict(r) if r else None

    def list(self, search: str = "", filt: str = "all", limit: int | None = None):
        q, a = "SELECT * FROM projects WHERE 1=1", []
        if search:
            q += " AND (name LIKE ? OR style LIKE ?)"
            a += [f"%{search}%"] * 2
        if filt == "favorites":
            q += " AND favorite=1"
        elif filt == "generated":
            q += " AND kind='ai' AND status='Completed'"
        elif filt == "originals":
            q += " AND original_path IS NOT NULL AND original_path<>''"
        elif filt == "edited":
            q += " AND kind='edit'"
        q += " ORDER BY created DESC"
        if limit:
            q += f" LIMIT {int(limit)}"
        return [dict(r) for r in self.con.execute(q, a).fetchall()]

    def delete(self, pid: int, remove_files: bool = True):
        p = self.get(pid)
        if p and remove_files:
            for k in ("original_path", "output_path", "thumb"):
                f = p.get(k)
                if f and os.path.isfile(f):
                    try:
                        os.remove(f)
                    except OSError:
                        pass
        self.con.execute("DELETE FROM projects WHERE id=?", (pid,))
        self.con.commit()
