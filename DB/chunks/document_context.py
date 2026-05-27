from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import quote

from app.config import settings
from app.observability.logging import log_event


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "documents.sqlite"
DEFAULT_DB_PATH = DB_PATH
REQUIRED_TABLES = ("documents", "chunks")
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
    "rag",
    "retrieval augmented generation",
    "retrieval-augmented generation",
    "patrick lewis",
    "lewis",
)
NUCLEO_TERMS = (
    "nucleo",
    "runtime",
    "orquestador",
    "agentruntime",
    "telegram",
    "repo",
    "frontend",
    "proyecto",
    "project",
)
REFERENTIAL_TERMS = {
    "ese",
    "esa",
    "eso",
    "esto",
    "esta",
    "este",
    "anterior",
    "anteriormente",
    "previo",
    "previa",
    "misma",
    "mismo",
    "técnica",
    "tecnica",
    "método",
    "metodo",
    "enfoque",
    "rendimiento",
    "that",
    "this",
    "previous",
    "prior",
}
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


@dataclass
class DocumentsDbAudit:
    db_path: str
    exists: bool = False
    readable: bool = False
    size_bytes: int | None = None
    tables: list[str] = field(default_factory=list)
    required_tables: list[str] = field(default_factory=lambda: list(REQUIRED_TABLES))
    missing_tables: list[str] = field(default_factory=list)
    documents_count: int | None = None
    chunks_count: int | None = None
    status: str = "error"
    error: str | None = None

    def as_dict(self) -> dict:
        return {
            "db_path": self.db_path,
            "exists": self.exists,
            "readable": self.readable,
            "size_bytes": self.size_bytes,
            "tables": self.tables,
            "required_tables": self.required_tables,
            "missing_tables": self.missing_tables,
            "documents_count": self.documents_count,
            "chunks_count": self.chunks_count,
            "status": self.status,
        }


def get_documents_db_path() -> str:
    if DB_PATH != DEFAULT_DB_PATH:
        return str(DB_PATH)
    configured_path = str(settings.documents_db_path or "").strip()
    if configured_path:
        return configured_path
    return str(DB_PATH)


def _sqlite_uri_for_readonly(db_path: str) -> str:
    if db_path.startswith("//") or db_path.startswith("\\\\"):
        normalized = db_path.replace("\\", "/")
        return f"file:{quote(normalized, safe='/:')}?mode=ro"
    normalized = str(Path(db_path)).replace("\\", "/")
    return f"file:{quote(normalized, safe='/:')}?mode=ro"


def connect_documents_db_readonly(db_path: str | None = None) -> sqlite3.Connection:
    resolved_path = str(db_path or get_documents_db_path())
    return sqlite3.connect(_sqlite_uri_for_readonly(resolved_path), uri=True)


