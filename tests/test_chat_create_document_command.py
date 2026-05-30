import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app


class ChatCreateDocumentCommandTests(unittest.TestCase):
    NORMAL_CHAT_PAYLOAD = {
        "message": "Que es RAG?",
        "provider": "ollama",
        "model": "granite4.1:8b",
        "use_rag": True,
    }
    CREATE_DOCUMENT_PAYLOAD = {
        "message": "/creardoc Crea un documento explicando que es RAG para alumnos no tecnicos",
        "provider": "ollama",
        "model": "granite4.1:8b",
        "temperature": 0.2,
        "use_rag": True,
    }

    def _successful_rag_context(self) -> dict:
        return {
            "status": "EVIDENCE_FOUND",
            "prompt": "context prompt",
            "chunks": [],
            "warnings": [],
            "query_original": self.NORMAL_CHAT_PAYLOAD["message"],
            "query_normalized": self.NORMAL_CHAT_PAYLOAD["message"].strip().casefold(),
            "query_terms": [],
            "quoted_terms": [],
            "source_intent": "mixed",
            "selected_corpus": "mixed",
            "candidate_filenames": [],
            "selected_filenames": [],
            "scores": [],
        }

    def test_normal_message_keeps_normal_chat_flow(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            with patch("app.main.build_document_prompt", return_value=self._successful_rag_context()) as build_prompt_mock:
                with patch(
                    "app.main.ask_chat",
                    return_value={
                        "status": "ok",
                        "provider": "ollama",
                        "model": "granite4.1:8b",
                        "temperature": 0.2,
                        "use_rag": True,
                        "answer": "RAG combina recuperacion y generacion.",
                    },
                ):
                    response = TestClient(app).post("/chat", json=self.NORMAL_CHAT_PAYLOAD)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["answer"], "RAG combina recuperacion y generacion.")
        build_prompt_mock.assert_called_once()

    def test_creardoc_without_instruction_returns_missing_instruction(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            response = TestClient(app).post(
                "/chat",
                json={
                    "message": "/creardoc",
                    "provider": "ollama",
                    "model": "granite4.1:8b",
                    "use_rag": False,
                },
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"]["code"], "missing_instruction")

    def test_creardoc_calls_tool_and_bypasses_rag(self):
        create_document_tool_mock = AsyncMock(
            return_value={
                "status": "ok",
                "tool_called": "create_document",
                "tool_result_status": "ok",
                "document_path": "outputs/documents/doc.md",
                "document_filename": "doc.md",
                "chars_written": 123,
                "overwrite_requested": False,
                "overwrite_applied": False,
                "overwrite_reason": "unique_trace_filename_policy",
            }
        )
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            with patch("app.main.build_document_prompt") as build_prompt_mock:
                with patch(
                    "app.main.ask_chat",
                    return_value={
                        "status": "ok",
                        "provider": "ollama",
                        "model": "granite4.1:8b",
                        "temperature": 0.2,
                        "use_rag": False,
                        "answer": "# RAG\n\nContenido en Markdown.",
                        "prompt_eval_count": 20,
                        "eval_count": 40,
                    },
                ) as ask_chat_mock:
                    with patch("app.main.create_document_tool", create_document_tool_mock):
                        with patch("app.chat_runtime.create_document_tool", create_document_tool_mock):
                            response = TestClient(app).post("/chat", json=self.CREATE_DOCUMENT_PAYLOAD)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["tool_called"], "create_document")
        self.assertEqual(body["command"], "creardoc")
        self.assertEqual(body["document_path"], "outputs/documents/doc.md")
        self.assertEqual(body["document_filename"], "doc.md")
        self.assertFalse(body["use_rag"])
        self.assertFalse(body["overwrite_requested"])
        self.assertFalse(body["overwrite_applied"])
        self.assertEqual(body["overwrite_reason"], "unique_trace_filename_policy")
        build_prompt_mock.assert_not_called()
        create_document_tool_mock.assert_awaited_once()
        ask_chat_kwargs = ask_chat_mock.call_args.kwargs
        self.assertFalse(ask_chat_kwargs["use_rag"])
        self.assertIn("Markdown", ask_chat_kwargs["system_prompt"])

    def test_creardoc_persists_command_metadata_in_trace(self):
        create_document_tool_mock = AsyncMock(
            return_value={
                "status": "ok",
                "tool_called": "create_document",
                "tool_result_status": "ok",
                "document_path": "outputs/documents/doc.md",
                "document_filename": "doc.md",
                "chars_written": 456,
                "overwrite_requested": False,
                "overwrite_applied": False,
                "overwrite_reason": "unique_trace_filename_policy",
            }
        )
        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "CHAT_RUNS"
            with patch("app.auth.settings.chat_auth_mode", "local_open"):
                with patch("app.main.settings.chat_runs_path", str(runs_dir)):
                    with patch("app.observability.chat_runs.settings.chat_runs_path", str(runs_dir)):
                        with patch(
                            "app.main.ask_chat",
                            return_value={
                                "status": "ok",
                                "provider": "ollama",
                                "model": "granite4.1:8b",
                                "temperature": 0.2,
                                "use_rag": False,
                                "answer": "# Docker\n\nContenido.",
                                "prompt_eval_count": 10,
                                "eval_count": 20,
                            },
                        ):
                            with patch("app.main.create_document_tool", create_document_tool_mock):
                                with patch("app.chat_runtime.create_document_tool", create_document_tool_mock):
                                    response = TestClient(app).post("/chat", json=self.CREATE_DOCUMENT_PAYLOAD)

            self.assertEqual(response.status_code, 200)
            payload = json.loads(next(runs_dir.glob("*.json")).read_text(encoding="utf-8"))

        self.assertEqual(payload["source"], "frontend")
        self.assertEqual(payload["command"], "creardoc")
        self.assertEqual(payload["tool_called"], "create_document")
        self.assertEqual(payload["tool_result_status"], "ok")
        self.assertEqual(payload["document_path"], "outputs/documents/doc.md")
        self.assertEqual(payload["document_filename"], "doc.md")
        self.assertEqual(payload["overwrite_reason"], "unique_trace_filename_policy")


if __name__ == "__main__":
    unittest.main()
