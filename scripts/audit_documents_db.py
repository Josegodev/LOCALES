from __future__ import annotations

import sqlite3
from pathlib import Path

from app.config import settings

REQUIRED_TABLES = ["documents", "chunks"]


def _count_rows(conn: sqlite3.Connection, table_name: str) -> int:
    return int(conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])


def audit_documents_db(db_path: str | Path | None = None) -> dict:
    resolved_path = Path(db_path or settings.documents_db_path)
    result = {
        "db_path": str(resolved_path),
        "exists": resolved_path.exists(),
        "readable": False,
        "tables": [],
        "required_tables": list(REQUIRED_TABLES),
        "missing_tables": list(REQUIRED_TABLES),
        "documents_count": 0,
        "chunks_count": 0,
        "status": "error",
        "retrieval_ready": False,
    }

    if not result["exists"]:
        result["status"] = "missing"
        return result

    try:
        conn = sqlite3.connect(resolved_path)
        try:
            result["readable"] = True
            tables = sorted(
                str(row[0])
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                ).fetchall()
            )
            result["tables"] = tables
            result["missing_tables"] = [
                table_name for table_name in REQUIRED_TABLES if table_name not in tables
            ]

            if not result["missing_tables"]:
                result["documents_count"] = _count_rows(conn, "documents")
                result["chunks_count"] = _count_rows(conn, "chunks")
                result["retrieval_ready"] = result["chunks_count"] > 0
                result["status"] = "ok" if result["retrieval_ready"] else "empty"
            else:
                result["status"] = "invalid_schema"
        finally:
            conn.close()
    except sqlite3.Error as exc:
        result["status"] = "unreadable"
        result["error"] = str(exc)

    return result


if __name__ == "__main__":
    import json

    print(json.dumps(audit_documents_db(), ensure_ascii=False, indent=2))
