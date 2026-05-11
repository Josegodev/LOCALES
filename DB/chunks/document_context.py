from __future__ import annotations

import re
import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "documents.sqlite"
UNKNOWN_CORPUS = "unknown"
UNKNOWN_SOURCE_TYPE = "unknown"
OFFICIAL_CORPUS = "documentos_oficiales"
NUCLEO_CORPUS = "nucleo"
OFFICIAL_SOURCE_TYPE = "pdf"
NUCLEO_SOURCE_TYPE = "markdown"
OFFICIAL_TERMS = (
    "paper",
    "pdf",
    "artículo",
    "articulo",
    "documento oficial",
)
NUCLEO_TERMS = (
    "nucleo",
    "runtime",
    "orquestador",
    "agentruntime",
    "telegram",
    "repo",
)
DOMAIN_QUERY_EXPANSIONS = {
    "atencion": [
        "attention",
        "self-attention",
        "multi-head attention",
        "scaled dot-product attention",
    ],
    "atención": [
        "attention",
        "self-attention",
        "multi-head attention",
        "scaled dot-product attention",
    ],
    "mecanismo": [
        "mechanism",
        "attention mechanism",
        "function",
    ],
    "transformer": [
        "transformer",
        "attention is all you need",
    ],
    "transformers": [
        "transformer",
        "attention is all you need",
    ],
    "secuencia": [
        "sequence",
    ],
    "traduccion": [
        "translation",
    ],
    "traducción": [
        "translation",
    ],
}


def normalize_query(query: str) -> str:
    cleaned = (
        query.casefold()
        .replace(",", " ")
        .replace(".", " ")
        .replace("¿", " ")
        .replace("?", " ")
        .replace(":", " ")
        .replace(";", " ")
        .replace('"', " ")
        .replace("'", " ")
    )
    return " ".join(cleaned.split())


def normalize_terms(query: str) -> list[str]:
    cleaned = normalize_query(query)
    return [
        term.strip()
        for term in cleaned.split()
        if len(term.strip()) >= 4
    ]


def extract_quoted_terms(query: str) -> list[str]:
    matches = re.findall(r'"([^"]+)"|\'([^\']+)\'', query)
    quoted_terms: list[str] = []

    for double_quoted, single_quoted in matches:
        raw_term = double_quoted or single_quoted
        normalized_term = " ".join(raw_term.casefold().split())
        if normalized_term and normalized_term not in quoted_terms:
            quoted_terms.append(normalized_term)

    return quoted_terms


def expand_query_terms(query_terms: list[str]) -> list[str]:
    expanded_terms: list[str] = []

    for term in query_terms:
        for expanded_term in DOMAIN_QUERY_EXPANSIONS.get(term, []):
            normalized_term = " ".join(expanded_term.casefold().split())
            if normalized_term and normalized_term not in expanded_terms:
                expanded_terms.append(normalized_term)

    return expanded_terms


def normalize_source_filenames(values: list[str] | None) -> list[str]:
    if not values:
        return []

    normalized: list[str] = []
    for item in values:
        filename = Path(item.strip()).name
        if filename and filename not in normalized:
            normalized.append(filename)
    return normalized


def classify_document_metadata(
    *,
    filename: str,
    source_path: str,
) -> tuple[str, str, int]:
    filename_casefold = filename.casefold()
    source_path_casefold = source_path.casefold()

    if filename_casefold.endswith(".pdf") or "/pdf/" in source_path_casefold:
        return OFFICIAL_CORPUS, OFFICIAL_SOURCE_TYPE, 100

    if (
        filename_casefold.endswith(".md")
        or "/nucleo/" in source_path_casefold
        or "/docs/" in source_path_casefold
    ):
        return NUCLEO_CORPUS, NUCLEO_SOURCE_TYPE, 50

    return UNKNOWN_CORPUS, UNKNOWN_SOURCE_TYPE, 0


