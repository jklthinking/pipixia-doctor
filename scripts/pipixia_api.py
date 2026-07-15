"""Optional FastAPI service for Pipixia Doctor.

功能仅用于融合增强，不影响既有 CLI 路径。
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from hashlib import sha1

from pipixia_history_store import latest_runs, store_run

try:
    from fastapi import FastAPI
except Exception:
    FastAPI = None  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = os.getenv("PIPIXIA_DOCTOR_HISTORY_DB", "~/.pipixia_doctor_cache/doctor_runs.sqlite")


def _run_doctor_check() -> tuple[bool, list[dict], str]:
    cp = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "doctor.py"), "check", "--target", str(ROOT), "--format", "json"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    try:
        data = json.loads(cp.stdout)
    except Exception:
        data = {}
    if cp.returncode != 0:
        data = {"level": "fail", "title": "doctor check", "evidence": cp.stderr.strip() or cp.stdout.strip()}
        return False, [data], cp.stderr or cp.stdout
    findings = data.get("findings") if isinstance(data, dict) else []
    return len([item for item in findings if isinstance(item, dict) and item.get("level") == "fail"]) == 0, findings or [], cp.stdout


def create_app() -> "FastAPI":
    if FastAPI is None:
        raise RuntimeError("请先安装 fastapi 与 uvicorn（pip install fastapi uvicorn）")

    app = FastAPI(title="pipixia-doctor api", version="5.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "pipixia-doctor"}

    @app.post("/diag/run")
    def diag_run() -> dict[str, object]:
        passed, findings, raw = _run_doctor_check()
        run_id = sha1((str(ROOT) + raw).encode()).hexdigest()[:16]
        store_run(run_id=run_id, checks=findings if isinstance(findings, list) else [], passed=passed, db_path=DB_PATH)
        return {
            "run_id": run_id,
            "passed": passed,
            "findings_count": len(findings) if isinstance(findings, list) else 0,
            "findings": findings,
            "raw": raw[-1000:],
        }

    @app.get("/diag/latest")
    def diag_latest(limit: int = 10):
        return latest_runs(limit=limit, db_path=DB_PATH)

    return app


def main() -> int:
    if FastAPI is None:
        raise RuntimeError("请先安装 fastapi 与 uvicorn（pip install fastapi uvicorn）")

    parser = argparse.ArgumentParser(description="pipixia-doctor API")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8750)
    args = parser.parse_args()

    import uvicorn

    uvicorn.run(create_app(), host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
