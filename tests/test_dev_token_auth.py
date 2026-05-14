import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class DevTokenAuthTests(unittest.TestCase):
    def test_health_remains_open_without_token(self):
        with patch("app.auth.settings.jose_dev_token", "test-dev-token"):
            response = TestClient(app).get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_chat_without_token_returns_401(self):
        with patch("app.auth.settings.jose_dev_token", "test-dev-token"):
            response = TestClient(app).post("/chat", json={"message": "hola"})

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"]["code"], "invalid_token")

    def test_chat_with_wrong_token_returns_401(self):
        with patch("app.auth.settings.jose_dev_token", "test-dev-token"):
            response = TestClient(app).post(
                "/chat",
                headers={"Authorization": "Bearer wrong-token"},
                json={"message": "hola"},
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"]["code"], "invalid_token")

    def test_chat_with_correct_token_returns_success(self):
        with patch("app.auth.settings.jose_dev_token", "test-dev-token"):
            with patch(
                "app.main.build_document_prompt",
                return_value={"status": "EVIDENCE_FOUND", "prompt": "context prompt", "chunks": []},
            ):
                with patch(
                    "app.main.ask_chat",
                    return_value={
                        "status": "ok",
                        "provider": "ollama",
                        "model": "granite4.1:8b",
                        "temperature": 0.2,
                        "use_rag": True,
                        "answer": "ok",
                    },
                ):
                    response = TestClient(app).post(
                        "/chat",
                        headers={"Authorization": "Bearer test-dev-token"},
                        json={"message": "hola"},
                    )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], "ok")

    def test_chat_returns_500_when_server_token_missing(self):
        with patch("app.auth.settings.jose_dev_token", None):
            response = TestClient(app).post(
                "/chat",
                headers={"Authorization": "Bearer anything"},
                json={"message": "hola"},
            )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"]["code"], "dev_token_not_configured")


if __name__ == "__main__":
    unittest.main()
