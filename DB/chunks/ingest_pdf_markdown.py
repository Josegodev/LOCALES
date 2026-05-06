from __future__ import annotations

import argparse
import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import pymupdf4llm


DB_PATH = "documents.sqlite"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(block)

    return digest.hexdigest()


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        source_path TEXT NOT NULL,
        sha256 TEXT NOT NULL UNIQUE,
        raw_markdown TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        chunk_index INTEGER NOT NULL,
        text TEXT NOT NULL,
        char_count INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (document_id) REFERENCES documents(id)
    )
    """)

    conn.execute("""
    CREATE INDEX IF NOT EXISTS idx_chunks_document_id
    ON chunks(document_id)
    """)

    conn.commit()


def chunk_markdown(
    markdown: str,
    chunk_size: int = 1200,
    overlap: int = 200,
) -> list[str]:
    text = markdown.strip()

    chunks: list[str] = []
    cursor = 0

    while cursor < len(text):
        end = cursor + chunk_size
        chunk = text[cursor:end].strip()

        if chunk:
            chunks.append(chunk)

        cursor = end - overlap

        if cursor < 0:
            cursor = 0

        if cursor >= len(text):
            break

    return chunks


def ingest_pdf(pdf_path: Path) -> None:
    pdf_path = pdf_path.resolve()
    file_hash = sha256_file(pdf_path)

    markdown = pymupdf4llm.to_markdown(str(pdf_path))

    if not markdown.strip():
        raise RuntimeError("No se pudo extraer texto del PDF. Puede ser escaneado o requerir OCR.")

    chunks = chunk_markdown(markdown)

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    try:
        with conn:
            cursor = conn.execute(
                """
                INSERT INTO documents (
                    filename,
                    source_path,
                    sha256,
                    raw_markdown,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    pdf_path.name,
                    str(pdf_path),
                    file_hash,
                    markdown,
                    now_iso(),
                ),
            )

            document_id = cursor.lastrowid

            for index, chunk in enumerate(chunks):
                conn.execute(
                    """
                    INSERT INTO chunks (
                        document_id,
                        chunk_index,
                        text,
                        char_count,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        document_id,
                        index,
                        chunk,
                        len(chunk),
                        now_iso(),
                    ),
                )

        print(f"OK document_id={document_id} chunks={len(chunks)}")

    except sqlite3.IntegrityError:
        print("ERROR: documento ya ingerido. Mismo sha256.")

    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", help="Ruta al PDF")
    args = parser.parse_args()

    ingest_pdf(Path(args.pdf))


if __name__ == "__main__":
    main()
