from __future__ import annotations

from app.chat.retrieval import (
    _extract_chunk_response_data as retrieval_extract_chunk_response_data,
)
from app.chat.retrieval import (
    _extract_chunk_source_filename as retrieval_extract_chunk_source_filename,
)
from app.chat.retrieval import (
    _normalize_source_filename as retrieval_normalize_source_filename,
)


def normalize_source_filename(value: object) -> str | None:
    return retrieval_normalize_source_filename(value)


def extract_chunk_source_filename(chunk: dict) -> str | None:
    return retrieval_extract_chunk_source_filename(chunk)


def extract_chunk_response_data(
    chunks: list[dict],
) -> tuple[list[str], list[int], list[int], list[str]]:
    return retrieval_extract_chunk_response_data(chunks)


def evidence_used_from_payload(
    *,
    chunk_ids: list[int] | None,
    document_ids: list[int] | None,
    source_filenames: list[str] | None,
) -> bool:
    return bool(chunk_ids or document_ids or source_filenames)