def ensure_documents_metadata_schema(conn: sqlite3.Connection) -> None:
    columns = {
        row[1]
        for row in conn.execute("PRAGMA table_info(documents)").fetchall()
    }

    if "corpus" not in columns:
        conn.execute(
            "ALTER TABLE documents ADD COLUMN corpus TEXT DEFAULT 'unknown'"
        )
    if "source_type" not in columns:
        conn.execute(
            "ALTER TABLE documents ADD COLUMN source_type TEXT DEFAULT 'unknown'"
        )
    if "priority" not in columns:
        conn.execute(
            "ALTER TABLE documents ADD COLUMN priority INTEGER DEFAULT 0"
        )

    rows = conn.execute(
        """
        SELECT id, filename, source_path, corpus, source_type, priority
        FROM documents
        ORDER BY id
        """
    ).fetchall()

    updates: list[tuple[str, str, int, int]] = []
    for row in rows:
        document_id = int(row[0])
        filename = str(row[1])
        source_path = str(row[2])
        corpus, source_type, priority = classify_document_metadata(
            filename=filename,
            source_path=source_path,
        )

        if (
            str(row[3] or UNKNOWN_CORPUS) != corpus
            or str(row[4] or UNKNOWN_SOURCE_TYPE) != source_type
            or int(row[5] or 0) != priority
        ):
            updates.append((corpus, source_type, priority, document_id))

    if updates:
        conn.executemany(
            """
            UPDATE documents
            SET corpus = ?, source_type = ?, priority = ?
            WHERE id = ?
            """,
            updates,
        )

    conn.commit()


def detect_source_intent(query: str) -> str:
    normalized_query = query.casefold()
    quoted_terms = extract_quoted_terms(query)
    official_match = any(term in normalized_query for term in OFFICIAL_TERMS)
    nucleo_match = any(term in normalized_query for term in NUCLEO_TERMS)

    if not official_match and "documento" in normalized_query and quoted_terms:
        official_match = True

    if official_match and not nucleo_match:
        return "official_docs"
    if nucleo_match and not official_match:
        return "nucleo"
    return "mixed"


def select_corpus_from_intent(source_intent: str) -> str:
    if source_intent == "official_docs":
        return OFFICIAL_CORPUS
    if source_intent == "nucleo":
        return NUCLEO_CORPUS
    return "mixed"


def _unique_filenames(rows: list[dict]) -> list[str]:
    filenames: list[str] = []
    for row in rows:
        filename = row.get("filename")
        if isinstance(filename, str) and filename not in filenames:
            filenames.append(filename)
    return filenames


def _collect_trace(
    *,
    query_original: str,
    query_normalized: str,
    query_terms: list[str],
    quoted_terms: list[str],
    source_intent: str,
    selected_corpus: str,
    retrieval_status: str,
    candidate_chunks: list[dict],
    selected_chunks: list[dict],
    active_document_id: int | None = None,
    active_document_title: str | None = None,
    active_context_used: bool = False,
    active_context_reason: str | None = None,
    query_expansion_used: bool = False,
    query_expansion_reason: str | None = None,
    expanded_query_terms: list[str] | None = None,
) -> dict:
    chunk_ids: list[int] = []
    document_ids: list[int] = []
    seen_document_ids: set[int] = set()
    scores: list[int] = []

    for chunk in selected_chunks:
        chunk_id = chunk.get("id")
        if isinstance(chunk_id, int):
            chunk_ids.append(chunk_id)

        document_id = chunk.get("document_id")
        if isinstance(document_id, int) and document_id not in seen_document_ids:
            document_ids.append(document_id)
            seen_document_ids.add(document_id)

        score = chunk.get("score")
        if isinstance(score, int):
            scores.append(score)

    selected_filenames = _unique_filenames(selected_chunks)
    candidate_filenames = _unique_filenames(candidate_chunks)

    return {
        "query_original": query_original,
        "query_normalized": query_normalized,
        "query_terms": query_terms,
        "quoted_terms": quoted_terms,
        "source_intent": source_intent,
        "selected_corpus": selected_corpus,
        "active_document_id": active_document_id,
        "active_document_title": active_document_title,
        "active_context_used": active_context_used,
        "active_context_reason": active_context_reason,
        "query_expansion_used": query_expansion_used,
        "query_expansion_reason": query_expansion_reason,
        "expanded_query_terms": list(expanded_query_terms or []),
        "candidate_filenames": candidate_filenames,
        "selected_filenames": selected_filenames,
        "retrieval_status": retrieval_status,
        "chunk_ids": chunk_ids,
        "document_ids": document_ids,
        "source_filenames": selected_filenames,
        "scores": scores,
    }


