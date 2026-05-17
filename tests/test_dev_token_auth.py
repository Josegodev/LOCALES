import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class DevTokenAuthTests(unittest.TestCase):
    CHAT_PAYLOAD = {"message": "hola", "provider": "ollama", "model": "granite4.1:8b"}

    def test_health_remains_open_without_token(self):
        with patch("app.auth.settings.jose_dev_token", "test-dev-token"):
            response = TestClient(app).get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_startup_logs_chat_only_runtime_mode(self):
        with patch("app.main.settings.jose_dev_token", "test-dev-token"):
            with patch("app.main.get_logger") as get_logger:
                with TestClient(app):
                    pass

        get_logger.return_value.info.assert_any_call("JOSE_DEV_TOKEN configured: %s", "true")
        get_logger.return_value.info.assert_any_call("Chat-only runtime mode enabled for /chat and /health.")

    def test_chat_local_open_accepts_request_without_token(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
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
                    response = TestClient(app).post("/chat", json=self.CHAT_PAYLOAD)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], "ok")
        self.assertTrue(response.json()["trace_id"])

    def test_chat_bearer_required_without_token_returns_401(self):
        with patch("app.auth.settings.chat_auth_mode", "bearer_required"):
            with patch("app.auth.settings.jose_dev_token", "test-dev-token"):
                response = TestClient(app).post("/chat", json=self.CHAT_PAYLOAD)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"]["code"], "invalid_token")

    def test_chat_with_wrong_token_returns_401(self):
        with patch("app.auth.settings.chat_auth_mode", "bearer_required"):
            with patch("app.auth.settings.jose_dev_token", "test-dev-token"):
                response = TestClient(app).post(
                    "/chat",
                    headers={"Authorization": "Bearer wrong-token"},
                    json=self.CHAT_PAYLOAD,
                )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"]["code"], "invalid_token")

    def test_chat_with_correct_token_returns_success(self):
        with patch("app.auth.settings.chat_auth_mode", "bearer_required"):
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
                            json=self.CHAT_PAYLOAD,
                        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], "ok")

    def test_chat_disabled_returns_403(self):
        with patch("app.auth.settings.chat_auth_mode", "disabled"):
            response = TestClient(app).post("/chat", json=self.CHAT_PAYLOAD)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"]["code"], "chat_disabled")

    def test_chat_returns_500_when_server_token_missing(self):
        with patch("app.auth.settings.chat_auth_mode", "bearer_required"):
            with patch("app.auth.settings.jose_dev_token", None):
                response = TestClient(app).post(
                    "/chat",
                    headers={"Authorization": "Bearer anything"},
                    json=self.CHAT_PAYLOAD,
                )

        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json()["detail"]["code"], "dev_token_not_configured")

    def test_chat_trace_endpoint_is_open_in_local_open_mode(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            response = TestClient(app).get("/api/traces/chat?limit=1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_chat_runs_endpoint_is_open_in_local_open_mode(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            response = TestClient(app).get("/api/chat/runs?limit=1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_chat_without_model_returns_explicit_contract_error(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            response = TestClient(app).post("/chat", json={"message": "hola", "provider": "ollama"})

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"]["code"], "model_required")

    def test_chat_models_endpoint_returns_ollama_and_openai_options(self):
        with patch("app.main.list_chat_models", return_value=[
            {
                "provider": "ollama",
                "model": "granite4.1:8b",
                "label": "granite4.1:8b",
                "is_default": False,
            },
            {
                "provider": "openai",
                "model": "gpt-5.5",
                "label": "OpenAI / gpt-5.5",
                "is_default": False,
            },
        ]):
            response = TestClient(app).get("/api/models/chat")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["items"][0]["model"], "granite4.1:8b")
        self.assertEqual(response.json()["items"][1]["provider"], "openai")

    def test_chat_cors_allows_lan_dev_frontend_port(self):
        response = TestClient(app).options(
            "/chat",
            headers={
                "Origin": "http://192.168.1.20:4177",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["access-control-allow-origin"], "http://192.168.1.20:4177")

    def test_saved_eval_runs_endpoint_is_open_in_local_open_mode(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            response = TestClient(app).get("/api/evals/runs")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_frontend_files_do_not_reference_operational_token_name(self):
        frontend_js = Path("/home/jose-gonzalez-oliva/LOCALES/frontend/app.js").read_text(encoding="utf-8")
        frontend_html = Path("/home/jose-gonzalez-oliva/LOCALES/frontend/index.html").read_text(encoding="utf-8")

        self.assertNotIn("JOSE_DEV_TOKEN", frontend_js)
        self.assertNotIn("JOSE_DEV_TOKEN", frontend_html)

    def test_frontend_files_do_not_reference_telegram_endpoints(self):
        frontend_js = Path("/home/jose-gonzalez-oliva/LOCALES/frontend/app.js").read_text(encoding="utf-8")
        frontend_html = Path("/home/jose-gonzalez-oliva/LOCALES/frontend/index.html").read_text(encoding="utf-8")

        self.assertNotIn("/telegram/", frontend_js)
        self.assertNotIn("/api/evals/telegram", frontend_js)
        self.assertNotIn("/api/evals/chat/run", frontend_js)
        self.assertIn("/api/models/chat", frontend_js)
        self.assertIn("/api/models/chat", frontend_html)
        self.assertIn("NucleoChat", frontend_html)
        self.assertIn("POST /chat", frontend_html)
        self.assertNotIn("Telegram legacy", frontend_html)
        self.assertNotIn("Telegram Evals", frontend_html)

    def test_frontend_model_selector_does_not_hardcode_granite_option(self):
        frontend_html = Path("/home/jose-gonzalez-oliva/LOCALES/frontend/index.html").read_text(encoding="utf-8")

        self.assertNotIn('<option value="granite"', frontend_html)
        self.assertIn("Cargando modelos", frontend_html)

    def test_frontend_persists_provider_model_pair(self):
        frontend_js = Path("/home/jose-gonzalez-oliva/LOCALES/frontend/app.js").read_text(encoding="utf-8")

        self.assertIn("normalizeProviderModel", frontend_js)
        self.assertIn("locales.chatModelKey", frontend_js)
        self.assertIn("provider: selected.provider", frontend_js)
        self.assertIn("model: selected.model", frontend_js)


if __name__ == "__main__":
    unittest.main()
