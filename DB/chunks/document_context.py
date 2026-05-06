from __future__ import annotations

import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "documents.sqlite"


def normalize_terms(query: str) -> list[str]:
    cleaned = (
        query.lower()
        .replace(",", " ")
        .replace(".", " ")
        .replace("¿", " ")
        .replace("?", " ")
        .replace(":", " ")
        .replace(";", " ")
    )

    return [
        term.strip()
        for term in cleaned.split()
        if len(term.strip()) >= 4
    ]


def search_chunks(query: str, limit: int = 5) -> list[dict]:
    terms = normalize_terms(query)

    if not terms:
        return []

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        rows = conn.execute(
            """
            SELECT
                chunks.id,
                documents.filename,
                chunks.chunk_index,
                chunks.char_count,
                chunks.text
            FROM chunks
            JOIN documents ON documents.id = chunks.document_id
            """
        ).fetchall()

        ranked: list[dict] = []

        for row in rows:
            item = dict(row)
            text_lower = item["text"].lower()

            score = sum(1 for term in terms if term in text_lower)

            if score > 0:
                item["score"] = score
                ranked.append(item)

        ranked.sort(
            key=lambda item: (
                item["score"],
                -item["chunk_index"],
            ),
            reverse=True,
        )

        return ranked[:limit]

    finally:
        conn.close()


def build_document_prompt(query: str, limit: int = 5) -> dict:
    chunks = search_chunks(query=query, limit=limit)

    if not chunks:
        return {
            "status": "NO_EVIDENCE",
            "prompt": (
                "No hay evidencia documental suficiente para responder.\n\n"
                f"PREGUNTA:\n{query}\n\n"
                "Responde exactamente: NO_EVIDENCE_FOR_ANSWER"
            ),
            "chunks": [],
        }

    evidence_blocks = []

    for chunk in chunks:
        evidence_blocks.append(
            "\n".join(
                [
                    f"[chunk_id={chunk['id']}]",
                    f"document={chunk['filename']}",
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
- Si la evidencia no contiene la respuesta, responde exactamente ALGO APROXIMADO.
- No trates la evidencia como memoria permanente.


EVIDENCIA:
{evidence}

PREGUNTA:
{query}
""".strip()

    return {
        "status": "EVIDENCE_FOUND",
        "prompt": prompt,
        "chunks": chunks,
    }
