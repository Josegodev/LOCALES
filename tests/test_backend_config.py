import os
import unittest

from app import config
from app.adapters import backend_client


class BackendConfigTests(unittest.TestCase):
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

    def test_backend_client_builds_chat_url_from_base_url(self):
        captured: dict = {}

        class DummyResponse:
            status_code = 200

            @staticmethod
            def json() -> dict:
                return {"status": "ok", "provider": "ollama", "model": "granite4.1:8b", "answer": "ok"}

        class DummyRequests:
            @staticmethod
            def post(url: str, json: dict, timeout: int):
                captured["url"] = url
                captured["json"] = json
                captured["timeout"] = timeout
                return DummyResponse()

        response = backend_client.ask_chat(
            "hola",
            requests_module=DummyRequests,
            base_url="http://192.168.1.20:8000/",
            timeout_seconds=90,
        )

        self.assertEqual(captured["url"], "http://192.168.1.20:8000/chat")
        self.assertEqual(response["answer"], "ok")


if __name__ == "__main__":
    unittest.main()
