from app.adapters.telegram_api import send_message


def send_telegram_message(bot_token: str, chat_id: int, text: str) -> None:
    send_message(chat_id, text, bot_token=bot_token)


__all__ = ["send_telegram_message"]