def _filter_rows_for_active_document(
    rows: list[sqlite3.Row],
    *,
    active_document_id: int | None,
    active_document_title: str | None,
) -> list[sqlite3.Row]:
    if active_document_id is None and not active_document_title:
        return []

    normalized_title = Path(active_document_title).name.casefold() if active_document_title else None
    filtered: list[sqlite3.Row] = []

    for row in rows:
        row_document_id = row["document_id"]
        row_filename = str(row["filename"]).casefold()
        if active_document_id is not None and row_document_id == active_document_id:
            filtered.append(row)
            continue
        if normalized_title and row_filename == normalized_title:
            filtered.append(row)

    return filtered


def _active_document_context_chunks(
    *,
    rows: list[sqlite3.Row],
    limit: int,
) -> list[dict]:
    ranked: list[dict] = []

    for row in sorted(rows, key=lambda item: int(item["chunk_index"])):
        item = dict(row)
        item["quoted_matches"] = []
        item["matched_terms"] = []
        item["score"] = int(item.get("priority") or 0) + max(0, 200 - int(item["chunk_index"]))
        ranked.append(item)

    return ranked[:limit]


def _rank_rows(
    *,
    rows: list[sqlite3.Row],
    query_terms: list[str],
    expanded_query_terms: list[str],
    quoted_terms: list[str],
    allowed_filenames: set[str],
    source_intent: str,
) -> list[dict]:
    ranked: list[dict] = []

    for row in rows:
        item = dict(row)
        if allowed_filenames and str(item["filename"]).casefold() not in allowed_filenames:
            continue
        if source_intent == "official_docs":
            if item.get("corpus") != OFFICIAL_CORPUS and item.get("source_type") != OFFICIAL_SOURCE_TYPE:
                continue
        elif source_intent == "nucleo":
            if item.get("corpus") != NUCLEO_CORPUS:
                continue

        text_casefold = str(item["text"]).casefold()
        quoted_matches = [term for term in quoted_terms if term in text_casefold]
        term_matches = [term for term in query_terms if term in text_casefold]
        expanded_matches = [term for term in expanded_query_terms if term in text_casefold]

        if not quoted_matches and not term_matches and not expanded_matches:
            continue

        quoted_score = sum(max(len(term), 1) * 40 for term in quoted_matches)
        term_score = sum(max(len(term) - 3, 1) for term in term_matches)
        expanded_score = sum(max(len(term) - 3, 1) * 3 for term in expanded_matches)
        corpus_boost = 0
        source_type_boost = 0

        if source_intent == "official_docs":
            if item.get("corpus") == OFFICIAL_CORPUS:
                corpus_boost += 500
            if item.get("source_type") == OFFICIAL_SOURCE_TYPE:
                source_type_boost += 150
        elif source_intent == "nucleo":
            if item.get("corpus") == NUCLEO_CORPUS:
                corpus_boost += 160
            if item.get("source_type") == NUCLEO_SOURCE_TYPE:
                source_type_boost += 40

        priority = int(item.get("priority") or 0)
        score = quoted_score + term_score + expanded_score + corpus_boost + source_type_boost + priority

        item["score"] = score
        item["quoted_matches"] = quoted_matches
        item["matched_terms"] = term_matches
        item["expanded_matches"] = expanded_matches
        ranked.append(item)

    ranked.sort(
        key=lambda item: (
            item["score"],
            len(item.get("quoted_matches", [])),
            len(item.get("matched_terms", [])),
            len(item.get("expanded_matches", [])),
            int(item.get("priority") or 0),
            -item["chunk_index"],
        ),
        reverse=True,
    )

    return ranked


