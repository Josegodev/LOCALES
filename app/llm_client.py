import requests

from app.adapters.openai_client import (
    DEFAULT_OPENAI_MODEL,
    SUPPORTED_MODELS as OPENAI_SUPPORTED_MODELS,
    ask_chat as _ask_openai_chat,
    resolve_model as _resolve_openai_model,
)
from app.adapters.ollama_client import ask_chat as _ask_chat
from app.adapters.ollama_client import list_models as _list_ollama_models
from app.config import settings
from app.llm_errors import LLMClientError as BaseLLMClientError

LLMClientError = BaseLLMClientError
OPENAI_MODEL_PREFIX = "gpt-"
CHAT_SYSTEM_PROMPT = (
    "Te llamas 5060Ti eres el bot del llm lab de Jose Gonzalez Oliva, "
    "tu función es responder a las preguntas de forma clara y concisa. "
    "Si no sabes la respuesta, di que no lo sabes."
)


def _normalize_model_name(model: str | None) -> str | None:
    if not isinstance(model, str):
        return None

    normalized_model = model.strip()
    return normalized_model or None


def _is_openai_model(model: str) -> bool:
    return model.startswith(OPENAI_MODEL_PREFIX) or model in OPENAI_SUPPORTED_MODELS


def _resolve_ollama_model(model: str | None) -> str:
    configured_default_model = settings.effective_ollama_model()
    if model is None:
        selected_model = ""
    else:
        selected_model = model.strip()
    if not selected_model and configured_default_model:
        return configured_default_model
    try:
        available_models = sorted(_list_ollama_models(), key=str.casefold)
    except LLMClientError:
        if selected_model:
            return selected_model
        raise

    if not selected_model:
        if available_models:
            return available_models[0]
        raise LLMClientError(
            "llm_model_not_available",
            "ollama_no_models_available",
        )

    if selected_model in available_models:
        return selected_model

    lowered_model = selected_model.casefold()
    prefix_matches = [
        available_model
        for available_model in available_models
        if available_model.casefold().startswith(lowered_model)
    ]
    if len(prefix_matches) == 1:
        return prefix_matches[0]

    return selected_model


def list_chat_models() -> list[dict[str, object]]:
    items: list[dict[str, object]] = []
    available_ollama_models = sorted(_list_ollama_models(), key=str.casefold)

    for model_name in available_ollama_models:
        items.append(
            {
                "provider": "ollama",
                "model": model_name,
                "label": model_name,
                "is_default": False,
            }
        )

    items.append(
        {
            "provider": "openai",
            "model": DEFAULT_OPENAI_MODEL,
            "label": f"OpenAI / {DEFAULT_OPENAI_MODEL}",
            "is_default": False,
        }
    )
    return items


def resolve_provider_model(
    provider: str | None,
    model: str | None,
) -> tuple[str, str]:
    selected_provider = (provider or "ollama").strip().lower()
    selected_model = _normalize_model_name(model)

    if selected_provider == "ollama":
        if selected_model is not None and _is_openai_model(selected_model):
            raise LLMClientError(
                "invalid_provider_model_pair",
                f"provider_model_pair_invalido: provider={selected_provider}, model={selected_model}",
            )
        return selected_provider, _resolve_ollama_model(selected_model)
    if selected_provider == "openai":
        if selected_model is not None and not _is_openai_model(selected_model):
            raise LLMClientError(
                "invalid_provider_model_pair",
                f"provider_model_pair_invalido: provider={selected_provider}, model={selected_model}",
            )
        selected_model = _resolve_openai_model(selected_model or DEFAULT_OPENAI_MODEL)
        return selected_provider, selected_model

    raise LLMClientError(
        "llm_provider_error",
        f"provider_no_soportado: {provider}",
    )


def ask_chat(
    message: str,
    *,
    provider: str | None = None,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
    use_rag: bool | None = None,
) -> dict:
    selected_provider, selected_model = resolve_provider_model(provider, model)

    if selected_provider == "openai":
        return _ask_openai_chat(
            message,
            model=selected_model,
            max_tokens=max_tokens,
            temperature=temperature,
            use_rag=use_rag,
            system_prompt=CHAT_SYSTEM_PROMPT,
            settings_obj=settings,
        )

    return _ask_chat(
        message,
        model=selected_model,
        temperature=temperature,
        use_rag=use_rag,
        num_predict=max_tokens,
        system_prompt=CHAT_SYSTEM_PROMPT,
        requests_module=requests,
        settings_obj=settings,
    )
