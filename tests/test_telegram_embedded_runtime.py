import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas import TelegramConfigUpdateRequest
from app.telegram_runtime import TelegramRuntime


class TelegramEmbeddedRuntimeTests(unittest.TestCase):
    def test_startup_lifecycle_invokes_auto_start_hook(self):
        with patch("app.main.telegram_runtime.start_if_enabled") as start_if_enabled:
            with TestClient(app):
                pass

        start_if_enabled.assert_called_once()

    def test_status_exposes_operational_fields_without_token(self):
        runtime = TelegramRuntime()

        with patch("app.telegram_runtime.settings.telegram_enabled", True):
            status = runtime.status()

        self.assertTrue(status["enabled"])
        self.assertFalse(status["running"])
        self.assertIn("token_present", status)
        self.assertIn("model", status)
        self.assertIn("rag_enabled", status)
        self.assertNotIn("telegram_bot_token", status)
        self.assertNotIn("bot_token", status)

    def test_config_update_schema_uses_frontend_contract(self):
        request = TelegramConfigUpdateRequest(
            model="granite4.1:8b",
            temperature=0.2,
            rag_enabled=True,
        )

        self.assertEqual(request.model, "granite4.1:8b")
        self.assertEqual(request.temperature, 0.2)
        self.assertTrue(request.rag_enabled)

        with self.assertRaises(ValidationError):
            TelegramConfigUpdateRequest(
                default_model="granite4.1:8b",
                default_temperature=0.2,
                default_rag_enabled=True,
            )


if __name__ == "__main__":
    unittest.main()
