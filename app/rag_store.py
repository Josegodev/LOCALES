import sqlite3
from pathlib import Path


DB_PATH = Path("chunks/document_chunks.sqlite")

_LIKE_ESCAPE_CHAR = "\\"


def _escape_like(term: str) -> str:
    return (
        term
        .replace(_LIKE_ESCAPE_CHAR, _LIKE_ESCAPE_CHAR + _LIKE_ESCAPE_CHAR)
        .replace("%", _LIKE_ESCAPE_CHAR + "%")
        .replace("_", _LIKE_ESCAPE_CHAR + "_")
    )


def search_chunks(query: str, limit: int = 3) -> list[dict]:
    terms = [t.strip().lower() for t in query.split() if len(t.strip()) > 2]

    if not terms:
        return []

    sql = """
    SELECT id, source, text
    FROM chunks
    WHERE lower(text) LIKE ? ESCAPE '\\'
    LIMIT ?
    """

    results = []

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        for term in terms:
            rows = conn.execute(sql, (f"%{_escape_like(term)}%", limit)).fetchall()

            for row in rows:
                item = dict(row)
                item["score"] = sum(
                    1 for t in terms if t in item["text"].lower()
                )
                results.append(item)

    dedup = {}
    for item in results:
        dedup[item["id"]] = item

    ranked = sorted(
        dedup.values(),
        key=lambda x: x["score"],
        reverse=True,
    )

    return ranked[:limit]