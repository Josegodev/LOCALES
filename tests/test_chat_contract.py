import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas import ChatResponse


class ChatContractTests(unittest.TestCase):
    def test_chat_rejects_invalid_payload(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            response = TestClient(app).post(
                "/chat",
                json={"provider": "ollama", "model": "granite4.1:8b"},
            )

        self.assertEqual(response.status_code, 422)

    def test_chat_returns_mocked_runtime_response_with_public_fields(self):
        expected_response = ChatResponse(
            trace_id="12345678-1234-5678-1234-567812345678",
            status="ok",
            provider="ollama",
            model="granite4.1:8b",
            temperature=0.2,
            use_rag=False,
            answer="Respuesta estable.",
            latency_ms=17,
            retrieval_status="DISABLED",
            answer_mode="standard_answer",
            warnings=["runtime_mocked"],
        )

        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            with patch("app.main.run_chat_request", return_value=expected_response) as run_chat_request_mock:
                response = TestClient(app).post(
                    "/chat",
                    json={
                        "message": "hola",
                        "provider": "ollama",
                        "model": "granite4.1:8b",
                        "use_rag": False,
                    },
                )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["answer"], "Respuesta estable.")
        self.assertEqual(payload["trace_id"], "12345678-1234-5678-1234-567812345678")
        self.assertEqual(payload["retrieval_status"], "DISABLED")
        self.assertEqual(payload["answer_mode"], "standard_answer")
        self.assertEqual(payload["latency_ms"], 17)
        self.assertEqual(payload["warnings"], ["runtime_mocked"])
        run_chat_request_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
