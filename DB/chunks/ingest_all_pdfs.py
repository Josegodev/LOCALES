from __future__ import annotations

import argparse
import sqlite3
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
PDF_DIR = BASE_DIR / "pdf"
DB_PATH = BASE_DIR / "documents.sqlite"
INGEST_SCRIPT = BASE_DIR / "ingest_pdf_markdown.py"


def find_pdfs(pdf_dir: Path) -> list[Path]:
    if not pdf_dir.exists():
        raise FileNotFoundError(f"No existe la carpeta PDF: {pdf_dir}")

    pdfs = sorted(pdf_dir.glob("*.pdf"))

    if not pdfs:
        raise RuntimeError(f"No hay PDFs en: {pdf_dir}")

    return pdfs


def ingest_pdf(pdf_path: Path) -> None:
    print("=" * 80)
    print(f"INGEST: {pdf_path.name}")

    result = subprocess.run(
        [
            sys.executable,
            str(INGEST_SCRIPT),
            str(pdf_path),
        ],
        cwd=str(BASE_DIR),
        text=True,
        capture_output=True,
    )

    if result.stdout:
        print(result.stdout.strip())

    if result.stderr:
        print(result.stderr.strip())

    if result.returncode != 0:
        raise RuntimeError(
            f"Falló ingesta de {pdf_path.name} con código {result.returncode}"
        )


def validate_sqlite() -> None:
    print("=" * 80)
    print("VALIDATE SQLITE")

    if not DB_PATH.exists():
        raise RuntimeError(f"No existe la base SQLite: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)

    try:
        documents_count = conn.execute(
            "SELECT COUNT(*) FROM documents"
        ).fetchone()[0]

        chunks_count = conn.execute(
            "SELECT COUNT(*) FROM chunks"
        ).fetchone()[0]

        print(f"documents: {documents_count}")
        print(f"chunks: {chunks_count}")

        rows = conn.execute(
            """
            SELECT
                documents.id,
                documents.filename,
                length(documents.raw_markdown) AS raw_len,
                COUNT(chunks.id) AS chunk_count
            FROM documents
            LEFT JOIN chunks ON chunks.document_id = documents.id
            GROUP BY documents.id, documents.filename
            ORDER BY documents.id
            """
        ).fetchall()

        for row in rows:
            print(
                f"document_id={row[0]} "
                f"filename={row[1]} "
                f"raw_markdown_len={row[2]} "
                f"chunks={row[3]}"
            )

        if documents_count < 1:
            raise RuntimeError("No hay documentos registrados")

        if chunks_count < 1:
            raise RuntimeError("No hay chunks registrados")

    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pdf-dir",
        default=str(PDF_DIR),
        help="Carpeta donde buscar PDFs",
    )
    args = parser.parse_args()

    pdf_dir = Path(args.pdf_dir).resolve()
    pdfs = find_pdfs(pdf_dir)

    print(f"PDF_DIR: {pdf_dir}")
    print(f"PDFS_FOUND: {len(pdfs)}")

    for pdf in pdfs:
        ingest_pdf(pdf)

    validate_sqlite()

    print("=" * 80)
    print("INGEST_ALL_OK")


if __name__ == "__main__":
    main()
