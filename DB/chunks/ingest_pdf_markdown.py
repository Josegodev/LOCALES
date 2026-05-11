from __future__ import annotations

import argparse
import hashlib
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

import pymupdf4llm

try:
    from .document_context import classify_document_metadata, ensure_documents_metadata_schema
except ImportError:
    from document_context import classify_document_metadata, ensure_documents_metadata_schema


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_PDF_DIR = BASE_DIR / "pdf"
DB_PATH = BASE_DIR / "documents.sqlite"


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
        created_at TEXT NOT NULL,
        corpus TEXT DEFAULT 'unknown',
        source_type TEXT DEFAULT 'unknown',
        priority INTEGER DEFAULT 0
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

    ensure_documents_metadata_schema(conn)
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
    print(f"INGEST_START file={pdf_path}")

    file_hash = sha256_file(pdf_path)
    print(f"INGEST_HASH file={pdf_path.name} sha256={file_hash}")

    markdown = pymupdf4llm.to_markdown(str(pdf_path))

    if not markdown.strip():
        raise RuntimeError("No se pudo extraer texto del PDF. Puede ser escaneado o requerir OCR.")

    chunks = chunk_markdown(markdown)
    print(f"INGEST_EXTRACTED file={pdf_path.name} chunks={len(chunks)}")
    corpus, source_type, priority = classify_document_metadata(
        filename=pdf_path.name,
        source_path=str(pdf_path),
    )

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
                    created_at,
                    corpus,
                    source_type,
                    priority
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pdf_path.name,
                    str(pdf_path),
                    file_hash,
                    markdown,
                    now_iso(),
                    corpus,
                    source_type,
                    priority,
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

        print(f"INGEST_OK file={pdf_path.name} document_id={document_id} chunks={len(chunks)}")

    except sqlite3.IntegrityError as exc:
        raise RuntimeError("Documento ya ingerido. Mismo sha256.") from exc

    finally:
        conn.close()


def resolve_input_path(raw_path: str | None) -> Path:
    if raw_path is None or not raw_path.strip():
        return DEFAULT_PDF_DIR.resolve()

    return Path(raw_path).expanduser().resolve()


def collect_pdf_paths(input_path: Path) -> list[Path]:
    if not input_path.exists():
        raise FileNotFoundError(f"No existe la ruta indicada: {input_path}")

    if input_path.is_file():
        if input_path.suffix.lower() != ".pdf":
            raise ValueError(f"La ruta debe apuntar a un .pdf: {input_path}")
        return [input_path]

    if input_path.is_dir():
        return sorted(
            path.resolve()
            for path in input_path.iterdir()
            if path.is_file() and path.suffix.lower() == ".pdf"
        )

    raise ValueError(f"La ruta no es ni archivo ni directorio: {input_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "input_path",
        nargs="?",
        default=None,
        help="Ruta a un PDF o a un directorio con PDFs. Si se omite, usa DB/chunks/pdf.",
    )
    args = parser.parse_args()

    input_path = resolve_input_path(args.input_path)
    pdf_paths = collect_pdf_paths(input_path)

    print(f"INPUT_PATH: {input_path}")
    print(f"DB_PATH: {DB_PATH}")
    print(f"PDFS_FOUND: {len(pdf_paths)}")

    ok_count = 0
    error_count = 0

    for pdf_path in pdf_paths:
        try:
            ingest_pdf(pdf_path)
            ok_count += 1
        except Exception as exc:
            error_count += 1
            print(
                f"INGEST_ERROR file={pdf_path} type={type(exc).__name__} detail={exc}",
                file=sys.stderr,
            )

    print("INGEST_SUMMARY")
    print(f"PDFs encontrados: {len(pdf_paths)}")
    print(f"PDFs procesados OK: {ok_count}")
    print(f"PDFs con error: {error_count}")

    if error_count > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
