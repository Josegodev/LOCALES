import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app, telegram_runtime as live_telegram_runtime
from app.llm_client import LLMClientError
from app.schemas import TelegramConfigUpdateRequest
from app.telegram_runtime import TelegramRuntime, TelegramRuntimeConfig, resolve_telegram_provider_model


class TelegramEmbeddedRuntimeTests(unittest.TestCase):
    def setUp(self):
        self._original_live_config = TelegramRuntimeConfig(
            provider=live_telegram_runtime._config.provider,
            model=live_telegram_runtime._config.model,
            temperature=live_telegram_runtime._config.temperature,
            use_rag=live_telegram_runtime._config.use_rag,
        )

    def tearDown(self):
        live_telegram_runtime._config = TelegramRuntimeConfig(
            provider=self._original_live_config.provider,
            model=self._original_live_config.model,
            temperature=self._original_live_config.temperature,
            use_rag=self._original_live_config.use_rag,
        )

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
        self.assertIn("provider", status)
        self.assertIn("model", status)
        self.assertIn("rag_enabled", status)
        self.assertNotIn("telegram_bot_token", status)
        self.assertNotIn("bot_token", status)

    def test_start_if_enabled_fails_fast_when_enabled_without_token(self):
        runtime = TelegramRuntime()

        with patch("app.telegram_runtime.settings.telegram_enabled", True):
            with patch.object(runtime, "token_configured", return_value=False):
                with self.assertRaises(RuntimeError) as ctx:
                    runtime.start_if_enabled()

        self.assertEqual(str(ctx.exception), "TELEGRAM_BOT_TOKEN no definido.")

    def test_telegram_config_endpoint_resolves_gpt_alias_to_openai(self):
        with patch("app.main.telegram_runtime.start_if_enabled"):
            with TestClient(app) as client:
                response = client.post(
                    "/telegram/config",
                    json={"model": "gpt", "temperature": 0.2, "rag_enabled": True},
                )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["provider"], "openai")
        self.assertEqual(payload["model"], "gpt-5.5")
        self.assertEqual(payload["default_provider"], "ollama")
        self.assertEqual(payload["default_model"], "granite4.1:8b")

    def test_telegram_config_endpoint_resolves_explicit_gpt_model_to_openai(self):
        with patch("app.main.telegram_runtime.start_if_enabled"):
            with TestClient(app) as client:
                response = client.post(
                    "/telegram/config",
                    json={"model": "gpt-5.5", "temperature": 0.2, "rag_enabled": True},
                )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["provider"], "openai")
        self.assertEqual(payload["model"], "gpt-5.5")

    def test_telegram_config_endpoint_preserves_local_granite_pair(self):
        with patch("app.main.telegram_runtime.start_if_enabled"):
            with TestClient(app) as client:
                response = client.post(
                    "/telegram/config",
                    json={"model": "granite4.1:8b", "temperature": 0.2, "rag_enabled": True},
                )

        payload = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["provider"], "ollama")
        self.assertEqual(payload["model"], "granite4.1:8b")

    def test_telegram_config_endpoint_defaults_remain_ollama_granite(self):
        with patch("app.main.telegram_runtime.start_if_enabled"):
            with TestClient(app) as client:
                payload = client.get("/telegram/config").json()

        self.assertEqual(payload["provider"], "ollama")
        self.assertEqual(payload["model"], "granite4.1:8b")
        self.assertEqual(payload["default_provider"], "ollama")
        self.assertEqual(payload["default_model"], "granite4.1:8b")

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

    def test_resolve_provider_model_maps_gpt_alias_to_openai(self):
        provider, model = resolve_telegram_provider_model("gpt")

        self.assertEqual(provider, "openai")
        self.assertEqual(model, "gpt-5.5")

    def test_resolve_provider_model_maps_explicit_gpt_model_to_openai(self):
        provider, model = resolve_telegram_provider_model("gpt-5.5")

        self.assertEqual(provider, "openai")
        self.assertEqual(model, "gpt-5.5")

    def test_resolve_provider_model_preserves_default_ollama_when_empty(self):
        provider, model = resolve_telegram_provider_model("")

        self.assertEqual(provider, "ollama")
        self.assertEqual(model, "granite4.1:8b")

    def test_resolve_provider_model_keeps_local_granite_on_ollama(self):
        provider, model = resolve_telegram_provider_model("granite4.1:8b")

        self.assertEqual(provider, "ollama")
        self.assertEqual(model, "granite4.1:8b")

    def test_resolve_provider_model_rejects_invalid_explicit_pair(self):
        with self.assertRaises(LLMClientError) as ctx:
            resolve_telegram_provider_model("gpt-5.5", provider="ollama")

        self.assertEqual(ctx.exception.code, "invalid_provider_model_pair")

    def test_ask_backend_sends_resolved_openai_provider_model_pair(self):
        runtime = TelegramRuntime()
        runtime.update_config(model="gpt", temperature=0.2, rag_enabled=True)
        captured: dict = {}

        def fake_ask_chat(message: str, **kwargs):
            captured["message"] = message
            captured["kwargs"] = dict(kwargs)
            return {
                "status": "ok",
                "provider": "openai",
                "model": "gpt-5.5",
                "temperature": 0.2,
                "use_rag": True,
                "answer": "ok",
            }

        with patch("app.telegram_runtime.backend_client.ask_chat", side_effect=fake_ask_chat):
            runtime._ask_backend("hola", trace_id="trace-1")

        self.assertEqual(captured["kwargs"]["provider"], "openai")
        self.assertEqual(captured["kwargs"]["model"], "gpt-5.5")


if __name__ == "__main__":
    unittest.main()
