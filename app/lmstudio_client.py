import time
import json
import requests

from app.config import settings
from app.observability import log_event


class LLMError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def ask_lmstudio(
    message: str,
    model: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> dict:
    selected_model = model or settings.default_model

    payload = {
        "model": selected_model,
        "messages": [
            {
                "role": "system",
                "content": "Te llamas 5060Ti eres el bot del llm lab de Jose Gonzalez Oliva, tu función es responder a las preguntas de forma clara y concisa. Si no sabes la respuesta, di que no lo sabes.",
            },
            {
                "role": "user",
                "content": message,
            },
        ],
        "temperature": temperature if temperature is not None else settings.temperature,
        "max_tokens": max_tokens if max_tokens is not None else settings.max_tokens,
    }

    start = time.perf_counter()

    url = f"{settings.lmstudio_v1_base_url()}/chat/completions"

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=settings.lmstudio_timeout_seconds,
        )
    except requests.exceptions.ConnectionError as exc:
        log_event(component="lmstudio", event="lmstudio.connection_error", status="error", error=str(exc))
        raise LLMError("LMSTUDIO_UNAVAILABLE", "LM Studio no está disponible.") from exc
    except requests.exceptions.Timeout as exc:
        log_event(component="lmstudio", event="lmstudio.timeout", status="error", error=str(exc))
        raise LLMError("TIMEOUT", "LM Studio ha agotado el tiempo de respuesta.") from exc
    except requests.exceptions.RequestException as exc:
        log_event(component="lmstudio", event="lmstudio.request_error", status="error", error=str(exc))
        raise LLMError("HTTP_ERROR", "Error de conexión con LM Studio.") from exc

    latency_ms = int((time.perf_counter() - start) * 1000)

    if response.status_code != 200:
        log_event(component="lmstudio", event="lmstudio.http_error", status="error", http_status=response.status_code)
        raise LLMError(
            "LMSTUDIO_HTTP_ERROR",
            f"LM Studio devolvió HTTP {response.status_code}: {response.text[:300]}",
        )

    try:
        data = response.json()
        choice = data["choices"][0]
        message_payload = choice["message"]
        answer = message_payload["content"]
    except Exception as exc:
        log_event(component="lmstudio", event="lmstudio.invalid_response", status="error")
        raise LLMError("INVALID_RESPONSE", "Respuesta inválida de LM Studio.") from exc

    if not isinstance(answer, str) or not answer.strip():
        log_event(
            component="lmstudio",
            event="lmstudio.empty_response",
            status="error",
            model=data.get("model"),
            finish_reason=choice.get("finish_reason"),
        )
        raise LLMError(
            "EMPTY_RESPONSE",
            (
                "LM Studio devolvió content vacío. "
                f"model={data.get('model')!r}, "
                f"finish_reason={choice.get('finish_reason')!r}, "
                f"reasoning_content_present={bool(message_payload.get('reasoning_content'))}."
            ),
        )

    return {
        "status": "ok",
        "model": selected_model,
        "answer": answer.strip(),
        "latency_ms": latency_ms,
    }
