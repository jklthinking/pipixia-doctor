#!/usr/bin/env python3
"""Expose Pipixia Doctor history as mem0-style memory payload."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pipixia_history_store import latest_runs


def collect_mem0_records(limit: int = 20, db_path: str = "~/.pipixia_doctor_cache/doctor_runs.sqlite") -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in latest_runs(limit=limit, db_path=db_path):
        metadata = {
            "checked_at": item["checked_at"],
            "total_checks": item["total_checks"],
            "failed": item["failed"],
            "summary": item["summary"],
            "source": "pipixia-doctor",
        }
        records.append(
            {
                "memory_id": item["run_id"],
                "text": item["summary"],
                "metadata": metadata,
                "is_deleted": False,
            }
        )
    return records


def collect_export(root: Path, limit: int, db_path: str) -> dict[str, Any]:
    return {
        "version": "1",
        "memory": collect_mem0_records(limit=limit, db_path=db_path),
        "provider": "pipixia-doctor",
        "root": str(root),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pipixia Doctor mem0 bridge exporter")
    parser.add_argument("--target", default=".", help="Repository root path")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--db-path", default="~/.pipixia_doctor_cache/doctor_runs.sqlite")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.target).expanduser().resolve()
    payload = collect_export(root, args.limit, args.db_path)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"pipixia-doctor mem0 桥接条目数: {len(payload['memory'])}")
        for row in payload["memory"]:
            print(f"- {row['memory_id']} | {row['metadata']['checked_at']} | {row['text']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
