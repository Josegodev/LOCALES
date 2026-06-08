import sqlite3
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from db_store import (
    approve_memory,
    create_model_profile,
    ensure_profile_exists,
    enforce_memory_limit,
    get_memory_context,
    list_model_profiles,
    memory_stats,
    prune_raw,
    raw_stats,
    save_exchange,
)

from lmstudio_client import (
    extract_message_content,
    load_config,
    send_chat_completion,
)
from message_builder import build_messages, build_payload
from defaults import DEFAULT_SYSTEM_PROMPT


app = FastAPI(
    title="LOCALES LLM DB API",
    description=(
        "API local para LM Studio + SQLite. "
        "Separa raw prompts, raw outputs y memoria aprobada por perfil."
    ),
    version="0.1.0",
)


class CreateProfileRequest(BaseModel):
    slug: str = Field(..., min_length=1)
    model_name: str = Field(..., min_length=1)

    temperature: float = 0.2
    top_p: float | None = None
    max_tokens: int | None = None

    system_prompt: str = DEFAULT_SYSTEM_PROMPT

    raw_retention_days: int = 14
    raw_max_rows: int = 500
    raw_max_mb: int = 200
    memory_max_items: int = 200


class ChatRequest(BaseModel):
    slug: str = Field(..., min_length=1)
    prompt: str = Field(..., min_length=1)
    memory_limit: int | None = None


class ApproveMemoryRequest(BaseModel):
    output_id: int
    saved_text: str = Field(..., min_length=1)
    reason: str | None = None


@app.get("/health")
def health() -> dict[str, Any]:
    config = load_config()

    return {
        "status": "ok",
        "lmstudio_base_url": config.get("lmstudio_base_url"),
    }


@app.get("/profiles")
def get_profiles() -> dict[str, Any]:
    return {
        "profiles": list_model_profiles(active_only=False),
    }


@app.post("/profiles")
def create_profile(request: CreateProfileRequest) -> dict[str, Any]:
    parameters: dict[str, Any] = {
        "temperature": request.temperature,
        "stream": False,
    }

    if request.top_p is not None:
        parameters["top_p"] = request.top_p

    if request.max_tokens is not None:
        parameters["max_tokens"] = request.max_tokens

    try:
        profile_id = create_model_profile(
            slug=request.slug,
            runtime="lmstudio",
            model_name=request.model_name,
            parameters=parameters,
            system_prompt=request.system_prompt,
            raw_retention_days=request.raw_retention_days,
            raw_max_rows=request.raw_max_rows,
            raw_max_mb=request.raw_max_mb,
            memory_max_items=request.memory_max_items,
        )

    except sqlite3.IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail=f"El perfil ya existe: {request.slug}",
        ) from exc

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "profile_id": profile_id,
        "slug": request.slug,
    }


@app.get("/profiles/{slug}")
def get_profile(slug: str) -> dict[str, Any]:
    try:
        return ensure_profile_exists(slug)

    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/profiles/{slug}/stats")
def get_profile_stats(slug: str) -> dict[str, Any]:
    try:
        return {
            "raw": raw_stats(slug),
            "memory": memory_stats(slug),
        }

    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/profiles/{slug}/memory")
def get_profile_memory(
    slug: str,
    limit: int = Query(default=20, ge=1, le=500),
) -> dict[str, Any]:
    try:
        memory = get_memory_context(slug=slug, limit=limit)

    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "slug": slug,
        "items": memory,
        "count": len(memory),
    }


@app.post("/profiles/{slug}/memory/approve")
def approve_profile_memory(
    slug: str,
    request: ApproveMemoryRequest,
) -> dict[str, Any]:
    try:
        memory_id = approve_memory(
            slug=slug,
            output_id=request.output_id,
            saved_text=request.saved_text,
            reason=request.reason,
        )

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {
        "memory_id": memory_id,
        "slug": slug,
        "output_id": request.output_id,
    }


@app.post("/chat")
def chat(request: ChatRequest) -> dict[str, Any]:
    prompt = request.prompt.strip()

    if not prompt:
        raise HTTPException(status_code=400, detail="prompt vacío")

    try:
        profile = ensure_profile_exists(request.slug)

    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if not profile["active"]:
        raise HTTPException(
            status_code=400,
            detail=f"Perfil inactivo: {request.slug}",
        )

    config = load_config()

    memory_limit = (
        request.memory_limit
        if request.memory_limit is not None
        else int(config.get("default_memory_limit", 20))
    )

    approved_memory = get_memory_context(
        slug=profile["slug"],
        limit=memory_limit,
    )

    messages = build_messages(
        system_prompt=profile["system_prompt"],
        approved_memory=approved_memory,
        user_prompt=prompt,
    )

    payload = build_payload(
        model_name=profile["model_name"],
        parameters=profile["parameters"],
        messages=messages,
    )

    response_json: dict[str, Any] | None = None

    try:
        response_json = send_chat_completion(payload)
        model_output = extract_message_content(response_json)

        ids = save_exchange(
            slug=profile["slug"],
            user_prompt=prompt,
            request_payload=payload,
            model_output=model_output,
            response_payload=response_json,
            status="ok",
            error_text=None,
        )

        return {
            "status": "ok",
            "slug": profile["slug"],
            "prompt_id": ids["prompt_id"],
            "output_id": ids["output_id"],
            "content": model_output,
        }

    except Exception as exc:
        ids = save_exchange(
            slug=profile["slug"],
            user_prompt=prompt,
            request_payload=payload,
            model_output=None,
            response_payload=response_json,
            status="error",
            error_text=str(exc),
        )

        raise HTTPException(
            status_code=502,
            detail={
                "status": "error",
                "slug": profile["slug"],
                "prompt_id": ids["prompt_id"],
                "output_id": ids["output_id"],
                "error": str(exc),
            },
        ) from exc


@app.post("/profiles/{slug}/prune")
def prune_profile(slug: str) -> dict[str, Any]:
    try:
        result = prune_raw(slug)

    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "slug": slug,
        "result": result,
    }


@app.post("/profiles/{slug}/memory/enforce-limit")
def enforce_profile_memory_limit(slug: str) -> dict[str, Any]:
    try:
        deleted = enforce_memory_limit(slug)

    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return {
        "slug": slug,
        "deleted": deleted,
    }