def audit_documents_db(db_path: str | None = None) -> DocumentsDbAudit:
    resolved_path = str(db_path or get_documents_db_path())
    audit = DocumentsDbAudit(db_path=resolved_path)

    path = Path(resolved_path)
    try:
        audit.exists = path.exists()
        if audit.exists:
            audit.size_bytes = path.stat().st_size
    except OSError as exc:
        audit.status = "unreadable"
        audit.error = str(exc)
        return audit

    if not audit.exists:
        audit.status = "not_found"
        audit.missing_tables = list(REQUIRED_TABLES)
        return audit

    try:
        conn = connect_documents_db_readonly(resolved_path)
    except sqlite3.Error as exc:
        audit.status = "unreadable"
        audit.error = str(exc)
        return audit

    try:
        audit.readable = True
        audit.tables = [
            str(row[0])
            for row in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                ORDER BY name
                """
            ).fetchall()
        ]
        audit.missing_tables = [
            table_name for table_name in REQUIRED_TABLES if table_name not in audit.tables
        ]
        if audit.missing_tables:
            audit.status = "schema_invalid"
            return audit

        audit.documents_count = int(conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0])
        audit.chunks_count = int(conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0])
        if audit.documents_count == 0 and audit.chunks_count == 0:
            audit.status = "empty"
            return audit

        audit.status = "ok"
        return audit
    except sqlite3.Error as exc:
        audit.status = "error"
        audit.error = str(exc)
        return audit
    finally:
        conn.close()


def _warning_code_for_audit(audit: DocumentsDbAudit) -> str:
    if audit.status == "not_found":
        return "RAG_DB_NOT_FOUND"
    if audit.status == "unreadable":
        return "RAG_DB_UNREADABLE"
    if audit.status == "schema_invalid":
        return "RAG_DB_SCHEMA_INVALID"
    if audit.status == "empty":
        return "RAG_DB_EMPTY"
    return "RAG_DB_ERROR"


def _db_not_ready_trace(
    *,
    query_original: str,
    query_normalized: str,
    query_terms: list[str],
    quoted_terms: list[str],
    source_intent: str,
    selected_corpus: str,
    active_document_id: int | None,
    active_document_title: str | None,
    active_context_reason: str | None,
    query_expansion_used: bool,
    query_expansion_reason: str | None,
    expanded_query_terms: list[str],
    audit: DocumentsDbAudit,
    warning_code: str,
) -> dict:
    warning = {
        "code": warning_code,
        "db_path": audit.db_path,
        "existing_tables": audit.tables,
        "missing_tables": audit.missing_tables,
    }
    if audit.error:
        warning["error"] = audit.error

    return {
        **_collect_trace(
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
        ),
        "db_path": audit.db_path,
        "warnings": [warning],
    }


def _log_rag_db_not_ready(
    *,
    audit: DocumentsDbAudit,
    warning_code: str,
    retrieval_status: str = "NO_EVIDENCE_FOR_ANSWER",
) -> None:
    log_event(
        component="rag.db",
        event="rag.db.not_ready",
        db_path=audit.db_path,
        retrieval_status=retrieval_status,
        warning_code=warning_code,
        missing_tables=audit.missing_tables,
        existing_tables=audit.tables,
    )


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


def is_referential_query(query: str) -> bool:
    normalized_query = normalize_query(query)
    if not normalized_query:
        return False

    return any(term in REFERENTIAL_TERMS for term in normalized_query.split())


def source_intent_from_corpus_hint(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None

    normalized_value = normalize_query(value)
    if normalized_value in {
        "official_docs",
        OFFICIAL_CORPUS,
        OFFICIAL_SOURCE_TYPE,
        "paper",
        "papers",
    }:
        return "official_docs"
    if normalized_value in {
        "nucleo",
        NUCLEO_CORPUS,
        NUCLEO_SOURCE_TYPE,
        "project",
        "proyecto",
    }:
        return "nucleo"
    return None


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


def detect_source_intent(
    query: str,
    *,
    active_corpus: str | None = None,
    last_source_intent: str | None = None,
) -> str:
    normalized_query = normalize_query(query)
    quoted_terms = extract_quoted_terms(query)
    official_match = any(term in normalized_query for term in OFFICIAL_TERMS)
    nucleo_match = any(term in normalized_query for term in NUCLEO_TERMS)

    if not official_match and "documento" in normalized_query and quoted_terms:
        official_match = True

    if official_match and not nucleo_match:
        return "official_docs"
    if nucleo_match and not official_match:
        return "nucleo"

    if is_referential_query(query):
        normalized_last_source_intent = normalize_query(last_source_intent or "")
        if normalized_last_source_intent in {"official_docs", "nucleo"}:
            return normalized_last_source_intent

        hinted_intent = source_intent_from_corpus_hint(active_corpus)
        if hinted_intent is not None:
            return hinted_intent

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
        "ranking_scores": scores,
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
    active_corpus: str | None = None,
    last_source_intent: str | None = None,
) -> tuple[list[dict], dict]:
    query_original = query
    query_normalized = normalize_query(query)
    query_terms = normalize_terms(query)
    quoted_terms = extract_quoted_terms(query)
    expanded_query_terms = expand_query_terms(query_terms)
    query_expansion_used = bool(expanded_query_terms)
    query_expansion_reason = "domain_dictionary" if expanded_query_terms else None
    source_intent = detect_source_intent(
        query,
        active_corpus=active_corpus,
        last_source_intent=last_source_intent,
    )
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

    db_path = get_documents_db_path()
    audit = audit_documents_db(db_path)
    if audit.status in {"not_found", "unreadable", "schema_invalid", "empty"}:
        warning_code = _warning_code_for_audit(audit)
        _log_rag_db_not_ready(audit=audit, warning_code=warning_code)
        return [], _db_not_ready_trace(
            query_original=query_original,
            query_normalized=query_normalized,
            query_terms=query_terms,
            quoted_terms=quoted_terms,
            source_intent=source_intent,
            selected_corpus=selected_corpus,
            active_document_id=active_document_id,
            active_document_title=active_document_title,
            active_context_reason=active_context_reason,
            query_expansion_used=query_expansion_used,
            query_expansion_reason=query_expansion_reason,
            expanded_query_terms=expanded_query_terms,
            audit=audit,
            warning_code=warning_code,
        )
    if audit.status != "ok":
        log_event(
            component="rag.db",
            event="rag.db.error",
            db_path=audit.db_path,
            retrieval_status="RAG_ERROR",
            error=audit.error,
        )
        raise sqlite3.OperationalError(audit.error or "documents_db_audit_failed")

    conn = sqlite3.connect(db_path)
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
                candidate_chunks = _rank_rows(
                    rows=rows,
                    query_terms=non_quoted_query_terms,
                    expanded_query_terms=expanded_query_terms,
                    quoted_terms=quoted_terms,
                    allowed_filenames=allowed_filenames,
                    source_intent=source_intent,
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
    active_corpus: str | None = None,
    last_source_intent: str | None = None,
) -> list[dict]:
    chunks, _ = search_chunks_with_trace(
        query=query,
        limit=limit,
        allowed_source_filenames=allowed_source_filenames,
        active_document_id=active_document_id,
        active_document_title=active_document_title,
        allow_active_document_fallback=allow_active_document_fallback,
        active_context_reason=active_context_reason,
        active_corpus=active_corpus,
        last_source_intent=last_source_intent,
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
    active_corpus: str | None = None,
    last_source_intent: str | None = None,
) -> dict:
    chunks, trace = search_chunks_with_trace(
        query=query,
        limit=limit,
        allowed_source_filenames=allowed_source_filenames,
        active_document_id=active_document_id,
        active_document_title=active_document_title,
        allow_active_document_fallback=allow_active_document_fallback,
        active_context_reason=active_context_reason,
        active_corpus=active_corpus,
        last_source_intent=last_source_intent,
    )

    if not chunks:
        trace_warnings = list(trace.get("warnings", []))
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
            "warnings": trace_warnings,
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
