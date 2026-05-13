import json
import re

import requests

from app.config import settings


class TelegramApiError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        endpoint: str | None = None,
        status_code: int | None = None,
        response_body: str | None = None,
        retry_after: int | None = None,
        url: str | None = None,
    ):
        self.code = code
        self.message = message
        self.endpoint = endpoint
        self.status_code = status_code
        self.response_body = response_body
        self.retry_after = retry_after
        self.url = url
        super().__init__(message)


def _bot_token(explicit_bot_token: str | None = None) -> str:
    bot_token = explicit_bot_token or settings.telegram_bot_token
    if not bot_token:
        raise TelegramApiError("telegram_token_missing", "TELEGRAM_BOT_TOKEN no definido")
    return bot_token


def _base_url(explicit_bot_token: str | None = None) -> str:
    return f"https://api.telegram.org/bot{_bot_token(explicit_bot_token)}"


def _redact_bot_token_in_url(url: str | None) -> str | None:
    if not isinstance(url, str):
        return url
    return re.sub(r"/bot[0-9]{8,12}:[A-Za-z0-9_-]{30,}", "/bot<redacted>", url)


def _truncate_response_body(body: str, max_chars: int = 500) -> str:
    if len(body) <= max_chars:
        return body
    return body[:max_chars]


def _safe_response_json(response) -> dict | None:
    try:
        data = response.json()
    except (ValueError, TypeError, AttributeError):
        return None

    if isinstance(data, dict):
        return data

    return None


def _safe_response_body(response, max_chars: int = 500) -> str | None:
    response_text = getattr(response, "text", None)
    if isinstance(response_text, str) and response_text:
        return _truncate_response_body(response_text, max_chars=max_chars)

    data = _safe_response_json(response)
    if data is None:
        return None

    return _truncate_response_body(json.dumps(data, ensure_ascii=False), max_chars=max_chars)


def _extract_retry_after(response, payload: dict | None = None) -> int | None:
    if payload is None:
        payload = _safe_response_json(response)

    if isinstance(payload, dict):
        parameters = payload.get("parameters")
        if isinstance(parameters, dict):
            retry_after = parameters.get("retry_after")
            if isinstance(retry_after, int) and retry_after >= 0:
                return retry_after
            if isinstance(retry_after, str) and retry_after.isdigit():
                return int(retry_after)

    headers = getattr(response, "headers", None)
    if headers is None:
        return None

    retry_after_header = headers.get("Retry-After")
    if isinstance(retry_after_header, str) and retry_after_header.isdigit():
        return int(retry_after_header)

    return None


def classify_telegram_http_error(
    exc: requests.exceptions.HTTPError,
    *,
    endpoint: str,
) -> dict:
    response = exc.response
    status_code = getattr(response, "status_code", None)
    response_body = _safe_response_body(response)
    url = _redact_bot_token_in_url(getattr(response, "url", None))
    payload = _safe_response_json(response)
    retry_after = _extract_retry_after(response, payload)

    description = None
    if isinstance(payload, dict):
        raw_description = payload.get("description")
        if isinstance(raw_description, str):
            description = raw_description

    lowered_body = (response_body or "").lower()

    if status_code == 401:
        return {
            "code": "invalid_token",
            "reason": "invalid_token",
            "message": "Token de Telegram inválido o revocado.",
            "status_code": status_code,
            "response_body": response_body,
            "endpoint": endpoint,
            "url": url,
            "retry_after": retry_after,
            "description": description,
        }

    if status_code == 409:
        reason = "terminated_by_other_getUpdates" if "terminated by other getupdates request" in lowered_body else "polling_conflict"
        return {
            "code": "polling_conflict",
            "reason": reason,
            "message": "Ya hay otro proceso usando este bot token. Cierra procesos duplicados.",
            "status_code": status_code,
            "response_body": response_body,
            "endpoint": endpoint,
            "url": url,
            "retry_after": retry_after,
            "description": description,
        }

    if status_code == 429:
        return {
            "code": "rate_limited",
            "reason": "rate_limited",
            "message": "Telegram ha aplicado rate limiting al polling.",
            "status_code": status_code,
            "response_body": response_body,
            "endpoint": endpoint,
            "url": url,
            "retry_after": retry_after,
            "description": description,
        }

    if isinstance(status_code, int) and status_code >= 500:
        return {
            "code": "telegram_server_error",
            "reason": "telegram_server_error",
            "message": "Telegram devolvió un error de servidor.",
            "status_code": status_code,
            "response_body": response_body,
            "endpoint": endpoint,
            "url": url,
            "retry_after": retry_after,
            "description": description,
        }

    return {
        "code": "telegram_http_error",
        "reason": "telegram_http_error",
        "message": "Telegram devolvió un error HTTP no clasificado.",
        "status_code": status_code,
        "response_body": response_body,
        "endpoint": endpoint,
        "url": url,
        "retry_after": retry_after,
        "description": description,
    }


def classify_telegram_request_error(
    exc: requests.exceptions.RequestException,
    *,
    endpoint: str,
) -> dict:
    if isinstance(exc, requests.exceptions.HTTPError):
        return classify_telegram_http_error(exc, endpoint=endpoint)

    if isinstance(exc, requests.exceptions.Timeout):
        reason = "timeout"
        message = "Timeout al conectar con Telegram."
    elif isinstance(exc, requests.exceptions.ConnectionError):
        reason = "connection_error"
        message = "No se pudo conectar con Telegram."
    else:
        reason = exc.__class__.__name__
        message = "Error de red al llamar a Telegram."

    request = getattr(exc, "request", None)
    url = _redact_bot_token_in_url(getattr(request, "url", None))

    return {
        "code": "network_error",
        "reason": reason,
        "message": message,
        "status_code": None,
        "response_body": None,
        "endpoint": endpoint,
        "url": url,
        "retry_after": None,
        "description": None,
    }


def get_updates(
    *,
    last_update_id: int | None,
    requests_module=requests,
    bot_token: str | None = None,
    api_timeout_seconds: int = 15,
    poll_timeout_seconds: int = 10,
) -> list[dict]:
    params = {"timeout": poll_timeout_seconds}
    if last_update_id is not None:
        params["offset"] = last_update_id + 1

    response = requests_module.get(
        f"{_base_url(bot_token)}/getUpdates",
        params=params,
        timeout=api_timeout_seconds,
    )
    response.raise_for_status()

    data = response.json()
    if not data.get("ok"):
        raise TelegramApiError(
            "telegram_api_error",
            f"Telegram getUpdates error: {data}",
            endpoint="getUpdates",
            status_code=response.status_code,
            response_body=_safe_response_body(response),
            retry_after=_extract_retry_after(response, data),
            url=_redact_bot_token_in_url(getattr(response, "url", None)),
        )

    return data.get("result", [])


def send_message(
    chat_id: int,
    text: str,
    *,
    requests_module=requests,
    bot_token: str | None = None,
    timeout_seconds: int = 15,
) -> None:
    response = requests_module.post(
        f"{_base_url(bot_token)}/sendMessage",
        json={"chat_id": chat_id, "text": text[:4000]},
        timeout=timeout_seconds,
    )
    response.raise_for_status()

    data = _safe_response_json(response)
    if isinstance(data, dict) and not data.get("ok", True):
        raise TelegramApiError(
            "telegram_api_error",
            f"Telegram sendMessage error: {data}",
            endpoint="sendMessage",
            status_code=response.status_code,
            response_body=_safe_response_body(response),
            retry_after=_extract_retry_after(response, data),
            url=_redact_bot_token_in_url(getattr(response, "url", None)),
        )
