import json
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
import requests
from pydantic import ValidationError

# Allows `python scripts/run_telegram.py` to import top-level packages (e.g. `app`).
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import settings
from app.llm_client import LLMClientError, generate_markdown
from app.schemas import CreateDocumentRequest
from app.telegram_permissions import TelegramPermissionConfigError, is_telegram_user_allowed

FASTAPI_URL = "http://127.0.0.1:8000"

TG_TOKEN = settings.telegram_bot_token
FASTAPI_CHAT_URL = f"{FASTAPI_URL}/chat"
FASTAPI_DOCUMENTS_URL = f"{FASTAPI_URL}/documents"

if not TG_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN no definido en .env")

BASE_URL = f"https://api.telegram.org/bot{TG_TOKEN}"
last_update_id = None

DOC_COMMAND = "doc.create"
DOC_USAGE_TEXT = "Uso: /doc nombre.md\\ncontenido"
DOC_AI_COMMAND = "doc_ai.create"
DOC_AI_USAGE_TEXT = "Uso: /doc_ai nombre.md\\ninstrucción para el modelo"


@dataclass(frozen=True)
class ParsedDocCommand:
    command: str
    filename: str
    content: str
    user_id: int
    chat_id: int


@dataclass(frozen=True)
class ParsedDocAiCommand:
    command: str
    filename: str
    prompt: str
    user_id: int
    chat_id: int


class DocCommandParseError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class LLMOutputValidationError(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


def parse_doc_command(
    text: str,
    user_id: int | None,
    chat_id: int | None,
) -> ParsedDocCommand:
    if not isinstance(user_id, int):
        raise DocCommandParseError("user_id_required", "No se pudo identificar el usuario.")
    if not isinstance(chat_id, int):
        raise DocCommandParseError("chat_id_required", "No se pudo identificar el chat.")

    raw = text.removeprefix("/doc")
    if not raw.strip() or "\n" not in raw:
        raise DocCommandParseError("invalid_doc_usage", DOC_USAGE_TEXT)

    filename, content = raw.lstrip().split("\n", 1)

    return ParsedDocCommand(
        command=DOC_COMMAND,
        filename=filename.strip(),
        content=content.strip(),
        user_id=user_id,
        chat_id=chat_id,
    )


def parse_doc_ai_command(
    text: str,
    user_id: int | None,
    chat_id: int | None,
) -> ParsedDocAiCommand:
    if not isinstance(user_id, int):
        raise DocCommandParseError("user_id_required", "No se pudo identificar el usuario.")
    if not isinstance(chat_id, int):
        raise DocCommandParseError("chat_id_required", "No se pudo identificar el chat.")

    raw = text.removeprefix("/doc_ai")
    parts = raw.lstrip().split(None, 1)
    if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
        raise DocCommandParseError("invalid_doc_ai_usage", DOC_AI_USAGE_TEXT)

    return ParsedDocAiCommand(
        command=DOC_AI_COMMAND,
        filename=parts[0].strip(),
        prompt=parts[1].strip(),
        user_id=user_id,
        chat_id=chat_id,
    )


def _validation_error_reason(exc: ValidationError) -> str:
    first_error = exc.errors()[0]
    ctx = first_error.get("ctx") or {}
    original_error = ctx.get("error")
    if original_error:
        return str(original_error)
    return str(first_error.get("msg", "validation_error"))


def _response_error_reason(response: requests.Response) -> str:
    try:
        detail = response.json().get("detail", {})
    except Exception:
        return response.text or "backend_error"

    if isinstance(detail, dict):
        return str(detail.get("code") or detail.get("message") or "backend_error")
    return str(detail or "backend_error")


def _doc_error_reply(message: str, request_id: str) -> str:
    return f"{message} (request_id={request_id})"


def _validate_llm_markdown_output(content: str) -> str:
    if not isinstance(content, str):
        raise LLMOutputValidationError("llm_output_not_text", "La salida del LLM no es texto.")

    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    if "\x00" in normalized:
        raise LLMOutputValidationError(
            "llm_output_contains_null_byte",
            "La salida del LLM contiene bytes nulos.",
        )

    normalized = normalized.strip()
    if not normalized:
        raise LLMOutputValidationError("llm_output_empty", "La salida del LLM está vacía.")

    if len(normalized) > settings.llm_max_output_chars:
        raise LLMOutputValidationError(
            "llm_output_too_large",
            "La salida del LLM supera el tamaño máximo.",
        )

    return normalized


def _log_doc_ai_event(
    *,
    event: str,
    request_id: str,
    user_id: int | None,
    chat_id: int | None,
    filename: str,
    model: str,
    status: str,
    reason: str,
    started_at: float,
    output_chars: int = 0,
) -> None:
    payload = {
        "event": event,
        "component": event.rsplit(".", 1)[0],
        "request_id": request_id,
        "command": DOC_AI_COMMAND,
        "user_id": user_id,
        "chat_id": chat_id,
        "filename": filename,
        "model": model,
        "duration_ms": int((time.perf_counter() - started_at) * 1000),
        "status": status,
        "reason": reason,
        "output_chars": output_chars,
    }
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True), flush=True)


