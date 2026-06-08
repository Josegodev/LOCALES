import os
import unittest
from unittest.mock import patch, MagicMock

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

from app.telegram_client import send_telegram_message


class SendTelegramMessageTests(unittest.TestCase):
    @patch("app.telegram_client.send_message")
    def test_delegates_to_adapter(self, mock_send):
        send_telegram_message("bot-token-123", 456, "hello world")
        mock_send.assert_called_once_with(456, "hello world", bot_token="bot-token-123")


if __name__ == "__main__":
    unittest.main()