def search_chunks_with_trace(
    query: str,
    limit: int = 5,
    allowed_source_filenames: list[str] | None = None,
    active_document_id: int | None = None,
    active_document_title: str | None = None,
    allow_active_document_fallback: bool = False,
    active_context_reason: str | None = None,
) -> tuple[list[dict], dict]:
    query_original = query
    query_normalized = normalize_query(query)
    query_terms = normalize_terms(query)
    quoted_terms = extract_quoted_terms(query)
    expanded_query_terms = expand_query_terms(query_terms)
    query_expansion_used = bool(expanded_query_terms)
    query_expansion_reason = "domain_dictionary" if expanded_query_terms else None
    source_intent = detect_source_intent(query)
    selected_corpus = select_corpus_from_intent(source_intent)

    allowed_filenames = {
        filename.casefold()
        for filename in normalize_source_filenames(allowed_source_filenames)
    }

    if not query_terms and not quoted_terms:
        return [], _collect_trace(
            query_original=query_original,
            query_normalized=query_normalized,
            query_terms=query_terms,
            quoted_terms=quoted_terms,
            source_intent=source_intent,
            selected_corpus=selected_corpus,
            retrieval_status="NO_EVIDENCE",
            candidate_chunks=[],
            selected_chunks=[],
            active_document_id=active_document_id,
            active_document_title=active_document_title,
            active_context_used=False,
            active_context_reason=active_context_reason,
            query_expansion_used=query_expansion_used,
            query_expansion_reason=query_expansion_reason,
            expanded_query_terms=expanded_query_terms,
        )

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        ensure_documents_metadata_schema(conn)

        rows = conn.execute(
            """
            SELECT
                chunks.id,
                documents.id AS document_id,
                documents.filename,
                documents.source_path,
                documents.corpus,
                documents.source_type,
                documents.priority,
                chunks.chunk_index,
                chunks.char_count,
                chunks.text
            FROM chunks
            JOIN documents ON documents.id = chunks.document_id
            """
        ).fetchall()

        non_quoted_query_terms = [
            term for term in query_terms
            if term not in quoted_terms
        ]
        active_context_used = False
        candidate_chunks: list[dict] = []
        top_chunks: list[dict] = []

        active_rows = _filter_rows_for_active_document(
            rows,
            active_document_id=active_document_id,
            active_document_title=active_document_title,
        )
        if allow_active_document_fallback and active_rows:
            active_context_used = True
            ranked_active = _rank_rows(
                rows=active_rows,
                query_terms=non_quoted_query_terms,
                expanded_query_terms=expanded_query_terms,
                quoted_terms=quoted_terms,
                allowed_filenames=allowed_filenames,
                source_intent=source_intent,
            )
            if ranked_active:
                candidate_chunks = ranked_active
                top_chunks = ranked_active[:limit]
                active_context_used = True
            else:
                candidate_chunks = _active_document_context_chunks(
                    rows=active_rows,
                    limit=limit,
                )
                top_chunks = candidate_chunks[:limit]
        else:
            candidate_chunks = _rank_rows(
                rows=rows,
                query_terms=non_quoted_query_terms,
                expanded_query_terms=expanded_query_terms,
                quoted_terms=quoted_terms,
                allowed_filenames=allowed_filenames,
                source_intent=source_intent,
            )
            top_chunks = candidate_chunks[:limit]

        retrieval_status = "EVIDENCE_FOUND" if top_chunks else "NO_EVIDENCE"
        trace_selected_corpus = selected_corpus
        if top_chunks and isinstance(top_chunks[0].get("corpus"), str):
            trace_selected_corpus = str(top_chunks[0]["corpus"])
        elif candidate_chunks and isinstance(candidate_chunks[0].get("corpus"), str):
            trace_selected_corpus = str(candidate_chunks[0]["corpus"])

        return top_chunks, _collect_trace(
            query_original=query_original,
            query_normalized=query_normalized,
            query_terms=query_terms,
            quoted_terms=quoted_terms,
            source_intent=source_intent,
            selected_corpus=trace_selected_corpus,
            retrieval_status=retrieval_status,
            candidate_chunks=candidate_chunks,
            selected_chunks=top_chunks,
            active_document_id=active_document_id,
            active_document_title=active_document_title,
            active_context_used=active_context_used,
            active_context_reason=active_context_reason,
            query_expansion_used=query_expansion_used,
            query_expansion_reason=query_expansion_reason,
            expanded_query_terms=expanded_query_terms,
        )

    finally:
        conn.close()


