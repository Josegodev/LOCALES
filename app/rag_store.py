import logging
import sqlite3
from pathlib import Path


DB_PATH = Path("chunks/document_chunks.sqlite")

logger = logging.getLogger("locales")


def search_chunks(query: str, limit: int = 3) -> list[dict]:
    terms = [t.strip().lower() for t in query.split() if len(t.strip()) > 2]

    if not terms:
        return []

    sql = """
    SELECT id, source, text
    FROM chunks
    WHERE lower(text) LIKE ?
    LIMIT ?
    """

    results = []

    try:
        conn = sqlite3.connect(DB_PATH)
    except sqlite3.Error as exc:
        logger.warning("rag_store.search_chunks: cannot open DB %s: %s", DB_PATH, exc)
        return []

    try:
        conn.row_factory = sqlite3.Row

        for term in terms:
            rows = conn.execute(sql, (f"%{term}%", limit)).fetchall()

            for row in rows:
                item = dict(row)
                item["score"] = sum(
                    1 for t in terms if t in item["text"].lower()
                )
                results.append(item)
    except sqlite3.Error as exc:
        logger.warning("rag_store.search_chunks: query failed: %s", exc)
        return []
    finally:
        conn.close()

    dedup = {}
    for item in results:
        dedup[item["id"]] = item

    ranked = sorted(
        dedup.values(),
        key=lambda x: x["score"],
        reverse=True,
    )

    return ranked[:limit]