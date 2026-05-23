from collections.abc import Mapping
from typing import Any

from pydantic import ValidationError

from app.schemas import CreateDocumentRequest
from app.services.document_writer import slugify, write_document


CREATE_DOCUMENT_SYSTEM_PROMPT = """
Eres un generador de documentos Markdown.
Devuelve únicamente el contenido final del documento en Markdown válido.
No expliques el proceso.
No incluyas metacomentarios.
Si falta información, añade una sección llamada 'Información pendiente'.
"""

DEFAULT_DOCUMENT_REQUEST_FILENAME = "documento.md"


def _error_result(error_type: str, error_message: str) -> dict[str, Any]:
    return {
        "status": "error",
        "error_type": error_type,
        "error_message": error_message,
        "tool_called": "create_document",
    }


def _overwrite_metadata(overwrite_requested: bool) -> dict[str, Any]:
    return {
        "overwrite_requested": overwrite_requested,
        "overwrite_applied": False,
        "overwrite_reason": "unique_trace_filename_policy",
    }


def build_create_document_request(
    *,
    request_id: str,
    instruction: str,
    content: str,
    user_id: int | None,
    chat_id: int | None,
    overwrite: bool = False,
) -> CreateDocumentRequest:
    normalized_instruction = instruction.strip() if isinstance(instruction, str) else ""
    safe_filename = f"{slugify(normalized_instruction)}.md" if normalized_instruction else DEFAULT_DOCUMENT_REQUEST_FILENAME
    return CreateDocumentRequest(
        request_id=request_id,
        filename=safe_filename,
        content=content,
        overwrite=overwrite,
        user_id=user_id if isinstance(user_id, int) else 0,
        chat_id=chat_id if isinstance(chat_id, int) else 0,
    )


async def _generate_markdown_content(
    *,
    instruction: str,
    filename: str,
    model_client: Any,
    model: str,
    provider: str,
    temperature: float,
) -> dict[str, Any]:
    prompt = f"""
Instrucción del usuario:

{instruction}

Nombre solicitado del documento: {filename}

Genera el documento en formato Markdown.
"""

    llm_result = await model_client.generate(
        system_prompt=CREATE_DOCUMENT_SYSTEM_PROMPT,
        user_prompt=prompt,
        model=model,
        provider=provider,
        temperature=temperature,
    )
    content = llm_result.get("text") or llm_result.get("response") or ""
    return {
        "content": content,
        "tokens_input": llm_result.get("tokens_input"),
        "tokens_output": llm_result.get("tokens_output"),
        "latency_ms": llm_result.get("latency_ms"),
        "provider": provider,
        "model": model,
        "temperature": temperature,
    }


async def _coerce_request(
    *,
    request: CreateDocumentRequest | Mapping[str, object],
    instruction: str | None,
    model_client: Any,
    model: str | None,
    provider: str | None,
    temperature: float,
) -> tuple[CreateDocumentRequest | None, dict[str, Any]]:
    if isinstance(request, CreateDocumentRequest):
        return request, {
            "generation_used": False,
            "tokens_input": None,
            "tokens_output": None,
            "latency_ms": None,
            "provider": provider,
            "model": model,
            "temperature": temperature,
            "instruction": instruction,
            **_overwrite_metadata(request.overwrite),
        }

    if not isinstance(request, Mapping):
        return None, _error_result(
            "invalid_document_request",
            "La tool requiere un CreateDocumentRequest o un mapping equivalente.",
        )

    raw_request = dict(request)
    raw_content = raw_request.get("content")
    normalized_instruction = instruction.strip() if isinstance(instruction, str) and instruction.strip() else None

    generation_metadata = {
        "generation_used": False,
        "tokens_input": None,
        "tokens_output": None,
        "latency_ms": None,
        "provider": provider,
        "model": model,
        "temperature": temperature,
        "instruction": normalized_instruction,
        **_overwrite_metadata(bool(raw_request.get("overwrite"))),
    }

    if not isinstance(raw_content, str) or not raw_content.strip():
        if not normalized_instruction:
            return None, _error_result(
                "missing_instruction",
                "Falta contenido utilizable y no se proporcionó instrucción de generación.",
            )
        if model_client is None:
            return None, _error_result(
                "model_not_connected",
                "La tool está preparada para generar Markdown, pero todavía no está conectada a un modelo.",
            )
        if not isinstance(model, str) or not model.strip() or not isinstance(provider, str) or not provider.strip():
            return None, _error_result(
                "missing_model_configuration",
                "Falta configuración mínima del modelo para generar el documento Markdown.",
            )

        filename = raw_request.get("filename")
        generated = await _generate_markdown_content(
            instruction=normalized_instruction,
            filename=filename if isinstance(filename, str) else "documento.md",
            model_client=model_client,
            model=model.strip(),
            provider=provider.strip(),
            temperature=temperature,
        )
        raw_request["content"] = generated["content"]
        generation_metadata.update(generated)
        generation_metadata["generation_used"] = True

    try:
        validated_request = CreateDocumentRequest.model_validate(raw_request)
    except ValidationError as exc:
        return None, _error_result(
            "invalid_document_request",
            str(exc),
        )

    return validated_request, generation_metadata


async def create_document_tool(
    *,
    request: CreateDocumentRequest | Mapping[str, object],
    instruction: str | None = None,
    model_client: Any = None,
    model: str | None = None,
    provider: str | None = None,
    temperature: float = 0.2,
) -> dict[str, Any]:
    """Tool reutilizable para documentos Markdown; `overwrite` queda reservado y no se aplica en esta fase."""
    validated_request, metadata = await _coerce_request(
        request=request,
        instruction=instruction,
        model_client=model_client,
        model=model,
        provider=provider,
        temperature=temperature,
    )
    if validated_request is None:
        return metadata

    write_result = write_document(
        content=validated_request.content,
        trace_id=validated_request.request_id,
        filename=validated_request.filename,
        title=validated_request.filename,
    )
    if write_result.get("status") != "ok":
        return {
            **write_result,
            "tool_called": "create_document",
            "request_id": validated_request.request_id,
            "user_id": validated_request.user_id,
            "chat_id": validated_request.chat_id,
            "overwrite_requested": metadata.get("overwrite_requested"),
            "overwrite_applied": metadata.get("overwrite_applied"),
            "overwrite_reason": metadata.get("overwrite_reason"),
        }

    return {
        **write_result,
        "tool_called": "create_document",
        "request_id": validated_request.request_id,
        "filename": validated_request.filename,
        "format": ".md",
        "instruction": metadata.get("instruction"),
        "content_source": "model" if metadata.get("generation_used") else "request",
        "provider": metadata.get("provider"),
        "model": metadata.get("model"),
        "temperature": metadata.get("temperature"),
        "tokens_input": metadata.get("tokens_input"),
        "tokens_output": metadata.get("tokens_output"),
        "latency_ms": metadata.get("latency_ms"),
        "user_id": validated_request.user_id,
        "chat_id": validated_request.chat_id,
        "overwrite_requested": metadata.get("overwrite_requested"),
        "overwrite_applied": metadata.get("overwrite_applied"),
        "overwrite_reason": metadata.get("overwrite_reason"),
    }
