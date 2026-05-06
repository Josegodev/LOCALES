from __future__ import annotations

import requests


LMSTUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"
DEFAULT_MODEL = "local-model"


def ask_lmstudio(prompt: str, model: str = DEFAULT_MODEL, timeout: int = 120) -> str:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres un asistente de análisis documental. "
                    "Debes responder solo con la evidencia proporcionada."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.2,
        "stream": False,
    }

    response = requests.post(
        LMSTUDIO_URL,
        json=payload,
        timeout=timeout,
    )

    response.raise_for_status()
    data = response.json()

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Respuesta inesperada de LM Studio: {data}") from exc
