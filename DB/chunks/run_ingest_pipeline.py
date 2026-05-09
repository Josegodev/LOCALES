from __future__ import annotations

import argparse
import sqlite3
import subprocess
import sys
from pathlib import Path

from document_context import build_document_prompt
from search_docs import search_chunks


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "documents.sqlite"
DEFAULT_PDF = BASE_DIR / "pdf" / "MEMORIA 27.12.2021.pdf"


def run_ingest(pdf_path: Path) -> None:
    print("== INGEST PDF ==")
    print(f"pdf: {pdf_path}")

    result = subprocess.run(
        [
            sys.executable,
            str(BASE_DIR / "ingest_pdf_markdown.py"),
            str(pdf_path),
        ],
        cwd=str(BASE_DIR),
        text=True,
        capture_output=True,
    )

    print(result.stdout)

    if result.stderr:
        print(result.stderr)

    if result.returncode != 0:
        raise RuntimeError(f"ingest_pdf_markdown.py falló con código {result.returncode}")


def validate_sqlite() -> None:
    print("== VALIDATE SQLITE ==")

    conn = sqlite3.connect(DB_PATH)

    try:
        document_count = conn.execute(
            "SELECT COUNT(*) FROM documents"
        ).fetchone()[0]

        chunk_count = conn.execute(
            "SELECT COUNT(*) FROM chunks"
        ).fetchone()[0]

        docs = conn.execute(
            """
            SELECT id, filename, length(raw_markdown)
            FROM documents
            ORDER BY id
            """
        ).fetchall()

        print(f"documents: {document_count}")
        print(f"chunks: {chunk_count}")

        for doc in docs:
            print(f"document_id={doc[0]} filename={doc[1]} raw_markdown_len={doc[2]}")

        if document_count < 1:
            raise RuntimeError("No hay documentos en SQLite")

        if chunk_count < 1:
            raise RuntimeError("No hay chunks en SQLite")

    finally:
        conn.close()


def validate_search(
    query: str,
    top_k: int,
    allowed_source_filenames: list[str] | None = None,
) -> None:
    print("== VALIDATE SEARCH_DOCS ==")

    results = search_chunks(
        query=query,
        limit=top_k,
        allowed_source_filenames=allowed_source_filenames,
    )

    print(f"query: {query}")
    print(f"results: {len(results)}")

    if not results:
        raise RuntimeError("search_docs.py no recuperó resultados")

    for result in results:
        print(
            f"chunk_id={result['id']} "
            f"chunk_index={result['chunk_index']} "
            f"chars={result['char_count']}"
        )


def validate_document_context(
    query: str,
    top_k: int,
    allowed_source_filenames: list[str] | None = None,
) -> None:
    print("== VALIDATE DOCUMENT_CONTEXT ==")

    context = build_document_prompt(
        query=query,
        limit=top_k,
        allowed_source_filenames=allowed_source_filenames,
    )

    print(f"status: {context['status']}")
    print(f"chunks: {[chunk['id'] for chunk in context['chunks']]}")
    print(f"scores: {[chunk.get('score') for chunk in context['chunks']]}")

    if context["status"] != "EVIDENCE_FOUND":
        raise RuntimeError("document_context.py no generó evidencia")

    print("prompt_preview:")
    print(context["prompt"][:1200])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pdf",
        default=str(DEFAULT_PDF),
        help="Ruta al PDF a ingerir",
    )
    parser.add_argument(
        "--query",
        default="qué estudia la memoria sobre corcho y ASA",
        help="Consulta de validación",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Número de chunks a recuperar",
    )
    parser.add_argument(
        "--allowed-source-filename",
        action="append",
        default=[],
        help="Restringe la validación a filenames concretos. Se puede repetir.",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf).resolve()

    if not pdf_path.exists():
        raise FileNotFoundError(f"No existe el PDF: {pdf_path}")

    run_ingest(pdf_path)
    validate_sqlite()
    validate_search(args.query, args.top_k, args.allowed_source_filename)
    validate_document_context(args.query, args.top_k, args.allowed_source_filename)

    print("== PIPELINE_OK ==")


if __name__ == "__main__":
    main()
