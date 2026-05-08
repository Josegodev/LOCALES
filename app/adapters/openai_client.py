from __future__ import annotations

import time
from typing import Any

from openai import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    NotFoundError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)

from app.config import settings
from app.llm_errors import LLMClientError

SUPPORTED_MODELS: frozenset[str] = frozenset(
    {
        "gpt-5.5",
        "gpt-5.5-pro",
        "gpt-5.4",
        "gpt-5.4-mini",
        "gpt-5.4-nano",
        "gpt-5",
        "gpt-5-mini",
        "gpt-5-nano",
        "gpt-4.1",
        "gpt-4.1-mini",
        "gpt-4o",
        "gpt-4o-mini",
    }
)
DEFAULT_OPENAI_MODEL = "gpt-5.5"


class OpenAIClientError(LLMClientError):
    pass


def resolve_model(model: str | None) -> str:
    selected_model = (model or DEFAULT_OPENAI_MODEL).strip()
    if selected_model not in SUPPORTED_MODELS:
        raise OpenAIClientError(
            "llm_model_not_available",
            f"OpenAI model no disponible: {selected_model}",
        )
    return selected_model


def _build_client(settings_obj=settings) -> OpenAI:
    api_key = settings_obj.openai_api_key
    if not api_key:
        raise OpenAIClientError("llm_auth_error", "OPENAI_API_KEY no definido")

    return OpenAI(
        api_key=api_key,
        timeout=settings_obj.llm_timeout_seconds,
        max_retries=0,
    )


def _error_from_exception(exc: Exception) -> tuple[str, str]:
    if isinstance(exc, APITimeoutError):
        return "llm_timeout", "OpenAI ha agotado el tiempo de respuesta"
    if isinstance(exc, APIConnectionError):
        return "llm_network_error", "OpenAI no está disponible"
    if isinstance(exc, (AuthenticationError,)):
        return "llm_auth_error", "La API key de OpenAI no es válida"
    if isinstance(exc, (NotFoundError,)):
        return "llm_model_not_available", "OpenAI model no disponible"
    if isinstance(exc, RateLimitError):
        return "llm_rate_limited", "OpenAI devolvió rate limit"

    if isinstance(exc, APIStatusError):
        status_code = getattr(exc, "status_code", None)
        if status_code in {401, 403}:
            return "llm_auth_error", "La API key de OpenAI no es válida"
        if status_code == 404:
            return "llm_model_not_available", "OpenAI model no disponible"
        if status_code == 429:
            return "llm_rate_limited", "OpenAI devolvió rate limit"
        return "llm_provider_error", f"OpenAI devolvió HTTP {status_code}"

    if isinstance(exc, (APIError, OpenAIError)):
        return "llm_provider_error", str(exc) or "openai_provider_error"

    return "llm_provider_error", str(exc) or "openai_provider_error"


def _temperature_rejected(exc: Exception) -> bool:
    text = f"{exc.__class__.__name__}: {exc}".lower()
    return "temperature" in text and any(
        fragment in text
        for fragment in (
            "not supported",
            "unsupported",
            "invalid",
            "unexpected",
            "unknown field",
            "unrecognized",
            "not allowed",
            "not accepted",
            "does not support",
        )
    )


def _response_text(response: Any) -> str:
    text = getattr(response, "output_text", "")
    if not isinstance(text, str):
        return ""
    return " ".join(text.split())


def ask_chat(
    message: str,
    *,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
    use_rag: bool | None = None,
    system_prompt: str | None = None,
    settings_obj=settings,
) -> dict:
    if not isinstance(message, str) or not message.strip():
        raise OpenAIClientError("llm_generation_failed", "message_required")

    selected_model = resolve_model(model)
    selected_temperature = temperature if temperature is not None else settings_obj.temperature
    client = _build_client(settings_obj)

    payload: dict[str, Any] = {
        "model": selected_model,
        "input": message,
        "max_output_tokens": max_tokens if max_tokens is not None else settings_obj.max_tokens,
    }
    if selected_temperature is not None:
        payload["temperature"] = selected_temperature
    if system_prompt and system_prompt.strip():
        payload["instructions"] = system_prompt.strip()

    started_at = time.perf_counter()
    try:
        response = client.responses.create(**payload)
    except Exception as exc:
        if selected_temperature is not None and _temperature_rejected(exc):
            fallback_payload = dict(payload)
            fallback_payload.pop("temperature", None)
            try:
                response = client.responses.create(**fallback_payload)
            except Exception as retry_exc:
                code, message_text = _error_from_exception(retry_exc)
                raise OpenAIClientError(code, message_text) from retry_exc
            temperature_ignored = True
        else:
            code, message_text = _error_from_exception(exc)
            raise OpenAIClientError(code, message_text) from exc
    else:
        temperature_ignored = False

    answer = _response_text(response)
    if not answer:
        raise OpenAIClientError("llm_provider_error", "OpenAI devolvió respuesta vacía")

    latency_ms = int((time.perf_counter() - started_at) * 1000)

    return {
        "status": "ok",
        "provider": "openai",
        "model": selected_model,
        "temperature": selected_temperature,
        "temperature_ignored": temperature_ignored,
        "use_rag": True if use_rag is None else bool(use_rag),
        "answer": answer,
        "latency_ms": latency_ms,
    }
