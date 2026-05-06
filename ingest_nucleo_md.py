from pathlib import Path
import sqlite3
import hashlib
from datetime import datetime


MD_DIR = Path("/home/jose-gonzalez-oliva/NUCLEO/docs")  # AJUSTA
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "DB" / "chunks" / "documents.sqlite"


def utc_now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_text(text: str, max_chars: int = 1800):
    chunks = []
    current = ""

    for paragraph in text.split("\n\n"):
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        if len(current) + len(paragraph) < max_chars:
            current += "\n\n" + paragraph if current else paragraph
        else:
            chunks.append(current)
            current = paragraph

    if current:
        chunks.append(current)

    return chunks


def ingest_file(conn: sqlite3.Connection, path: Path):
    text = path.read_text(encoding="utf-8")
    created_at = utc_now()
    hash_value = sha256(text)

    cur = conn.cursor()

    # Evitar duplicados por hash
    existing = cur.execute(
        "SELECT id FROM documents WHERE sha256 = ?",
        (hash_value,),
    ).fetchone()

    if existing:
        print(f"[SKIP] {path} ya existe")
        return

    cur.execute(
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
            path.name,
            str(path),
            hash_value,
            text,
            created_at,
        ),
    )

    document_id = cur.lastrowid

    for idx, chunk in enumerate(chunk_text(text)):
        cur.execute(
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
                idx,
                chunk,
                len(chunk),
                created_at,
            ),
        )

    print(f"[OK] {path} → doc_id={document_id}")


def main():
    files = sorted(MD_DIR.rglob("*.md"))

    if not files:
        raise RuntimeError(f"No hay .md en {MD_DIR}")

    with sqlite3.connect(DB_PATH) as conn:
        for path in files:
            ingest_file(conn, path)

        conn.commit()


if __name__ == "__main__":
    main()