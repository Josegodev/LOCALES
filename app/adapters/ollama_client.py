import requests

from app.config import settings
from app.llm_errors import LLMClientError


class OllamaClientError(LLMClientError):
    pass


def _api_chat_url(settings_obj=settings) -> str:
    return f"{settings_obj.ollama_api_base_url()}/api/chat"


def _chat_completions_url(settings_obj=settings) -> str:
    return f"{settings_obj.ollama_v1_base_url()}/chat/completions"


def _api_tags_url(settings_obj=settings) -> str:
    return f"{settings_obj.ollama_api_base_url()}/api/tags"


def _selected_model(settings_obj=settings) -> str:
    return settings_obj.effective_ollama_model()


def _timeout_seconds(settings_obj=settings) -> float:
    return settings_obj.effective_ollama_timeout_seconds()


def _error_from_response(response: requests.Response) -> tuple[str, str]:
    try:
        payload = response.json()
    except ValueError:
        return "llm_http_error", f"Ollama devolvio HTTP {response.status_code}"

    raw_error = payload.get("error")
    if isinstance(raw_error, str):
        error_text = raw_error.strip()
        lowered = error_text.lower()
        if "model" in lowered and ("not found" in lowered or "not available" in lowered):
            return "llm_model_not_available", error_text
        return "llm_http_error", error_text

    return "llm_http_error", f"Ollama devolvio HTTP {response.status_code}"


def list_models(
    *,
    requests_module=requests,
    settings_obj=settings,
) -> list[str]:
    try:
        response = requests_module.get(
            _api_tags_url(settings_obj),
            timeout=_timeout_seconds(settings_obj),
        )
    except requests.exceptions.ConnectionError as exc:
        raise OllamaClientError("llm_unavailable", "Ollama no disponible") from exc
    except requests.exceptions.Timeout as exc:
        raise OllamaClientError("llm_timeout", "Ollama ha agotado el tiempo de respuesta") from exc
    except requests.exceptions.RequestException as exc:
        raise OllamaClientError("llm_http_error", str(exc)) from exc

    if response.status_code != 200:
        code, error_message = _error_from_response(response)
        raise OllamaClientError(code, error_message)

    try:
        data = response.json()
    except ValueError as exc:
        raise OllamaClientError("llm_invalid_json", "ollama_invalid_json") from exc

    raw_models = data.get("models")
    if not isinstance(raw_models, list):
        raise OllamaClientError("llm_invalid_json", "ollama_models_invalid")

    models: list[str] = []
    for raw_model in raw_models:
        if not isinstance(raw_model, dict):
            continue

        candidate = raw_model.get("name")
        if not isinstance(candidate, str) or not candidate.strip():
            candidate = raw_model.get("model")
        if not isinstance(candidate, str):
            continue

        normalized_model = candidate.strip()
        if normalized_model and normalized_model not in models:
            models.append(normalized_model)

    return models


def ask_chat(
    message: str,
    *,
    model: str | None = None,
    temperature: float | None = None,
    use_rag: bool | None = None,
    num_predict: int | None = None,
    system_prompt: str | None = None,
    requests_module=requests,
    settings_obj=settings,
) -> dict:
    if not isinstance(message, str) or not message.strip():
        raise OllamaClientError("llm_generation_failed", "message_required")

    selected_model = model or _selected_model(settings_obj)
    selected_temperature = temperature if temperature is not None else settings_obj.temperature
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": message})

    payload = {
        "model": selected_model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": selected_temperature,
            "num_predict": num_predict if num_predict is not None else 300,
        },
    }

    try:
        response = requests_module.post(
            _api_chat_url(settings_obj),
            json=payload,
            timeout=_timeout_seconds(settings_obj),
        )
    except requests.exceptions.ConnectionError as exc:
        raise OllamaClientError("llm_unavailable", "Ollama no disponible") from exc
    except requests.exceptions.Timeout as exc:
        raise OllamaClientError("llm_timeout", "Ollama ha agotado el tiempo de respuesta") from exc
    except requests.exceptions.RequestException as exc:
        raise OllamaClientError("llm_http_error", str(exc)) from exc

    if response.status_code != 200:
        code, error_message = _error_from_response(response)
        raise OllamaClientError(code, error_message)

    try:
        data = response.json()
    except ValueError as exc:
        raise OllamaClientError("llm_invalid_json", "ollama_invalid_json") from exc

    try:
        content = data["message"]["content"]
    except (KeyError, TypeError) as exc:
        raise OllamaClientError("llm_missing_content", "ollama_missing_message_content") from exc

    if not isinstance(content, str) or not content.strip():
        raise OllamaClientError("llm_missing_content", "ollama_missing_message_content")

    response_model = data.get("model")
    if not isinstance(response_model, str) or not response_model.strip():
        response_model = selected_model

    metrics = {
        "prompt_eval_count": data.get("prompt_eval_count") if isinstance(data.get("prompt_eval_count"), int) else None,
        "eval_count": data.get("eval_count") if isinstance(data.get("eval_count"), int) else None,
        "prompt_eval_duration": data.get("prompt_eval_duration") if isinstance(data.get("prompt_eval_duration"), int) else None,
        "eval_duration": data.get("eval_duration") if isinstance(data.get("eval_duration"), int) else None,
        "total_duration": data.get("total_duration") if isinstance(data.get("total_duration"), int) else None,
        "load_duration": data.get("load_duration") if isinstance(data.get("load_duration"), int) else None,
    }

    return {
        "status": "ok",
        "provider": "ollama",
        "model": response_model,
        "temperature": selected_temperature,
        "temperature_ignored": False,
        "use_rag": True if use_rag is None else bool(use_rag),
        "answer": content.strip(),
        **metrics,
    }
