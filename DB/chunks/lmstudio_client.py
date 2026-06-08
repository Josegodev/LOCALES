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

    try:
        response = requests.post(
            LMSTUDIO_URL,
            json=payload,
            timeout=timeout,
        )
    except requests.exceptions.ConnectionError as exc:
        raise RuntimeError("LM Studio no está disponible") from exc
    except requests.exceptions.Timeout as exc:
        raise RuntimeError("LM Studio ha agotado el tiempo de respuesta") from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Error de red al conectar con LM Studio: {exc}") from exc

    if response.status_code != 200:
        raise RuntimeError(
            f"LM Studio devolvió HTTP {response.status_code}: {response.text[:300]}"
        )

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError(f"Respuesta no JSON de LM Studio: {response.text[:300]}") from exc

    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Respuesta inesperada de LM Studio: {data}") from exc
