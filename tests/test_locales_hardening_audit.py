import importlib
import io
import json
import os
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("TELEGRAM_ALLOWED_USER_IDS", "123")

from app import llm_client
from app.adapters.backend_client import BackendClientError
from app.main import app
from app.observability import log_event, new_trace_id
from app.schemas import ChatResponse
from app.services import bot_service

REQUEST_ID = "12345678123456781234567812345678"


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self) -> dict:
        return self._payload


class LocalesHardeningAuditTests(unittest.TestCase):
    def test_trace_id_generation_returns_hex_uuid(self):
        trace_id = new_trace_id()

        self.assertEqual(len(trace_id), 32)
        int(trace_id, 16)

    def test_ollama_timeout_uses_environment_backed_setting(self):
        fake_response = FakeResponse(
            200,
            {"choices": [{"message": {"content": "# Markdown"}}]},
        )

        with patch.object(llm_client.settings, "ollama_base_url", "http://127.0.0.1:11434"):
            with patch.object(llm_client.settings, "ollama_model", "modelo-ollama-local"):
                with patch.object(llm_client.settings, "ollama_timeout_seconds", 7):
                    with patch.object(llm_client.requests, "post", return_value=fake_response) as post:
                        result = llm_client.generate_markdown("Haz un documento", REQUEST_ID)

        self.assertEqual(result, "# Markdown")
        self.assertEqual(
            post.call_args.args[0],
            "http://127.0.0.1:11434/v1/chat/completions",
        )
        self.assertEqual(post.call_args.kwargs["json"]["model"], "modelo-ollama-local")
        self.assertEqual(post.call_args.kwargs["timeout"], 7)

    def test_invalid_ollama_response_raises_explicit_error(self):
        fake_response = FakeResponse(200, {"unexpected": "shape"})

        with patch.object(llm_client.requests, "post", return_value=fake_response):
            with self.assertRaises(llm_client.LLMClientError) as ctx:
                llm_client.generate_markdown("Haz un documento", REQUEST_ID)

        self.assertEqual(ctx.exception.code, "llm_invalid_response")

    def test_chat_endpoint_uses_ollama_facade(self):
        client = TestClient(app)
        output = io.StringIO()

        with redirect_stdout(output):
            with patch(
                "app.main.build_document_prompt",
                return_value={
                    "status": "EVIDENCE_FOUND",
                    "prompt": "context prompt",
                    "chunks": [{"id": "chunk-1"}],
                },
            ):
                with patch(
                    "app.main.ask_chat",
                    return_value={
                        "status": "ok",
                        "model": "granite4.1:8b",
                        "answer": "OK",
                    },
                ) as ask_chat_mock:
                    response = client.post(
                        "/chat",
                        json={
                            "message": "hola",
                            "trace_id": REQUEST_ID,
                            "user_id": 123,
                            "chat_id": 456,
                        },
                    )

        self.assertEqual(response.status_code, 200)
        ask_chat_mock.assert_called_once_with(
            message="context prompt",
            model=None,
            max_tokens=None,
            temperature=None,
        )

    def test_chat_response_accepts_chunk_ids_separately_from_chunks(self):
        response = ChatResponse(
            status="ok",
            model="granite4.1:8b",
            answer="OK",
            latency_ms=12,
            retrieval_status="EVIDENCE_FOUND",
            chunks=["Fragmento A", "Fragmento B"],
            chunk_ids=[346, 206, 262],
        )

        self.assertEqual(response.chunks, ["Fragmento A", "Fragmento B"])
        self.assertEqual(response.chunk_ids, [346, 206, 262])

    def test_chat_endpoint_returns_chunk_ids_without_breaking_response_validation(self):
        client = TestClient(app)

        with patch(
            "app.main.build_document_prompt",
            return_value={
                "status": "EVIDENCE_FOUND",
                "prompt": "context prompt",
                "chunks": [
                    {"id": 346, "text": "NUCLEO es un runtime local."},
                    {"id": 206, "text": "Usa herramientas registradas."},
                    {"id": 262, "text": "La política controla la ejecución."},
                ],
            },
        ):
            with patch(
                "app.main.ask_chat",
                return_value={
                    "status": "ok",
                    "model": "granite4.1:8b",
                    "answer": "NUCLEO es un runtime local con política explícita.",
                },
            ):
                response = client.post(
                    "/chat",
                    json={
                        "message": "Busca evidencia sobre que es nucleo",
                        "trace_id": REQUEST_ID,
                        "chat_id": 6490442655,
                        "user_id": 6490442655,
                    },
                )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["retrieval_status"], "EVIDENCE_FOUND")
        self.assertEqual(body["chunk_ids"], [346, 206, 262])
        self.assertEqual(
            body["chunks"],
            [
                "NUCLEO es un runtime local.",
                "Usa herramientas registradas.",
                "La política controla la ejecución.",
            ],
        )

    def test_chat_endpoint_does_not_import_lmstudio_directly(self):
        source = Path("/home/jose-gonzalez-oliva/LOCALES/app/main.py").read_text(encoding="utf-8")

        self.assertNotIn("from app.lmstudio_client import", source)
        self.assertNotIn("ask_lmstudio(", source)

    def test_chat_endpoint_returns_controlled_ollama_error(self):
        client = TestClient(app)

        with patch(
            "app.main.build_document_prompt",
            return_value={
                "status": "EVIDENCE_FOUND",
                "prompt": "context prompt",
                "chunks": [{"id": "chunk-1"}],
            },
        ):
            with patch(
                "app.main.ask_chat",
                side_effect=llm_client.LLMClientError("llm_timeout", "timeout interno"),
            ):
                response = client.post(
                    "/chat",
                    json={
                        "message": "hola",
                        "trace_id": REQUEST_ID,
                        "user_id": 123,
                        "chat_id": 456,
                    },
                )

        self.assertEqual(response.status_code, 504)
        self.assertEqual(response.json()["detail"]["code"], "llm_timeout")
        self.assertEqual(response.json()["detail"]["trace_id"], REQUEST_ID)
        self.assertEqual(
            response.json()["detail"]["message"],
            "No se pudo generar respuesta del modelo.",
        )

    def test_chat_trace_id_appears_in_structured_logs(self):
        client = TestClient(app)
        output = io.StringIO()

        with redirect_stdout(output):
            with patch(
                "app.main.build_document_prompt",
                return_value={
                    "status": "EVIDENCE_FOUND",
                    "prompt": "context prompt",
                    "chunks": [{"id": "chunk-1"}],
                },
            ):
                with patch(
                    "app.main.ask_chat",
                    return_value={
                        "status": "ok",
                        "model": "granite4.1:8b",
                        "answer": "OK",
                    },
                ):
                    response = client.post(
                        "/chat",
                        json={
                            "message": "hola",
                            "trace_id": REQUEST_ID,
                            "user_id": 123,
                            "chat_id": 456,
                        },
                    )

        self.assertEqual(response.status_code, 200)
        events = [
            json.loads(line)
            for line in output.getvalue().splitlines()
            if line.strip().startswith("{")
        ]
        chat_event = next(event for event in events if event["component"] == "fastapi.chat")
        self.assertEqual(chat_event["trace_id"], REQUEST_ID)
        self.assertEqual(chat_event["chat_id"], 456)
        self.assertEqual(chat_event["user_id"], 123)
        self.assertEqual(chat_event["model"], "granite4.1:8b")
        self.assertEqual(chat_event["status"], "ok")
        self.assertIn("latency_ms", chat_event)

    def test_chat_no_evidence_response_contains_exact_marker(self):
        client = TestClient(app)

        with patch(
            "app.main.build_document_prompt",
            return_value={
                "status": "NO_EVIDENCE",
                "prompt": "unused",
                "chunks": [],
            },
        ):
            response = client.post(
                "/chat",
                json={
                    "message": "consulta sin evidencia",
                    "trace_id": REQUEST_ID,
                    "user_id": 123,
                    "chat_id": 456,
                },
            )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["answer"].startswith("NO_EVIDENCE_FOR_ANSWER"))
        self.assertEqual(body["retrieval_status"], "NO_EVIDENCE")

    def test_chat_forces_no_evidence_when_anchor_term_is_absent_from_chunks(self):
        client = TestClient(app)

        with patch(
            "app.main.build_document_prompt",
            return_value={
                "status": "EVIDENCE_FOUND",
                "prompt": "context prompt",
                "chunks": [
                    {
                        "id": "chunk-1",
                        "text": "Documento sobre NUCLEO y arquitectura modular.",
                    }
                ],
            },
        ):
            with patch("app.main.ask_chat") as ask_chat_mock:
                response = client.post(
                    "/chat",
                    json={
                        "message": "Busca HARDENING_NONCE_A_7F3K91X en el corpus",
                        "trace_id": REQUEST_ID,
                        "user_id": 123,
                        "chat_id": 456,
                    },
                )

        self.assertEqual(response.status_code, 200)
        ask_chat_mock.assert_not_called()
        body = response.json()
        self.assertTrue(body["answer"].startswith("NO_EVIDENCE_FOR_ANSWER"))
        self.assertEqual(body["retrieval_status"], "NO_EVIDENCE")

    def test_telegram_chat_error_is_controlled(self):
        sent_messages: list[tuple[int, str]] = []

        def fake_send(chat_id: int, text: str) -> None:
            sent_messages.append((chat_id, text))

        def failing_chat(*args, **kwargs) -> dict:
            raise BackendClientError("llm_timeout", "backend_chat_error", 504)

        bot_service.handle_message(
            {
                "chat": {"id": 456},
                "from": {"id": 123},
                "text": "hola",
            },
            send_message_fn=fake_send,
            ask_chat_fn=failing_chat,
        )

        self.assertEqual(len(sent_messages), 1)
        self.assertEqual(sent_messages[0][0], 456)
        self.assertIn("No se pudo procesar el mensaje.", sent_messages[0][1])
        self.assertIn("request_id=", sent_messages[0][1])
        self.assertNotIn("Traceback", sent_messages[0][1])

    def test_logs_are_structured_json(self):
        output = io.StringIO()

        with redirect_stdout(output):
            log_event(
                component="test.component",
                event="test.event",
                trace_id=REQUEST_ID,
                status="ok",
            )

        event = json.loads(output.getvalue().strip())
        self.assertEqual(event["component"], "test.component")
        self.assertEqual(event["event"], "test.event")
        self.assertEqual(event["trace_id"], REQUEST_ID)
        self.assertEqual(event["request_id"], REQUEST_ID)
        self.assertEqual(event["status"], "ok")

    def test_new_modules_import_without_circular_dependencies(self):
        modules = [
            "app.adapters.backend_client",
            "app.adapters.ollama_client",
            "app.adapters.telegram_api",
            "app.contracts.bot",
            "app.observability.logging",
            "app.observability.trace",
            "app.services.bot_service",
        ]

        for module_name in modules:
            imported = importlib.import_module(module_name)
            self.assertIsNotNone(imported)


if __name__ == "__main__":
    unittest.main()
