import os

from app.config import settings


class TelegramPermissionConfigError(Exception):
    pass


def parse_allowed_user_ids(raw: str | None = None) -> set[int]:
    if raw is None:
        raw = os.getenv(
            "TELEGRAM_ALLOWED_USER_IDS",
            settings.telegram_allowed_user_ids or "",
        )

    allowed_ids: set[int] = set()
    for item in raw.split(","):
        value = item.strip()
        if not value:
            continue
        try:
            allowed_ids.add(int(value))
        except ValueError as exc:
            raise TelegramPermissionConfigError(
                "TELEGRAM_ALLOWED_USER_IDS debe contener enteros separados por comas"
            ) from exc

    return allowed_ids


def is_telegram_user_allowed(user_id: int) -> bool:
    return user_id in parse_allowed_user_ids()
