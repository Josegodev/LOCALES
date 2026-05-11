import importlib
import io
import json
import os
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("TELEGRAM_ALLOWED_USER_IDS", "123")

from app import llm_client
from app.adapters.backend_client import BackendClientError
from app.adapters import openai_client
from app.main import _extract_chunk_response_data
from app.main import app
from app.observability import log_event, new_trace_id
from app.schemas import ChatResponse
from app.services import bot_service
from scripts import run_telegram

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
                        "use_rag": True,
                        "answer": "OK",
                    },
                ) as ask_chat_mock:
                    response = client.post(
                        "/chat",
                        json={
                            "message": "hola",
                            "temperature": 0.7,
                            "trace_id": REQUEST_ID,
                            "user_id": 123,
                            "chat_id": 456,
                        },
                    )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["provider"], "ollama")
        self.assertEqual(response.json()["temperature"], 0.7)
        self.assertTrue(response.json()["use_rag"])
        ask_chat_mock.assert_called_once_with(
            message="context prompt",
            provider="ollama",
            model="granite4.1:8b",
            max_tokens=None,
            temperature=0.7,
            use_rag=True,
        )

    def test_chat_endpoint_passes_openai_provider_to_llm(self):
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
                return_value={
                    "status": "ok",
                    "provider": "openai",
                    "model": "gpt-5.5",
                    "use_rag": True,
                    "answer": "OK",
                },
            ) as ask_chat_mock:
                response = client.post(
                    "/chat",
                    json={
                        "message": "hola",
                        "provider": "openai",
                        "model": "gpt-5.5",
                        "temperature": 0.4,
                        "trace_id": REQUEST_ID,
                        "user_id": 123,
                        "chat_id": 456,
                    },
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["provider"], "openai")
        self.assertEqual(response.json()["temperature"], 0.4)
        self.assertTrue(response.json()["use_rag"])
        ask_chat_mock.assert_called_once_with(
            message="context prompt",
            provider="openai",
            model="gpt-5.5",
            max_tokens=None,
            temperature=0.4,
            use_rag=True,
        )

    def test_chat_endpoint_passes_allowed_source_filenames_to_rag_builder(self):
        client = TestClient(app)

        with patch(
            "app.main.build_document_prompt",
            return_value={
                "status": "EVIDENCE_FOUND",
                "prompt": "context prompt",
                "chunks": [{"id": 346, "filename": "EVOLUTION_MAP.md", "text": "AgentRuntime"}],
            },
        ) as build_document_prompt_mock:
            with patch(
                "app.main.ask_chat",
                return_value={
                    "status": "ok",
                    "provider": "ollama",
                    "model": "granite4.1:8b",
                    "temperature": 0.2,
                    "use_rag": True,
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
                        "allowed_source_filenames": ["/tmp/docs/EVOLUTION_MAP.md", "ARCHITECTURE.md"],
                    },
                )

        self.assertEqual(response.status_code, 200)
        build_document_prompt_mock.assert_called_once_with(
            "hola",
            limit=3,
            allowed_source_filenames=["EVOLUTION_MAP.md", "ARCHITECTURE.md"],
        )

    def test_chat_endpoint_uses_active_document_context_for_short_follow_up(self):
        client = TestClient(app)

        with patch(
            "app.main.build_document_prompt",
            return_value={
                "status": "EVIDENCE_FOUND",
                "prompt": "context prompt",
                "query_original": "que son modelos?",
                "query_normalized": "que son modelos",
                "source_intent": "mixed",
                "selected_corpus": "documentos_oficiales",
                "active_document_id": 68,
                "active_document_title": "Attention is all yout need.pdf",
                "active_context_used": True,
                "active_context_reason": "short_or_ambiguous_query",
                "selected_filenames": ["Attention is all yout need.pdf"],
                "chunks": [{"id": 376, "document_id": 68, "filename": "Attention is all yout need.pdf", "text": "these models are superior"}],
            },
        ) as build_document_prompt_mock:
            with patch(
                "app.main.ask_chat",
                return_value={
                    "status": "ok",
                    "provider": "ollama",
                    "model": "granite4.1:8b",
                    "temperature": 0.2,
                    "use_rag": True,
                    "answer": "El documento usa modelos Transformer para traducción.",
                },
            ):
                response = client.post(
                    "/chat",
                    json={
                        "message": "que son modelos?",
                        "trace_id": REQUEST_ID,
                        "user_id": 123,
                        "chat_id": 456,
                        "active_document_id": 68,
                        "active_document_title": "Attention is all yout need.pdf",
                        "active_corpus": "documentos_oficiales",
                        "last_source_intent": "official_docs",
                    },
                )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["retrieval_status"], "EVIDENCE_FOUND")
        self.assertEqual(body["answer_mode"], "documentary_answer")
        self.assertTrue(body["active_context_used"])
        self.assertEqual(body["active_context_reason"], "short_or_ambiguous_query")
        self.assertEqual(body["selected_filenames"], ["Attention is all yout need.pdf"])
        build_document_prompt_mock.assert_called_once_with(
            "que son modelos?",
            limit=3,
            allowed_source_filenames=[],
            active_document_id=68,
            active_document_title="Attention is all yout need.pdf",
            allow_active_document_fallback=True,
            active_context_reason="short_or_ambiguous_query",
        )

    def test_chat_endpoint_disables_active_document_context_when_query_explicitly_switches_corpus(self):
        client = TestClient(app)

        with patch(
            "app.main.build_document_prompt",
            return_value={
                "status": "EVIDENCE_FOUND",
                "prompt": "context prompt",
                "query_original": "qué hace el orquestador de NUCLEO?",
                "query_normalized": "qué hace el orquestador de nucleo",
                "source_intent": "nucleo",
                "selected_corpus": "nucleo",
                "active_document_id": 68,
                "active_document_title": "Attention is all yout need.pdf",
                "active_context_used": False,
                "active_context_reason": "overridden_by_explicit_intent",
                "selected_filenames": ["orchestrator.md"],
                "chunks": [{"id": 3, "document_id": 3, "filename": "orchestrator.md", "text": "El orquestador coordina planner, policy y runtime."}],
            },
        ) as build_document_prompt_mock:
            with patch(
                "app.main.ask_chat",
                return_value={
                    "status": "ok",
                    "provider": "ollama",
                    "model": "granite4.1:8b",
                    "temperature": 0.2,
                    "use_rag": True,
                    "answer": "El orquestador coordina la ejecución en NUCLEO.",
                },
            ):
                response = client.post(
                    "/chat",
                    json={
                        "message": "qué hace el orquestador de NUCLEO?",
                        "trace_id": REQUEST_ID,
                        "user_id": 123,
                        "chat_id": 456,
                        "active_document_id": 68,
                        "active_document_title": "Attention is all yout need.pdf",
                        "active_corpus": "documentos_oficiales",
                        "last_source_intent": "official_docs",
                    },
                )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertFalse(body["active_context_used"])
        self.assertEqual(body["active_context_reason"], "overridden_by_explicit_intent")
        self.assertEqual(body["selected_corpus"], "nucleo")
        build_document_prompt_mock.assert_called_once_with(
            "qué hace el orquestador de NUCLEO?",
            limit=3,
            allowed_source_filenames=[],
            active_document_id=None,
            active_document_title=None,
            allow_active_document_fallback=False,
            active_context_reason="overridden_by_explicit_intent",
        )

    def test_chat_endpoint_disables_rag_when_requested(self):
        client = TestClient(app)

        with patch("app.main.build_document_prompt") as build_document_prompt_mock:
            with patch(
                "app.main.ask_chat",
                return_value={
                    "status": "ok",
                    "provider": "ollama",
                    "model": "granite4.1:8b",
                    "temperature": 0.2,
                    "use_rag": False,
                    "answer": "OK",
                },
            ) as ask_chat_mock:
                response = client.post(
                    "/chat",
                    json={
                        "message": "hola",
                        "use_rag": False,
                        "trace_id": REQUEST_ID,
                        "user_id": 123,
                        "chat_id": 456,
                    },
                )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["retrieval_status"], "DISABLED")
        self.assertEqual(response.json()["chunk_ids"], [])
        self.assertFalse(response.json()["use_rag"])
        build_document_prompt_mock.assert_not_called()
        ask_chat_mock.assert_called_once_with(
            message="hola",
            provider="ollama",
            model="granite4.1:8b",
            max_tokens=None,
            temperature=0.2,
            use_rag=False,
        )

    def test_resolve_provider_model_accepts_openai_gpt_55(self):
        provider, model = llm_client.resolve_provider_model("openai", "gpt-5.5")

        self.assertEqual(provider, "openai")
        self.assertEqual(model, "gpt-5.5")

    def test_resolve_provider_model_rejects_ollama_gpt_model(self):
        with self.assertRaises(llm_client.LLMClientError) as ctx:
            llm_client.resolve_provider_model("ollama", "gpt-5.5")

        self.assertEqual(ctx.exception.code, "invalid_provider_model_pair")

    def test_resolve_provider_model_accepts_ollama_granite(self):
        provider, model = llm_client.resolve_provider_model("ollama", "granite4.1:8b")

        self.assertEqual(provider, "ollama")
        self.assertEqual(model, "granite4.1:8b")

    def test_resolve_provider_model_rejects_openai_ollama_model(self):
        with self.assertRaises(llm_client.LLMClientError) as ctx:
            llm_client.resolve_provider_model("openai", "granite4.1:8b")

        self.assertEqual(ctx.exception.code, "invalid_provider_model_pair")

    def test_openai_client_accepts_supported_model(self):
        fake_response = SimpleNamespace(output_text="OK")

        class FakeResponses:
            def __init__(self):
                self.calls = []

            def create(self, **kwargs):
                self.calls.append(kwargs)
                return fake_response

        fake_responses = FakeResponses()
        fake_client = SimpleNamespace(responses=fake_responses)
        fake_settings = SimpleNamespace(
            openai_api_key="sk-test",
            llm_timeout_seconds=30,
            max_tokens=16,
            temperature=0.2,
        )

        with patch.object(openai_client, "OpenAI", return_value=fake_client) as openai_ctor:
            result = openai_client.ask_chat(
                "Responde solo: OK",
                model="gpt-5.5",
                settings_obj=fake_settings,
            )

        self.assertEqual(result["provider"], "openai")
        self.assertEqual(result["model"], "gpt-5.5")
        self.assertEqual(result["temperature"], 0.2)
        self.assertFalse(result["temperature_ignored"])
        self.assertEqual(result["answer"], "OK")
        self.assertEqual(fake_responses.calls[0]["model"], "gpt-5.5")
        self.assertEqual(fake_responses.calls[0]["temperature"], 0.2)
        openai_ctor.assert_called_once()

    def test_openai_client_rejects_unknown_model(self):
        fake_settings = SimpleNamespace(
            openai_api_key="sk-test",
            llm_timeout_seconds=30,
            max_tokens=16,
        )

        with patch.object(openai_client, "OpenAI") as openai_ctor:
            with self.assertRaises(openai_client.OpenAIClientError) as ctx:
                openai_client.ask_chat(
                    "Responde solo: OK",
                    model="modelo-inventado",
                    settings_obj=fake_settings,
                )

        self.assertEqual(ctx.exception.code, "llm_model_not_available")
        openai_ctor.assert_not_called()

    def test_openai_client_retries_without_temperature_when_rejected(self):
        fake_response = SimpleNamespace(output_text="OK")

        class FakeResponses:
            def __init__(self):
                self.calls = []

            def create(self, **kwargs):
                self.calls.append(kwargs)
                if len(self.calls) == 1:
                    raise RuntimeError("temperature not supported for this model")
                return fake_response

        fake_responses = FakeResponses()
        fake_client = SimpleNamespace(responses=fake_responses)
        fake_settings = SimpleNamespace(
            openai_api_key="sk-test",
            llm_timeout_seconds=30,
            max_tokens=16,
            temperature=0.2,
        )

        with patch.object(openai_client, "OpenAI", return_value=fake_client):
            result = openai_client.ask_chat(
                "Responde solo: OK",
                model="gpt-5.5",
                temperature=0.2,
                settings_obj=fake_settings,
            )

        self.assertEqual(result["temperature"], 0.2)
        self.assertTrue(result["temperature_ignored"])
        self.assertEqual(len(fake_responses.calls), 2)
        self.assertIn("temperature", fake_responses.calls[0])
        self.assertNotIn("temperature", fake_responses.calls[1])

    def test_select_temperature_accepts_valid_values(self):
        for raw_value, expected in [("0", 0.0), ("0.2", 0.2), ("1", 1.0)]:
            with self.subTest(raw_value=raw_value):
                with patch("builtins.input", return_value=raw_value):
                    self.assertEqual(run_telegram.select_temperature(), expected)

    def test_select_temperature_falls_back_on_invalid_values(self):
        for raw_value in ["texto", "-0.1", "1.1", "nan", "inf"]:
            with self.subTest(raw_value=raw_value):
                with patch("builtins.input", return_value=raw_value):
                    self.assertEqual(run_telegram.select_temperature(), 0.2)

    def test_select_use_rag_accepts_true_and_false_values(self):
        truthy_values = ["yes", "y", "si", "sí", "s", "true", "1"]
        falsy_values = ["no", "n", "false", "0"]

        for raw_value in truthy_values:
            with self.subTest(raw_value=raw_value):
                with patch("builtins.input", return_value=raw_value):
                    self.assertTrue(run_telegram.select_use_rag())

        for raw_value in falsy_values:
            with self.subTest(raw_value=raw_value):
                with patch("builtins.input", return_value=raw_value):
                    self.assertFalse(run_telegram.select_use_rag())

    def test_select_use_rag_defaults_to_true_on_invalid_or_empty_input(self):
        for raw_value in ["", "tal vez", "maybe"]:
            with self.subTest(raw_value=raw_value):
                with patch("builtins.input", return_value=raw_value):
                    self.assertTrue(run_telegram.select_use_rag())

    def test_chat_response_accepts_chunk_ids_and_source_filenames_separately_from_chunks(self):
        response = ChatResponse(
            status="ok",
            provider="ollama",
            model="granite4.1:8b",
            temperature=0.2,
            answer="OK",
            latency_ms=12,
            retrieval_status="EVIDENCE_FOUND",
            chunks=["Fragmento A", "Fragmento B"],
            chunk_ids=[346, 206, 262],
            source_filenames=["ARCHITECTURE.md", "POLICY.md"],
        )

        self.assertEqual(response.chunks, ["Fragmento A", "Fragmento B"])
        self.assertEqual(response.chunk_ids, [346, 206, 262])
        self.assertEqual(response.source_filenames, ["ARCHITECTURE.md", "POLICY.md"])

    def test_chat_endpoint_returns_chunk_ids_and_source_filenames_without_breaking_response_validation(self):
        client = TestClient(app)

        with patch(
            "app.main.build_document_prompt",
            return_value={
                "status": "EVIDENCE_FOUND",
                "prompt": "context prompt",
                "chunks": [
                    {"id": 346, "text": "NUCLEO es un runtime local.", "filename": "ARCHITECTURE.md"},
                    {"id": 206, "text": "Usa herramientas registradas.", "source_path": "/tmp/docs/ARCHITECTURE.md"},
                    {"id": 262, "text": "La política controla la ejecución.", "metadata": {"source_path": "/srv/docs/POLICY.md"}},
                ],
            },
        ):
            with patch(
                "app.main.ask_chat",
                return_value={
                    "status": "ok",
                    "provider": "ollama",
                    "model": "granite4.1:8b",
                    "temperature": 0.2,
                    "use_rag": True,
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
        self.assertEqual(body["source_filenames"], ["ARCHITECTURE.md", "POLICY.md"])
        self.assertEqual(body["temperature"], 0.2)
        self.assertTrue(body["use_rag"])
        self.assertEqual(
            body["chunks"],
            [
                "NUCLEO es un runtime local.",
                "Usa herramientas registradas.",
                "La política controla la ejecución.",
            ],
        )

    def test_extract_chunk_response_data_does_not_store_chunk_text_as_source_filename(self):
        chunk_texts, chunk_ids, document_ids, source_filenames = _extract_chunk_response_data(
            [
                {
                    "id": 346,
                    "text": "Contenido completo del chunk que no debe aparecer como filename.",
                }
            ]
        )

        self.assertEqual(
            chunk_texts,
            ["Contenido completo del chunk que no debe aparecer como filename."],
        )
        self.assertEqual(chunk_ids, [346])
        self.assertEqual(document_ids, [])
        self.assertEqual(source_filenames, [])

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
                    "provider": "ollama",
                    "model": "granite4.1:8b",
                    "temperature": 0.2,
                    "use_rag": True,
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
        self.assertEqual(chat_event["temperature"], 0.2)
        self.assertTrue(chat_event["use_rag"])
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
            with patch(
                "app.main.ask_chat",
                return_value={
                    "status": "ok",
                    "provider": "ollama",
                    "model": "granite4.1:8b",
                    "temperature": 0.2,
                    "use_rag": True,
                    "answer": "Parece una consulta sin contexto documental local, pero en términos generales puedo ayudarte.",
                },
            ) as ask_chat_mock:
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
        self.assertTrue(body["answer"].startswith("No he encontrado evidencia suficiente en los documentos cargados."))
        self.assertEqual(body["retrieval_status"], "NO_EVIDENCE_FOR_ANSWER")
        self.assertEqual(body["answer_mode"], "model_internal_answer")
        self.assertEqual(body["chunk_ids"], [])
        self.assertEqual(body["document_ids"], [])
        self.assertEqual(body["source_filenames"], [])
        self.assertFalse(body["evidence_used"])
        self.assertTrue(body["fallback_used"])
        self.assertEqual(
            body["warnings"],
            ["Respuesta generada sin evidencia documental local. Puede requerir verificación."],
        )
        ask_chat_mock.assert_called_once()

    def test_chat_endpoint_strips_no_evidence_marker_from_documentary_answer(self):
        client = TestClient(app)
        output = io.StringIO()

        with redirect_stdout(output):
            with patch(
                "app.main.build_document_prompt",
                return_value={
                    "status": "EVIDENCE_FOUND",
                    "prompt": "context prompt",
                    "query_original": 'que significa "attention"?',
                    "query_normalized": "que significa attention",
                    "quoted_terms": ["attention"],
                    "chunk_ids": [375],
                    "document_ids": [68],
                    "source_filenames": ["Attention is all yout need.pdf"],
                    "chunks": [{"id": 375, "document_id": 68, "filename": "Attention is all yout need.pdf", "text": "attention is all you need"}],
                },
            ):
                with patch(
                    "app.main.ask_chat",
                    return_value={
                        "status": "ok",
                        "provider": "ollama",
                        "model": "granite4.1:8b",
                        "temperature": 0.2,
                        "use_rag": True,
                        "answer": (
                            "El paper define attention como un mecanismo para relacionar posiciones.\n"
                            "NO_EVIDENCE_FOR_ANSWER\n"
                            "No hay evidencia documental suficiente para responder."
                        ),
                    },
                ):
                    response = client.post(
                        "/chat",
                        json={
                            "message": 'que significa "attention"?',
                            "trace_id": REQUEST_ID,
                            "user_id": 123,
                            "chat_id": 456,
                        },
                    )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["retrieval_status"], "EVIDENCE_FOUND")
        self.assertEqual(body["answer_mode"], "documentary_answer")
        self.assertTrue(body["evidence_used"])
        self.assertFalse(body["fallback_used"])
        self.assertIn("mecanismo", body["answer"])
        self.assertNotIn("NO_EVIDENCE_FOR_ANSWER", body["answer"])
        self.assertNotIn("No hay evidencia documental suficiente", body["answer"])

        events = [
            json.loads(line)
            for line in output.getvalue().splitlines()
            if line.strip().startswith("{")
        ]
        chat_event = next(event for event in events if event["component"] == "fastapi.chat")
        self.assertEqual(chat_event["trace_id"], REQUEST_ID)
        self.assertEqual(chat_event["query_original"], 'que significa "attention"?')
        self.assertEqual(chat_event["retrieval_status"], "EVIDENCE_FOUND")
        self.assertEqual(chat_event["chunks_found"], 1)
        self.assertEqual(chat_event["chunk_ids"], [375])
        self.assertEqual(chat_event["answer_mode"], "documentary_answer")
        self.assertNotIn("NO_EVIDENCE_FOR_ANSWER", chat_event["final_message_preview"])

    def test_chat_endpoint_converts_marker_only_llm_answer_to_no_evidence(self):
        client = TestClient(app)

        with patch(
            "app.main.build_document_prompt",
            return_value={
                "status": "EVIDENCE_FOUND",
                "prompt": "context prompt",
                "query_original": "¿que es un mecanismo de atencion?",
                "query_normalized": "que es un mecanismo de atencion",
                "chunk_ids": [375],
                "document_ids": [68],
                "source_filenames": ["Attention is all yout need.pdf"],
                "chunks": [
                    {
                        "id": 375,
                        "document_id": 68,
                        "filename": "Attention is all yout need.pdf",
                        "text": "Attention mechanism allows the model to focus on relevant positions.",
                    }
                ],
            },
        ):
            with patch(
                "app.main.ask_chat",
                side_effect=[
                    {
                        "status": "ok",
                        "provider": "openai",
                        "model": "gpt-5.5",
                        "temperature": 0.5,
                        "use_rag": True,
                        "answer": "NO_EVIDENCE_FOR_ANSWER\nNo hay evidencia documental suficiente para responder.",
                    },
                    {
                        "status": "ok",
                        "provider": "openai",
                        "model": "gpt-5.5",
                        "temperature": 0.5,
                        "use_rag": True,
                        "answer": "Un mecanismo de atención permite al modelo centrarse en partes relevantes de la entrada.",
                    },
                ],
            ):
                response = client.post(
                    "/chat",
                    json={
                        "message": "¿que es un mecanismo de atencion?",
                        "trace_id": REQUEST_ID,
                        "user_id": 123,
                        "chat_id": 456,
                        "provider": "openai",
                        "model": "gpt-5.5",
                        "temperature": 0.5,
                    },
                )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["retrieval_status"], "NO_EVIDENCE_FOR_ANSWER")
        self.assertEqual(body["answer_mode"], "model_internal_answer")
        self.assertTrue(body["answer"].startswith("No he encontrado evidencia suficiente en los documentos cargados."))
        self.assertEqual(body["chunk_ids"], [])
        self.assertEqual(body["document_ids"], [])
        self.assertEqual(body["source_filenames"], [])
        self.assertFalse(body["evidence_used"])
        self.assertTrue(body["fallback_used"])
        self.assertEqual(
            body["warnings"],
            ["Respuesta generada sin evidencia documental local. Puede requerir verificación."],
        )

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
            with patch(
                "app.main.ask_chat",
                return_value={
                    "status": "ok",
                    "provider": "ollama",
                    "model": "granite4.1:8b",
                    "temperature": 0.2,
                    "use_rag": True,
                    "answer": "No conozco ese término en los documentos, pero en general parece un identificador artificial de prueba.",
                },
            ) as ask_chat_mock:
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
        ask_chat_mock.assert_called_once()
        body = response.json()
        self.assertTrue(body["answer"].startswith("No he encontrado evidencia suficiente en los documentos cargados."))
        self.assertEqual(body["retrieval_status"], "NO_EVIDENCE_FOR_ANSWER")
        self.assertEqual(body["answer_mode"], "model_internal_answer")
        self.assertEqual(body["chunk_ids"], [])
        self.assertEqual(body["source_filenames"], [])
        self.assertFalse(body["evidence_used"])
        self.assertTrue(body["fallback_used"])

    def test_chat_forces_no_evidence_for_missing_meaningful_alpha_term(self):
        client = TestClient(app)

        with patch(
            "app.main.build_document_prompt",
            return_value={
                "status": "EVIDENCE_FOUND",
                "prompt": "context prompt",
                "chunks": [
                    {
                        "id": "chunk-1",
                        "text": "Documento sobre attention y transformers.",
                    }
                ],
            },
        ):
            with patch(
                "app.main.ask_chat",
                return_value={
                    "status": "ok",
                    "provider": "ollama",
                    "model": "granite4.1:8b",
                    "temperature": 0.2,
                    "use_rag": True,
                    "answer": "No puedo verificar ese término en los documentos, pero parece un token inventado para una prueba.",
                },
            ) as ask_chat_mock:
                response = client.post(
                    "/chat",
                    json={
                        "message": "qué dice el PDF sobre una cosa que no existe xyzabc?",
                        "trace_id": REQUEST_ID,
                        "user_id": 123,
                        "chat_id": 456,
                    },
                )

        self.assertEqual(response.status_code, 200)
        ask_chat_mock.assert_called_once()
        body = response.json()
        self.assertTrue(body["answer"].startswith("No he encontrado evidencia suficiente en los documentos cargados."))
        self.assertEqual(body["retrieval_status"], "NO_EVIDENCE_FOR_ANSWER")
        self.assertEqual(body["answer_mode"], "model_internal_answer")
        self.assertEqual(body["chunk_ids"], [])
        self.assertEqual(body["source_filenames"], [])
        self.assertFalse(body["evidence_used"])
        self.assertTrue(body["fallback_used"])

    def test_chat_active_context_without_chunks_sets_specific_warning_and_flags(self):
        client = TestClient(app)

        with patch(
            "app.main.build_document_prompt",
            return_value={
                "status": "NO_EVIDENCE",
                "prompt": "unused",
                "chunks": [],
                "active_document_id": 68,
                "active_document_title": "Attention is all yout need.pdf",
                "active_context_used": True,
                "active_context_reason": "short_or_ambiguous_query",
                "query_expansion_used": True,
                "query_expansion_reason": "domain_dictionary",
                "expanded_query_terms": ["attention", "self-attention", "attention mechanism"],
            },
        ):
            with patch(
                "app.main.ask_chat",
                return_value={
                    "status": "ok",
                    "provider": "openai",
                    "model": "gpt-5.5",
                    "temperature": 0.5,
                    "use_rag": True,
                    "answer": "En términos generales, un mecanismo de atención permite ponderar partes relevantes de la entrada.",
                },
            ):
                response = client.post(
                    "/chat",
                    json={
                        "message": "¿que es un mecanismo de atencion?",
                        "trace_id": REQUEST_ID,
                        "user_id": 123,
                        "chat_id": 456,
                        "provider": "openai",
                        "model": "gpt-5.5",
                    },
                )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["active_context_used"])
        self.assertEqual(body["chunk_ids"], [])
        self.assertFalse(body["evidence_used"])
        self.assertTrue(body["fallback_used"])
        self.assertTrue(body["query_expansion_used"])
        self.assertEqual(body["query_expansion_reason"], "domain_dictionary")
        self.assertIn("attention", body["expanded_query_terms"])
        self.assertEqual(
            body["warnings"],
            [
                "Contexto activo detectado, pero sin chunks documentales suficientes. "
                "Respuesta generada con conocimiento general del modelo."
            ],
        )

    def test_telegram_chat_error_is_controlled(self):
        sent_messages: list[tuple[int, str]] = []

        def fake_send(chat_id: int, text: str) -> None:
            sent_messages.append((chat_id, text))

        def failing_chat(*args, **kwargs) -> dict:
            raise BackendClientError("llm_timeout", "backend_chat_error", 504)

        with patch("app.services.bot_service.write_telegram_conversation_record"):
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
