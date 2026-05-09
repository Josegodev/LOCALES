from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from document_context import build_document_prompt
from lmstudio_client import ask_lmstudio


app = FastAPI(title="Local Document RAG API")


class DocumentChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=3, ge=1, le=10)
    allowed_source_filenames: list[str] = Field(default_factory=list)


class RetrievedChunk(BaseModel):
    id: int
    filename: str
    chunk_index: int
    char_count: int
    score: int | None = None


class DocumentChatResponse(BaseModel):
    status: str
    query: str
    chunks: list[RetrievedChunk]
    answer: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/document-chat", response_model=DocumentChatResponse)
def document_chat(request: DocumentChatRequest) -> dict[str, Any]:
    context = build_document_prompt(
        query=request.query,
        limit=request.top_k,
        allowed_source_filenames=request.allowed_source_filenames,
    )

    chunks = [
        {
            "id": chunk["id"],
            "filename": chunk["filename"],
            "chunk_index": chunk["chunk_index"],
            "char_count": chunk["char_count"],
            "score": chunk.get("score"),
        }
        for chunk in context["chunks"]
    ]

    if context["status"] == "NO_EVIDENCE":
        return {
            "status": "no_evidence",
            "query": request.query,
            "chunks": [],
            "answer": "NO_EVIDENCE_FOR_ANSWER",
        }

    answer = ask_lmstudio(context["prompt"])

    return {
        "status": "ok",
        "query": request.query,
        "chunks": chunks,
        "answer": answer,
    }