def _log_doc_attempt(
    *,
    request_id: str,
    command: str,
    user_id: int | None,
    chat_id: int | None,
    filename: str,
    status: str,
    reason: str,
    started_at: float,
) -> None:
    event = {
        "component": "telegram.doc",
        "request_id": request_id,
        "command": command,
        "user_id": user_id,
        "chat_id": chat_id,
        "filename": filename,
        "status": status,
        "reason": reason,
        "duration_ms": int((time.perf_counter() - started_at) * 1000),
    }
    print(json.dumps(event, ensure_ascii=False, sort_keys=True), flush=True)


def handle_doc_command(text: str, user_id: int | None, chat_id: int | None) -> str:
    request_id = uuid.uuid4().hex
    started_at = time.perf_counter()
    command = DOC_COMMAND
    filename = ""
    status = "error"
    reason = "unexpected_error"

    try:
        parsed = parse_doc_command(text=text, user_id=user_id, chat_id=chat_id)
        command = parsed.command
        filename = parsed.filename

        if not is_telegram_user_allowed(parsed.user_id):
            status = "rejected"
            reason = "telegram_user_not_allowed"
            return _doc_error_reply("No autorizado para crear documentos.", request_id)

        try:
            request = CreateDocumentRequest(
                request_id=request_id,
                filename=parsed.filename,
                content=parsed.content,
                user_id=parsed.user_id,
                chat_id=parsed.chat_id,
            )
        except ValidationError as exc:
            status = "rejected"
            reason = _validation_error_reason(exc)
            return _doc_error_reply(f"No se pudo crear el documento: {reason}", request_id)

        payload = request.model_dump()
        payload["overwrite"] = False

        response = requests.post(
            FASTAPI_DOCUMENTS_URL,
            json=payload,
            timeout=20,
        )

        if response.status_code >= 400:
            status = "rejected" if response.status_code < 500 else "error"
            reason = _response_error_reason(response)
            return _doc_error_reply(f"No se pudo crear el documento: {reason}", request_id)

        data = response.json()
        status = "accepted"
        reason = "created"
        return f"Documento creado: {data['filename']} ({data['chars']} caracteres)"

    except DocCommandParseError as exc:
        status = "rejected"
        reason = exc.code
        return _doc_error_reply(exc.message, request_id)
    except TelegramPermissionConfigError:
        status = "error"
        reason = "telegram_permission_config_invalid"
        return _doc_error_reply(
            "No se pudo comprobar autorización para crear documentos.",
            request_id,
        )
    except Exception as exc:
        reason = exc.__class__.__name__
        return _doc_error_reply("No se pudo crear el documento: unexpected_error", request_id)
    finally:
        _log_doc_attempt(
            request_id=request_id,
            command=command,
            user_id=user_id,
            chat_id=chat_id,
            filename=filename,
            status=status,
            reason=reason,
            started_at=started_at,
        )


