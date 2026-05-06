import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"No existe config.json: {CONFIG_PATH}")

    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def send_chat_completion(payload: dict[str, Any]) -> dict[str, Any]:
    config = load_config()

    base_url = config["lmstudio_base_url"].rstrip("/")
    url = f"{base_url}/chat/completions"

    timeout = int(config.get("request_timeout_seconds", 120))

    headers = {
        "Content-Type": "application/json",
    }

    token = config.get("lmstudio_api_token")

    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    request = urllib.request.Request(
        url=url,
        data=body,
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response_body = response.read().decode("utf-8")

    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"LM Studio HTTP {exc.code}: {error_body}") from exc

    except urllib.error.URLError as exc:
        raise RuntimeError(f"No se pudo conectar a LM Studio: {exc}") from exc

    try:
        return json.loads(response_body)

    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Respuesta no JSON de LM Studio: {response_body}") from exc


def extract_message_content(response_json: dict[str, Any]) -> str:
    try:
        message = response_json["choices"][0]["message"]
        content = message.get("content", "")

    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Respuesta inesperada de LM Studio: {response_json}") from exc

    if not isinstance(content, str):
        raise RuntimeError(f"Contenido no textual recibido: {content}")

    content = content.strip()

    if not content:
        raise RuntimeError("Respuesta vacía del modelo")

    return content

   