import requests

from app.config import settings


SYSTEM_PROMPT = """Responde solo con Markdown.
No incluyas rutas de archivos.
No incluyas comandos de shell.
No afirmes que has creado archivos.
No pidas permisos.
No devuelvas JSON salvo que el usuario lo pida como contenido documental.
"""


class LLMClientError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def generate_markdown(prompt: str, request_id: str) -> str:
    if not isinstance(prompt, str) or not prompt.strip():
        raise LLMClientError("llm_generation_failed", "prompt_required")
    if not isinstance(request_id, str) or not request_id.strip():
        raise LLMClientError("llm_generation_failed", "request_id_required")

    payload = {
        "model": settings.lmstudio_model,
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "stream": False,
        "temperature": settings.temperature,
    }

    try:
        response = requests.post(
            f"{settings.lmstudio_v1_base_url()}/chat/completions",
            json=payload,
            timeout=settings.llm_timeout_seconds,
        )
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as exc:
        raise LLMClientError("llm_unavailable", "LM Studio no disponible") from exc
    except requests.exceptions.RequestException as exc:
        raise LLMClientError("llm_generation_failed", str(exc)) from exc

    if response.status_code != 200:
        raise LLMClientError(
            "llm_generation_failed",
            f"LM Studio devolvio HTTP {response.status_code}",
        )

    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise LLMClientError("llm_generation_failed", "lmstudio_invalid_response") from exc

    if not isinstance(content, str):
        raise LLMClientError("llm_generation_failed", "lmstudio_content_not_text")

    return content