def handle_doc_ai_command(text: str, user_id: int | None, chat_id: int | None) -> str:
    request_id = uuid.uuid4().hex
    started_at = time.perf_counter()
    filename = ""
    model = settings.lmstudio_model
    status = "error"
    reason = "unexpected_error"
    output_chars = 0

    try:
        parsed = parse_doc_ai_command(text=text, user_id=user_id, chat_id=chat_id)
        filename = parsed.filename
        _log_doc_ai_event(
            event="telegram.doc_ai.received",
            request_id=request_id,
            user_id=parsed.user_id,
            chat_id=parsed.chat_id,
            filename=filename,
            model=model,
            status="received",
            reason="received",
            started_at=started_at,
        )

        if not is_telegram_user_allowed(parsed.user_id):
            status = "rejected"
            reason = "telegram_user_not_allowed"
            return _doc_error_reply("No autorizado para crear documentos.", request_id)

        try:
            CreateDocumentRequest(
                request_id=request_id,
                filename=parsed.filename,
                content="contenido temporal para validar filename",
                user_id=parsed.user_id,
                chat_id=parsed.chat_id,
                overwrite=False,
            )
        except ValidationError as exc:
            status = "rejected"
            reason = _validation_error_reason(exc)
            return _doc_error_reply(f"No se pudo crear el documento: {reason}", request_id)

        llm_started_at = time.perf_counter()
        _log_doc_ai_event(
            event="llm.request.started",
            request_id=request_id,
            user_id=parsed.user_id,
            chat_id=parsed.chat_id,
            filename=filename,
            model=model,
            status="started",
            reason="started",
            started_at=llm_started_at,
        )

        try:
            llm_output = generate_markdown(parsed.prompt, request_id=request_id)
        except LLMClientError as exc:
            _log_doc_ai_event(
                event="llm.request.failed",
                request_id=request_id,
                user_id=parsed.user_id,
                chat_id=parsed.chat_id,
                filename=filename,
                model=model,
                status="error",
                reason=exc.code,
                started_at=llm_started_at,
            )
            status = "rejected"
            reason = exc.code
            return _doc_error_reply(f"No se pudo generar el documento: {reason}", request_id)

        try:
            content = _validate_llm_markdown_output(llm_output)
        except LLMOutputValidationError as exc:
            _log_doc_ai_event(
                event="llm.request.finished",
                request_id=request_id,
                user_id=parsed.user_id,
                chat_id=parsed.chat_id,
                filename=filename,
                model=model,
                status="rejected",
                reason=exc.code,
                started_at=llm_started_at,
                output_chars=len(llm_output) if isinstance(llm_output, str) else 0,
            )
            status = "rejected"
            reason = exc.code
            return _doc_error_reply(f"No se pudo crear el documento: {reason}", request_id)

        output_chars = len(content)
        _log_doc_ai_event(
            event="llm.request.finished",
            request_id=request_id,
            user_id=parsed.user_id,
            chat_id=parsed.chat_id,
            filename=filename,
            model=model,
            status="ok",
            reason="generated",
            started_at=llm_started_at,
            output_chars=output_chars,
        )

        try:
            request = CreateDocumentRequest(
                request_id=request_id,
                filename=parsed.filename,
                content=content,
                user_id=parsed.user_id,
                chat_id=parsed.chat_id,
                overwrite=False,
            )
        except ValidationError as exc:
            status = "rejected"
            reason = _validation_error_reason(exc)
            return _doc_error_reply(f"No se pudo crear el documento: {reason}", request_id)

        payload = request.model_dump()
        payload["overwrite"] = False

        response = requests.post(
            FASTAPI_DOCUMENTS_URL,
            json=payload,
            timeout=20,
        )

        if response.status_code >= 400:
            status = "rejected" if response.status_code < 500 else "error"
            reason = _response_error_reason(response)
            return _doc_error_reply(f"No se pudo crear el documento: {reason}", request_id)

        data = response.json()
        status = "accepted"
        reason = "created"
        return f"Documento creado: {data['filename']} ({data['chars']} caracteres)"

    except DocCommandParseError as exc:
        status = "rejected"
        reason = exc.code
        return _doc_error_reply(exc.message, request_id)
    except TelegramPermissionConfigError:
        status = "error"
        reason = "telegram_permission_config_invalid"
        return _doc_error_reply(
            "No se pudo comprobar autorización para crear documentos.",
            request_id,
        )
    except Exception as exc:
        reason = exc.__class__.__name__
        return _doc_error_reply("No se pudo crear el documento: unexpected_error", request_id)
    finally:
        _log_doc_ai_event(
            event="telegram.doc_ai.created"
            if status == "accepted"
            else "telegram.doc_ai.rejected",
            request_id=request_id,
            user_id=user_id,
            chat_id=chat_id,
            filename=filename,
            model=model,
            status=status,
            reason=reason,
            started_at=started_at,
            output_chars=output_chars,
        )


