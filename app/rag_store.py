from DB.chunks.document_context import search_chunks as canonical_search_chunks


def search_chunks(
    query: str,
    limit: int = 3,
    allowed_source_filenames: list[str] | None = None,
) -> list[dict]:
    """App-facing compatibility wrapper over canonical document retrieval."""
    results = canonical_search_chunks(
        query=query,
        limit=limit,
        allowed_source_filenames=allowed_source_filenames,
    )

    normalized_results: list[dict] = []
    for item in results:
        normalized_item = dict(item)
        filename = normalized_item.get("filename")
        if isinstance(filename, str) and filename.strip():
            normalized_item.setdefault("source", filename)
        normalized_results.append(normalized_item)

    return normalized_results
