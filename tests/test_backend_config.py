import os
import unittest
from pathlib import Path
from unittest.mock import patch

from app import config
from app.adapters import backend_client


class BackendConfigTests(unittest.TestCase):
    def test_env_file_path_is_repo_absolute(self):
        env_file = Path(config.Settings.model_config["env_file"])

        self.assertTrue(env_file.is_absolute())
        self.assertEqual(env_file.name, ".env")
        self.assertEqual(env_file.parent, config.REPO_ROOT)

    def test_backend_url_default_is_localhost_fastapi(self):
        settings = config.Settings(_env_file=None)
        self.assertEqual(settings.backend_base_url(), "http://127.0.0.1:8000")

    def test_backend_url_env_is_normalized_without_trailing_slash(self):
        previous = os.environ.get("BACKEND_URL")
        try:
            os.environ["BACKEND_URL"] = "http://192.168.1.20:8000/"
            settings = config.Settings(_env_file=None)
            self.assertEqual(settings.backend_base_url(), "http://192.168.1.20:8000")
        finally:
            if previous is None:
                os.environ.pop("BACKEND_URL", None)
            else:
                os.environ["BACKEND_URL"] = previous

    def test_backend_base_url_alias_is_supported(self):
        previous_legacy = os.environ.get("BACKEND_URL")
        previous_new = os.environ.get("BACKEND_BASE_URL")
        try:
            os.environ.pop("BACKEND_URL", None)
            os.environ["BACKEND_BASE_URL"] = "http://127.0.0.1:9001/"
            settings = config.Settings(_env_file=None)
            self.assertEqual(settings.backend_base_url(), "http://127.0.0.1:9001")
        finally:
            if previous_legacy is None:
                os.environ.pop("BACKEND_URL", None)
            else:
                os.environ["BACKEND_URL"] = previous_legacy
            if previous_new is None:
                os.environ.pop("BACKEND_BASE_URL", None)
            else:
                os.environ["BACKEND_BASE_URL"] = previous_new

    def test_backend_client_builds_chat_url_from_base_url(self):
        captured: dict = {}

        class DummyResponse:
            status_code = 200

            @staticmethod
            def json() -> dict:
                return {"status": "ok", "provider": "ollama", "model": "granite4.1:8b", "answer": "ok"}

        class DummyRequests:
            @staticmethod
            def post(url: str, json: dict, timeout: int, headers: dict | None = None):
                captured["url"] = url
                captured["json"] = json
                captured["timeout"] = timeout
                captured["headers"] = headers
                return DummyResponse()

        with patch.object(backend_client.settings, "jose_dev_token", "test-dev-token"):
            response = backend_client.ask_chat(
                "hola",
                requests_module=DummyRequests,
                base_url="http://192.168.1.20:8000/",
                timeout_seconds=90,
            )

        self.assertEqual(captured["url"], "http://192.168.1.20:8000/chat")
        self.assertEqual(captured["headers"], {"Authorization": "Bearer test-dev-token"})
        self.assertEqual(response["answer"], "ok")

    def test_backend_client_includes_provider_when_explicitly_provided(self):
        captured: dict = {}

        class DummyResponse:
            status_code = 200

            @staticmethod
            def json() -> dict:
                return {"status": "ok", "provider": "openai", "model": "gpt-5.5", "answer": "ok"}

        class DummyRequests:
            @staticmethod
            def post(url: str, json: dict, timeout: int, headers: dict | None = None):
                captured["url"] = url
                captured["json"] = json
                captured["timeout"] = timeout
                captured["headers"] = headers
                return DummyResponse()

        with patch.object(backend_client.settings, "jose_dev_token", "test-dev-token"):
            backend_client.ask_chat(
                "hola",
                provider="openai",
                model="gpt-5.5",
                requests_module=DummyRequests,
                base_url="http://127.0.0.1:8000",
                timeout_seconds=90,
            )

        self.assertEqual(captured["json"]["provider"], "openai")
        self.assertEqual(captured["json"]["model"], "gpt-5.5")

    def test_backend_client_fails_fast_when_internal_token_missing(self):
        with patch.object(backend_client.settings, "jose_dev_token", None):
            with self.assertRaises(backend_client.BackendClientError) as ctx:
                backend_client.build_internal_auth_headers()

        self.assertEqual(ctx.exception.code, "internal_auth_token_missing")
        self.assertEqual(ctx.exception.status_code, 500)


if __name__ == "__main__":
    unittest.main()
