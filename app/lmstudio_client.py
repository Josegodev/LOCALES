import time
import json
import traceback
import requests

from app.config import settings


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

    print("LM Studio URL:", url, flush=True)
    print(
        "LM Studio payload:",
        json.dumps(payload, ensure_ascii=False),
        flush=True,
    )

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=settings.lmstudio_timeout_seconds,
        )
    except requests.exceptions.ConnectionError:
        traceback.print_exc()
        raise LLMError("LMSTUDIO_UNAVAILABLE", "LM Studio no está disponible.")
    except requests.exceptions.Timeout:
        traceback.print_exc()
        raise LLMError("TIMEOUT", "LM Studio ha agotado el tiempo de respuesta.")
    except requests.exceptions.RequestException as exc:
        traceback.print_exc()
        raise LLMError("HTTP_ERROR", str(exc))

    latency_ms = int((time.perf_counter() - start) * 1000)

    print("LM Studio status:", response.status_code, flush=True)
    print("LM Studio body:", response.text, flush=True)

    if response.status_code != 200:
        traceback.print_stack()
        raise LLMError(
            "LMSTUDIO_HTTP_ERROR",
            f"LM Studio devolvió HTTP {response.status_code}: {response.text[:300]}",
        )

    try:
        data = response.json()
        choice = data["choices"][0]
        message_payload = choice["message"]
        answer = message_payload["content"]
    except Exception:
        traceback.print_exc()
        raise LLMError("INVALID_RESPONSE", "Respuesta inválida de LM Studio.")

    if not isinstance(answer, str) or not answer.strip():
        print(
            "LM Studio parsed response:",
            json.dumps(data, ensure_ascii=False),
            flush=True,
        )
        traceback.print_stack()
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