def get_updates() -> list[dict]:
    global last_update_id

    params = {"timeout": 10}
    if last_update_id is not None:
        params["offset"] = last_update_id + 1

    r = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=15)
    r.raise_for_status()

    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram getUpdates error: {data}")

    return data.get("result", [])


def send_message(chat_id: int, text: str) -> None:
    r = requests.post(
        f"{BASE_URL}/sendMessage",
        json={"chat_id": chat_id, "text": text[:4000]},
        timeout=15,
    )
    r.raise_for_status()


def ask_fastapi(message: str) -> dict:
    r = requests.post(
        FASTAPI_CHAT_URL,
        json={"message": message},
        timeout=90,
    )
    r.raise_for_status()
    return r.json()

def ask_backend(text: str) -> str:
    response = requests.post(
        f"{FASTAPI_URL}/chat",
        json={
            "slug": "lmstudio_qwen35_9b_q4km_temp07",
            "prompt": text,
        },
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    return data.get("answer", str(data))

def handle_message(msg: dict) -> None:
    chat_id = msg["chat"]["id"]
    user_id = msg.get("from", {}).get("id")
    text = msg.get("text", "").strip()

    if text.startswith("/doc_ai"):
        print(f"RX chat_id={chat_id} command=/doc_ai text_chars={len(text)}", flush=True)
    else:
        print(f"RX chat_id={chat_id} text={text!r}", flush=True)

    if not text:
        send_message(chat_id, "Mensaje vacío o no soportado.")
        return

    try:
        if text.startswith("/doc_ai"):
            response = handle_doc_ai_command(text, user_id=user_id, chat_id=chat_id)
            send_message(chat_id, response)
        elif text.startswith("/doc"):
            response = handle_doc_command(text, user_id=user_id, chat_id=chat_id)
            send_message(chat_id, response)
        else:
            result = ask_fastapi(text)
            answer = result.get("answer", "")
            send_message(chat_id, answer)

    except Exception as exc:
        print(f"ERROR: {exc}", flush=True)
        send_message(chat_id, f"ERROR: {exc}")


def main() -> None:
    global last_update_id

    print("Telegram polling iniciado vía FastAPI.", flush=True)
    print(f"FastAPI: {FASTAPI_CHAT_URL}", flush=True)

    while True:
        try:
            for update in get_updates():
                last_update_id = update["update_id"]

                if "message" in update:
                    handle_message(update["message"])

        except KeyboardInterrupt:
            print("\nTelegram polling detenido.", flush=True)
            break

        except Exception as exc:
            print(f"ERROR LOOP: {exc}", flush=True)

        time.sleep(1)


if __name__ == "__main__":
    main()
