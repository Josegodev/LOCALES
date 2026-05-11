from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from DB.chunks.document_context import audit_documents_db


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit the LOCALES documents RAG SQLite DB.")
    parser.add_argument("--db-path", help="Path to documents.sqlite. Defaults to settings.documents_db_path or DB/chunks/documents.sqlite.")
    args = parser.parse_args()

    audit = audit_documents_db(args.db_path)
    payload = audit.as_dict()
    if audit.error:
        payload["error"] = audit.error
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if audit.status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
