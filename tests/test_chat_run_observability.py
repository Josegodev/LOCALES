import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class ChatRunObservabilityTests(unittest.TestCase):
    CHAT_PAYLOAD = {
        "message": "Que es un transformer?",
        "provider": "ollama",
        "model": "granite4.1:8b",
        "use_rag": True,
    }

    def _successful_rag_context(self) -> dict:
        return {
            "status": "EVIDENCE_FOUND",
            "prompt": "context prompt",
            "chunks": [
                {
                    "text": "Transformer attention context",
                    "id": 1,
                    "document_id": 2,
                    "filename": "doc.pdf",
                    "score": 1,
                }
            ],
            "warnings": [],
            "query_original": self.CHAT_PAYLOAD["message"],
            "query_normalized": self.CHAT_PAYLOAD["message"].strip().casefold(),
            "query_terms": [],
            "quoted_terms": [],
            "source_intent": "mixed",
            "selected_corpus": "mixed",
            "candidate_filenames": ["doc.pdf"],
            "selected_filenames": ["doc.pdf"],
            "scores": [1],
        }

    def test_post_chat_persists_chat_run_line(self):
        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "CHAT_RUNS"
            with patch("app.auth.settings.chat_auth_mode", "local_open"):
                with patch("app.main.settings.chat_runs_path", str(runs_dir)):
                    with patch("app.observability.chat_runs.settings.chat_runs_path", str(runs_dir)):
                        with patch("app.main.build_document_prompt", return_value=self._successful_rag_context()):
                            with patch(
                                "app.main.ask_chat",
                                return_value={
                                    "status": "ok",
                                    "provider": "ollama",
                                    "model": "granite4.1:8b",
                                    "temperature": 0.2,
                                    "use_rag": True,
                                    "answer": "Transformer basado en attention.",
                                    "prompt_eval_count": 12,
                                    "eval_count": 20,
                                },
                            ):
                                response = TestClient(app).post("/chat", json=self.CHAT_PAYLOAD)

            self.assertEqual(response.status_code, 200)
            run_files = list(runs_dir.glob("*.json"))
            self.assertEqual(len(run_files), 1)
            payload = json.loads(run_files[0].read_text(encoding="utf-8"))
            self.assertTrue(run_files[0].name.startswith("chat_run_"))

        self.assertEqual(payload["version"], "chat_run.v1")
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["trace_id"])
        self.assertIn("created_at", payload)
        self.assertEqual(payload["timestamp"], payload["created_at"])
        self.assertEqual(payload["source"], "chat")
        self.assertEqual(payload["requested_model"], "granite4.1:8b")
        self.assertEqual(payload["model"], "granite4.1:8b")
        self.assertEqual(payload["provider"], "ollama")
        self.assertEqual(payload["temperature"], 0.2)
        self.assertEqual(payload["max_tokens"], 512)
        self.assertIsNone(payload["top_p"])
        self.assertEqual(payload["generation_config"]["temperature"], 0.2)
        self.assertEqual(payload["generation_config"]["max_tokens"], 512)
        self.assertEqual(payload["input"], self.CHAT_PAYLOAD["message"])
        self.assertEqual(payload["response"], "Transformer basado en attention.")
        self.assertEqual(payload["chunk_ids"], [1])
        self.assertEqual(payload["document_ids"], [2])
        self.assertEqual(payload["source_filenames"], ["doc.pdf"])
        self.assertEqual(payload["tokens_total"], 32)
        self.assertIn("generation_latency_ms", payload)
        self.assertIn("retrieval_latency_ms", payload)
        self.assertIn("tool_latency_ms", payload)

    def test_post_chat_persists_explicit_temperature_value(self):
        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "CHAT_RUNS"
            with patch("app.auth.settings.chat_auth_mode", "local_open"):
                with patch("app.main.settings.chat_runs_path", str(runs_dir)):
                    with patch("app.observability.chat_runs.settings.chat_runs_path", str(runs_dir)):
                        with patch("app.main.build_document_prompt", return_value=self._successful_rag_context()):
                            with patch(
                                "app.main.ask_chat",
                                return_value={
                                    "status": "ok",
                                    "provider": "ollama",
                                    "model": "granite4.1:8b",
                                    "temperature": 0.7,
                                    "use_rag": True,
                                    "answer": "Respuesta creativa.",
                                },
                            ):
                                response = TestClient(app).post(
                                    "/chat",
                                    json={**self.CHAT_PAYLOAD, "temperature": 0.7},
                                )

            self.assertEqual(response.status_code, 200)
            payload = json.loads(next(runs_dir.glob("*.json")).read_text(encoding="utf-8"))

        self.assertEqual(payload["temperature"], 0.7)
        self.assertEqual(payload["generation_config"]["temperature"], 0.7)

    def test_post_chat_persists_requested_model_and_effective_model(self):
        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "CHAT_RUNS"
            with patch("app.auth.settings.chat_auth_mode", "local_open"):
                with patch.dict("os.environ", {"CHAT_RUNS_DIR": str(runs_dir)}, clear=False):
                    with patch("app.main.resolve_provider_model", return_value=("ollama", "granite4.1:8b")):
                        with patch("app.main.build_document_prompt", return_value=self._successful_rag_context()):
                            with patch(
                                "app.main.ask_chat",
                                return_value={
                                    "status": "ok",
                                    "provider": "ollama",
                                    "model": "granite4.1:8b",
                                    "temperature": 0.2,
                                    "max_tokens": 256,
                                    "top_p": 0.9,
                                    "use_rag": True,
                                    "answer": "Respuesta OpenAI.",
                                },
                            ):
                                response = TestClient(app).post(
                                    "/chat",
                                    json={
                                        "message": "Resume el documento",
                                        "provider": "ollama",
                                        "model": "granite",
                                        "max_tokens": 256,
                                        "top_p": 0.9,
                                        "use_rag": True,
                                    },
                                )

            self.assertEqual(response.status_code, 200)
            payload = json.loads(next(runs_dir.glob("*.json")).read_text(encoding="utf-8"))

        self.assertEqual(payload["provider"], "ollama")
        self.assertEqual(payload["requested_model"], "granite")
        self.assertEqual(payload["model"], "granite4.1:8b")
        self.assertEqual(payload["max_tokens"], 256)
        self.assertEqual(payload["top_p"], 0.9)

    def test_controlled_error_also_persists_chat_run(self):
        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "CHAT_RUNS"
            with patch("app.auth.settings.chat_auth_mode", "local_open"):
                with patch("app.main.settings.chat_runs_path", str(runs_dir)):
                    with patch("app.observability.chat_runs.settings.chat_runs_path", str(runs_dir)):
                        response = TestClient(app).post(
                            "/chat",
                            json={"message": "hola", "provider": "ollama"},
                        )

            self.assertEqual(response.status_code, 400)
            payload = json.loads(next(runs_dir.glob("*.json")).read_text(encoding="utf-8"))

        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_code"], "model_required")
        self.assertEqual(payload["error_message"], "El contrato de /chat requiere un model explicito.")
        self.assertEqual(payload["input"], "hola")
        self.assertEqual(payload["source"], "chat")

    def test_post_chat_creates_runs_directory_automatically(self):
        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "CHAT_RUNS"
            with patch("app.auth.settings.chat_auth_mode", "local_open"):
                with patch("app.main.settings.chat_runs_path", str(runs_dir)):
                    with patch("app.observability.chat_runs.settings.chat_runs_path", str(runs_dir)):
                        with patch("app.main.build_document_prompt", return_value=self._successful_rag_context()):
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
            self.assertTrue(runs_dir.is_dir())
            self.assertEqual(len(list(runs_dir.glob("*.json"))), 1)

    def test_legacy_jsonl_runs_path_is_normalized_to_directory(self):
        with TemporaryDirectory() as tmpdir:
            legacy_runs_path = Path(tmpdir) / "chat_runs.jsonl"
            normalized_runs_dir = Path(tmpdir) / "chat_runs"
            with patch("app.auth.settings.chat_auth_mode", "local_open"):
                with patch("app.main.settings.chat_runs_path", str(legacy_runs_path)):
                    with patch("app.observability.chat_runs.settings.chat_runs_path", str(legacy_runs_path)):
                        with patch("app.main.build_document_prompt", return_value=self._successful_rag_context()):
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
            self.assertTrue(normalized_runs_dir.is_dir())
            self.assertEqual(len(list(normalized_runs_dir.glob("*.json"))), 1)

    def test_post_chat_returns_success_when_run_save_fails(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            with patch("app.main.build_document_prompt", return_value=self._successful_rag_context()):
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
                    with patch("app.main.save_chat_run", side_effect=OSError("disk_full")):
                        response = TestClient(app).post("/chat", json=self.CHAT_PAYLOAD)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_get_chat_runs_returns_descending_order(self):
        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "CHAT_RUNS"
            runs_dir.mkdir()
            (runs_dir / "chat_run_20260515T100000000000Z_older.json").write_text(
                json.dumps(
                    {
                        "version": "chat_run.v1",
                        "trace_id": "older",
                        "created_at": "2026-05-15T10:00:00+00:00",
                        "timestamp": "2026-05-15T10:00:00+00:00",
                        "source": "chat",
                        "endpoint": "/chat",
                        "input": "old",
                        "response": "old response",
                        "provider": "ollama",
                        "model": "granite4.1:8b",
                        "status": "ok",
                        "retrieval_status": "EVIDENCE_FOUND",
                        "chunk_ids": [],
                        "document_ids": [],
                        "source_filenames": [],
                    }
                ),
                encoding="utf-8",
            )
            (runs_dir / "chat_run_20260515T120000000000Z_newer.json").write_text(
                json.dumps(
                    {
                        "version": "chat_run.v1",
                        "trace_id": "newer",
                        "created_at": "2026-05-15T12:00:00+00:00",
                        "timestamp": "2026-05-15T12:00:00+00:00",
                        "source": "chat",
                        "endpoint": "/chat",
                        "input": "new",
                        "response": "new response",
                        "provider": "openai",
                        "model": "gpt-5.5",
                        "status": "error",
                        "retrieval_status": "NO_EVIDENCE_FOR_ANSWER",
                        "chunk_ids": [],
                        "document_ids": [],
                        "source_filenames": [],
                        "error_code": "rag_answer_contract_invalid",
                        "error_message": "failure",
                    }
                ),
                encoding="utf-8",
            )

            with patch("app.auth.settings.chat_auth_mode", "local_open"):
                with patch("app.main.settings.chat_runs_path", str(runs_dir)):
                    with patch("app.observability.chat_runs.settings.chat_runs_path", str(runs_dir)):
                        response = TestClient(app).get("/api/chat/runs?limit=10")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["count"], 2)
        self.assertEqual(body["items"][0]["trace_id"], "newer")
        self.assertEqual(body["items"][1]["trace_id"], "older")


if __name__ == "__main__":
    unittest.main()
