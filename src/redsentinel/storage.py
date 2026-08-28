import json
import sqlite3
from pathlib import Path
from typing import Any


class RunStore:
    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY, created_at TEXT, status TEXT, summary TEXT
                );
                CREATE TABLE IF NOT EXISTS findings (
                    run_id TEXT, case_id TEXT, payload TEXT,
                    PRIMARY KEY(run_id, case_id)
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def save(self, run: dict[str, Any]) -> None:
        with self._connect() as db:
            db.execute("INSERT OR REPLACE INTO runs VALUES (?, ?, ?, ?)", (run["id"], run["created_at"], run["status"], json.dumps(run["summary"])))
            db.executemany("INSERT OR REPLACE INTO findings VALUES (?, ?, ?)", ((run["id"], f["case_id"], json.dumps(f)) for f in run["findings"]))

    def get(self, run_id: str) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
            if not row:
                return None
            findings = [json.loads(r["payload"]) for r in db.execute("SELECT payload FROM findings WHERE run_id=? ORDER BY case_id", (run_id,))]
        return {"id": row["id"], "created_at": row["created_at"], "status": row["status"], "summary": json.loads(row["summary"]), "findings": findings}

    def list(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM runs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [{"id": r["id"], "created_at": r["created_at"], "status": r["status"], "summary": json.loads(r["summary"])} for r in rows]
