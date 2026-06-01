import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class ChatTemperatureContractTests(unittest.TestCase):
    def _rag_context(self) -> dict:
        return {"status": "EVIDENCE_FOUND", "prompt": "context prompt", "chunks": []}

    def test_chat_accepts_request_without_temperature(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            with patch("app.main.build_document_prompt", return_value=self._rag_context()):
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
                ) as ask_chat_mock:
                    response = TestClient(app).post(
                        "/chat",
                        json={"message": "hola", "provider": "ollama", "model": "granite4.1:8b"},
                    )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ask_chat_mock.call_args.kwargs["temperature"], 0.2)

    def test_chat_accepts_temperature_null_and_uses_default(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            with patch("app.main.build_document_prompt", return_value=self._rag_context()):
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
                ) as ask_chat_mock:
                    response = TestClient(app).post(
                        "/chat",
                        json={"message": "hola", "provider": "ollama", "model": "granite4.1:8b", "temperature": None},
                    )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ask_chat_mock.call_args.kwargs["temperature"], 0.2)

    def test_chat_accepts_temperature_zero(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            with patch("app.main.build_document_prompt", return_value=self._rag_context()):
                with patch(
                    "app.main.ask_chat",
                    return_value={
                        "status": "ok",
                        "provider": "ollama",
                        "model": "granite4.1:8b",
                        "temperature": 0.0,
                        "use_rag": True,
                        "answer": "ok",
                    },
                ) as ask_chat_mock:
                    response = TestClient(app).post(
                        "/chat",
                        json={"message": "hola", "provider": "ollama", "model": "granite4.1:8b", "temperature": 0.0},
                    )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ask_chat_mock.call_args.kwargs["temperature"], 0.0)

    def test_chat_accepts_temperature_point_two(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            with patch("app.main.build_document_prompt", return_value=self._rag_context()):
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
                ) as ask_chat_mock:
                    response = TestClient(app).post(
                        "/chat",
                        json={"message": "hola", "provider": "ollama", "model": "granite4.1:8b", "temperature": 0.2},
                    )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ask_chat_mock.call_args.kwargs["temperature"], 0.2)

    def test_chat_accepts_temperature_one(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            with patch("app.main.build_document_prompt", return_value=self._rag_context()):
                with patch(
                    "app.main.ask_chat",
                    return_value={
                        "status": "ok",
                        "provider": "ollama",
                        "model": "granite4.1:8b",
                        "temperature": 1.0,
                        "use_rag": True,
                        "answer": "ok",
                    },
                ) as ask_chat_mock:
                    response = TestClient(app).post(
                        "/chat",
                        json={"message": "hola", "provider": "ollama", "model": "granite4.1:8b", "temperature": 1.0},
                    )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ask_chat_mock.call_args.kwargs["temperature"], 1.0)

    def test_chat_accepts_top_p_and_propagates_it(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            with patch("app.main.build_document_prompt", return_value=self._rag_context()):
                with patch(
                    "app.main.ask_chat",
                    return_value={
                        "status": "ok",
                        "provider": "ollama",
                        "model": "granite4.1:8b",
                        "temperature": 0.2,
                        "top_p": 0.9,
                        "use_rag": True,
                        "answer": "ok",
                    },
                ) as ask_chat_mock:
                    response = TestClient(app).post(
                        "/chat",
                        json={"message": "hola", "provider": "ollama", "model": "granite4.1:8b", "top_p": 0.9},
                    )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ask_chat_mock.call_args.kwargs["top_p"], 0.9)

    def test_chat_uses_backend_default_top_p_when_missing(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            with patch("app.main.build_document_prompt", return_value=self._rag_context()):
                with patch(
                    "app.main.ask_chat",
                    return_value={
                        "status": "ok",
                        "provider": "ollama",
                        "model": "granite4.1:8b",
                        "temperature": 0.2,
                        "top_p": 0.9,
                        "use_rag": True,
                        "answer": "ok",
                    },
                ) as ask_chat_mock:
                    response = TestClient(app).post(
                        "/chat",
                        json={"message": "hola", "provider": "ollama", "model": "granite4.1:8b"},
                    )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ask_chat_mock.call_args.kwargs["top_p"], 0.9)

    def test_chat_accepts_top_k_and_propagates_it(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            with patch("app.main.build_document_prompt", return_value=self._rag_context()):
                with patch(
                    "app.main.ask_chat",
                    return_value={
                        "status": "ok",
                        "provider": "ollama",
                        "model": "granite4.1:8b",
                        "temperature": 0.2,
                        "top_p": 0.9,
                        "top_k": 40,
                        "use_rag": True,
                        "answer": "ok",
                    },
                ) as ask_chat_mock:
                    response = TestClient(app).post(
                        "/chat",
                        json={"message": "hola", "provider": "ollama", "model": "granite4.1:8b", "top_k": 40},
                    )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ask_chat_mock.call_args.kwargs["top_k"], 40)

    def test_chat_uses_backend_default_top_k_when_missing(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            with patch("app.main.build_document_prompt", return_value=self._rag_context()):
                with patch(
                    "app.main.ask_chat",
                    return_value={
                        "status": "ok",
                        "provider": "ollama",
                        "model": "granite4.1:8b",
                        "temperature": 0.2,
                        "top_p": 0.9,
                        "top_k": 40,
                        "use_rag": True,
                        "answer": "ok",
                    },
                ) as ask_chat_mock:
                    response = TestClient(app).post(
                        "/chat",
                        json={"message": "hola", "provider": "ollama", "model": "granite4.1:8b"},
                    )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(ask_chat_mock.call_args.kwargs["top_k"], 40)

    def test_chat_rejects_negative_temperature(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            response = TestClient(app).post(
                "/chat",
                json={"message": "hola", "provider": "ollama", "model": "granite4.1:8b", "temperature": -0.1},
            )

        self.assertEqual(response.status_code, 422)

    def test_chat_rejects_temperature_above_max(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            response = TestClient(app).post(
                "/chat",
                json={"message": "hola", "provider": "ollama", "model": "granite4.1:8b", "temperature": 1.6},
            )

        self.assertEqual(response.status_code, 422)

    def test_chat_rejects_top_p_above_max(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            response = TestClient(app).post(
                "/chat",
                json={"message": "hola", "provider": "ollama", "model": "granite4.1:8b", "top_p": 1.1},
            )

        self.assertEqual(response.status_code, 422)

    def test_chat_rejects_top_k_below_min(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            response = TestClient(app).post(
                "/chat",
                json={"message": "hola", "provider": "ollama", "model": "granite4.1:8b", "top_k": 0},
            )

        self.assertEqual(response.status_code, 422)

    def test_chat_rejects_top_k_above_max(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            response = TestClient(app).post(
                "/chat",
                json={"message": "hola", "provider": "ollama", "model": "granite4.1:8b", "top_k": 201},
            )

        self.assertEqual(response.status_code, 422)

    def test_chat_options_endpoint_returns_temperature_contract(self):
        response = TestClient(app).get("/api/chat/options")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["temperature"]["default"], 0.2)
        self.assertEqual(body["temperature"]["min"], 0.0)
        self.assertEqual(body["temperature"]["max"], 1.5)
        self.assertEqual(body["generation"]["temperature"]["default"], 0.2)
        self.assertEqual(body["generation"]["temperature"]["min"], 0.0)
        self.assertEqual(body["generation"]["temperature"]["max"], 1.5)
        self.assertEqual(body["generation"]["temperature"]["step"], 0.1)
        self.assertEqual(body["generation"]["top_p"]["default"], 0.9)
        self.assertEqual(body["generation"]["top_p"]["min"], 0.0)
        self.assertEqual(body["generation"]["top_p"]["max"], 1.0)
        self.assertEqual(body["generation"]["top_p"]["step"], 0.05)
        self.assertEqual(body["generation"]["top_k"]["default"], 40)
        self.assertEqual(body["generation"]["top_k"]["min"], 1)
        self.assertEqual(body["generation"]["top_k"]["max"], 200)
        self.assertEqual(body["generation"]["top_k"]["step"], 1)
        self.assertEqual(body["conversation"]["default"], 0)
        self.assertEqual(body["conversation"]["min"], 0)
        self.assertEqual(body["conversation"]["max"], 20)


if __name__ == "__main__":
    unittest.main()
