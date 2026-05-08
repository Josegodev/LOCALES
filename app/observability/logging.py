import json
import logging
import sys
from typing import Any


class _StdoutProxy:
    def write(self, message: str) -> int:
        return sys.stdout.write(message)

    def flush(self) -> None:
        sys.stdout.flush()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = getattr(record, "payload", None)
        if payload is None:
            payload = {
                "component": record.name,
                "level": record.levelname.lower(),
                "message": record.getMessage(),
            }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def get_logger() -> logging.Logger:
    logger = logging.getLogger("locales")
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(_StdoutProxy())
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


def log_event(
    *,
    component: str,
    event: str | None = None,
    trace_id: str | None = None,
    request_id: str | None = None,
    level: int = logging.INFO,
    **fields: Any,
) -> None:
    payload: dict[str, Any] = {"component": component}

    if event is not None:
        payload["event"] = event

    if request_id is None and trace_id is not None:
        request_id = trace_id

    if trace_id is not None:
        payload["trace_id"] = trace_id

    if request_id is not None:
        payload["request_id"] = request_id

    for key, value in fields.items():
        if value is not None:
            payload[key] = value

    get_logger().log(level, "", extra={"payload": payload})
