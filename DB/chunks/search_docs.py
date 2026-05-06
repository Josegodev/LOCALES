from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "documents.sqlite"


def search_chunks(query: str, limit: int = 5) -> list[dict]:
    terms = [
        term.strip().lower()
        for term in query.replace(",", " ").replace(".", " ").split()
        if len(term.strip()) >= 4
    ]

    if not terms:
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        rows = conn.execute(
            """
            SELECT
                chunks.id,
                documents.filename,
                chunks.chunk_index,
                chunks.char_count,
                chunks.text
            FROM chunks
            JOIN documents ON documents.id = chunks.document_id
            """
        ).fetchall()

        ranked: list[dict] = []

        for row in rows:
            item = dict(row)
            text_lower = item["text"].lower()

            score = sum(1 for term in terms if term in text_lower)

            if score > 0:
                item["score"] = score
                ranked.append(item)

        ranked.sort(
            key=lambda item: (
                item["score"],
                -item["chunk_index"],
            ),
            reverse=True,
        )

        return ranked[:limit]

    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    results = search_chunks(args.query, args.limit)

    if not results:
        print("NO_RESULTS")
        return

    for result in results:
        print("=" * 80)
        print(
            f"chunk_id={result['id']} "
            f"file={result['filename']} "
            f"chunk_index={result['chunk_index']} "
            f"chars={result['char_count']}"
        )
        print(result["text"][:1200])


if __name__ == "__main__":
    main()