def search_chunks(
    query: str,
    limit: int = 5,
    allowed_source_filenames: list[str] | None = None,
    active_document_id: int | None = None,
    active_document_title: str | None = None,
    allow_active_document_fallback: bool = False,
    active_context_reason: str | None = None,
) -> list[dict]:
    chunks, _ = search_chunks_with_trace(
        query=query,
        limit=limit,
        allowed_source_filenames=allowed_source_filenames,
        active_document_id=active_document_id,
        active_document_title=active_document_title,
        allow_active_document_fallback=allow_active_document_fallback,
        active_context_reason=active_context_reason,
    )
    return chunks


def build_document_prompt(
    query: str,
    limit: int = 5,
    allowed_source_filenames: list[str] | None = None,
    active_document_id: int | None = None,
    active_document_title: str | None = None,
    allow_active_document_fallback: bool = False,
    active_context_reason: str | None = None,
) -> dict:
    chunks, trace = search_chunks_with_trace(
        query=query,
        limit=limit,
        allowed_source_filenames=allowed_source_filenames,
        active_document_id=active_document_id,
        active_document_title=active_document_title,
        allow_active_document_fallback=allow_active_document_fallback,
        active_context_reason=active_context_reason,
    )

    if not chunks:
        return {
            "status": "NO_EVIDENCE",
            "retrieval_status": "NO_EVIDENCE",
            "prompt": (
                "No hay evidencia documental suficiente para responder.\n\n"
                f"PREGUNTA:\n{query}\n\n"
                "Responde exactamente: NO_EVIDENCE_FOR_ANSWER"
            ),
            "chunks": [],
            **trace,
        }

    evidence_blocks = []

    for chunk in chunks:
        evidence_blocks.append(
            "\n".join(
                [
                    f"[chunk_id={chunk['id']}]",
                    f"document={chunk['filename']}",
                    f"corpus={chunk.get('corpus', UNKNOWN_CORPUS)}",
                    f"source_type={chunk.get('source_type', UNKNOWN_SOURCE_TYPE)}",
                    f"chunk_index={chunk['chunk_index']}",
                    f"score={chunk.get('score', 0)}",
                    "text:",
                    chunk["text"],
                ]
            )
        )

    evidence = "\n\n---\n\n".join(evidence_blocks)

    prompt = f"""
Responde usando solo la evidencia documental proporcionada.

REGLAS:
- No inventes información que no esté en la evidencia.
- Si la evidencia no contiene la respuesta, responde exactamente NO_EVIDENCE_FOR_ANSWER.
- No trates la evidencia como memoria permanente.


EVIDENCIA:
{evidence}

PREGUNTA:
{query}
""".strip()

    return {
        "status": "EVIDENCE_FOUND",
        "retrieval_status": "EVIDENCE_FOUND",
        "prompt": prompt,
        "chunks": chunks,
        **trace,
    }
