from __future__ import annotations

import argparse

try:
    from .document_context import search_chunks as canonical_search_chunks
except ImportError:
    from document_context import search_chunks as canonical_search_chunks


def search_chunks(
    query: str,
    limit: int = 5,
    allowed_source_filenames: list[str] | None = None,
) -> list[dict]:
    """Compatibility wrapper over the canonical document retrieval."""
    return canonical_search_chunks(
        query=query,
        limit=limit,
        allowed_source_filenames=allowed_source_filenames,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument(
        "--allowed-source-filename",
        action="append",
        default=[],
        help="Restringe la búsqueda a filenames concretos. Se puede repetir.",
    )
    args = parser.parse_args()

    results = search_chunks(
        query=args.query,
        limit=args.limit,
        allowed_source_filenames=args.allowed_source_filename,
    )

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
