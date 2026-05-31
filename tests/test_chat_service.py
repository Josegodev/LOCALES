import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.chat import ChatDependencies, ChatService
from app.config import settings
from app.main import app
from app.schemas import ChatRequest, ChatResponse


class ChatServiceTests(unittest.TestCase):
    def _dependencies(self) -> ChatDependencies:
        return ChatDependencies(
            ask_chat=lambda *args, **kwargs: {"status": "ok"},
            build_document_prompt=lambda *args, **kwargs: {"status": "DISABLED", "prompt": "hola", "chunks": []},
            query_remote_rag=lambda *args, **kwargs: {"status": "DISABLED", "prompt": "hola", "chunks": []},
            resolve_provider_model=lambda provider, model: (provider or "ollama", model or "granite4.1:8b"),
            list_chat_runs=lambda *args, **kwargs: [],
            save_chat_run=lambda payload: None,
            log_event=lambda **kwargs: None,
            new_trace_id=lambda: "12345678123456781234567812345678",
            settings=settings,
            create_document_tool=lambda **kwargs: {"status": "ok"},
        )

    def test_chat_service_delegates_to_runtime_with_explicit_dependencies(self):
        dependencies = self._dependencies()
        request = ChatRequest(message="hola", provider="ollama", model="granite4.1:8b")
        expected_response = ChatResponse(
            trace_id="12345678123456781234567812345678",
            status="ok",
            provider="ollama",
            model="granite4.1:8b",
            temperature=0.2,
            use_rag=False,
            answer="ok",
            latency_ms=5,
        )

        with patch(
            "app.chat.service.chat_runtime_module.run_chat_request",
            return_value=expected_response,
        ) as run_chat_request_mock:
            service = ChatService(dependencies)
            response = service.run_chat_request(request, persist_trace=False)

        self.assertIs(response, expected_response)
        run_chat_request_mock.assert_called_once_with(
            request,
            persist_trace=False,
            dependencies=dependencies,
        )

    def test_chat_endpoint_keeps_contract_after_service_refactor(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            with patch("app.main.resolve_provider_model", return_value=("ollama", "granite4.1:8b")):
                with patch(
                    "app.main.ask_chat",
                    return_value={
                        "status": "ok",
                        "provider": "ollama",
                        "model": "granite4.1:8b",
                        "temperature": 0.2,
                        "use_rag": False,
                        "answer": "ok",
                    },
                ):
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
        self.assertEqual(payload["provider"], "ollama")
        self.assertEqual(payload["model"], "granite4.1:8b")
        self.assertEqual(payload["answer"], "ok")
        self.assertEqual(payload["retrieval_status"], "DISABLED")
        self.assertEqual(payload["answer_mode"], "standard_answer")
        self.assertFalse(payload["evidence_used"])
        self.assertFalse(payload["fallback_used"])
        self.assertTrue(payload["trace_id"])


if __name__ == "__main__":
    unittest.main()
