"""Persist lightweight status history for Pipixia Doctor API runs."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

DB_DEFAULT = Path("~/.pipixia_doctor_cache/doctor_runs.sqlite").expanduser()


def _connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    db_path = Path(db_path or DB_DEFAULT)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path.as_posix())
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            checked_at TEXT NOT NULL,
            passed INTEGER NOT NULL,
            total_checks INTEGER NOT NULL,
            failed INTEGER NOT NULL,
            summary TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def store_run(run_id: str, checks: list[dict[str, Any]], passed: bool, db_path: str | Path | None = None) -> tuple[str, int, int]:
    total = len(checks)
    failed = len([item for item in checks if item.get("level") in {"fail", "warn"}])
    summary = (", ".join(item.get("title") for item in checks if item.get("level") in {"fail", "warn"}) or "all_clear")[:220]
    checked_at = datetime.utcnow().isoformat() + "Z"

    conn = _connect(db_path)
    conn.execute(
        "INSERT OR REPLACE INTO runs (run_id, checked_at, passed, total_checks, failed, summary) VALUES (?, ?, ?, ?, ?, ?)",
        (run_id, checked_at, 1 if passed else 0, total, failed, summary),
    )
    conn.commit()
    conn.close()
    return run_id, total, failed


def latest_runs(limit: int = 10, db_path: str | Path | None = None) -> list[dict[str, Any]]:
    conn = _connect(db_path)
    rows = conn.execute(
        "SELECT run_id, checked_at, passed, total_checks, failed, summary FROM runs ORDER BY checked_at DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
