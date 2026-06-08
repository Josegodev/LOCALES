from __future__ import annotations

import argparse

from document_context import search_chunks


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
