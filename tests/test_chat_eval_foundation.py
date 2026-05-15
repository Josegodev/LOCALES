import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.observability.chat_trace import write_chat_trace


class ChatEvalFoundationTests(unittest.TestCase):
    def _write_eval_fixture_files(self, root: Path) -> tuple[Path, Path, Path]:
        cases_path = root / "cases.json"
        baseline_path = root / "baseline.json"
        runs_dir = root / "runs"
        cases_path.write_text(
            json.dumps(
                {
                    "version": "chat_eval_cases.v1",
                    "cases": [
                        {
                            "id": "case_1",
                            "input": "Que es un transformer?",
                            "provider": "ollama",
                            "model": "granite4.1:8b",
                            "use_rag": True,
                            "temperature": 0.2,
                            "forbidden_terms": [],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        baseline_path.write_text(
            json.dumps(
                {
                    "version": "chat_baseline.v1",
                    "baseline_items": [
                        {
                            "case_id": "case_1",
                            "expected_status": "ok",
                            "expected_retrieval_status": "EVIDENCE_FOUND",
                            "expected_source_filenames": ["doc.pdf"],
                            "expected_min_chunk_count": 1,
                            "expected_answer_contains": ["Transformer", "attention"],
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        return cases_path, baseline_path, runs_dir

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
            "query_original": "Que es un transformer?",
            "query_normalized": "que es un transformer?",
            "query_terms": [],
            "quoted_terms": [],
            "source_intent": "mixed",
            "selected_corpus": "mixed",
            "candidate_filenames": ["doc.pdf"],
            "selected_filenames": ["doc.pdf"],
            "scores": [1],
        }

    def test_chat_eval_endpoint_returns_expected_shape(self):
        with TemporaryDirectory() as tmpdir:
            trace_path = Path(tmpdir) / "chat_traces.jsonl"

            with patch("app.auth.settings.chat_auth_mode", "local_open"):
                with patch("app.observability.chat_trace.settings.chat_trace_path", str(trace_path)):
                    response = TestClient(app).get("/api/evals/chat?limit=25")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 0)
        self.assertEqual(response.json()["limit"], 25)
        self.assertEqual(response.json()["items"], [])

    def test_chat_eval_endpoint_clamps_limit(self):
        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            client = TestClient(app)
            too_small = client.get("/api/evals/chat?limit=0")
            too_large = client.get("/api/evals/chat?limit=500")

        self.assertEqual(too_small.status_code, 200)
        self.assertEqual(too_small.json()["limit"], 1)
        self.assertEqual(too_large.status_code, 200)
        self.assertEqual(too_large.json()["limit"], 100)

    def test_chat_eval_endpoint_lists_chat_traces_without_running_evals(self):
        with TemporaryDirectory() as tmpdir:
            trace_path = Path(tmpdir) / "chat_traces.jsonl"
            write_chat_trace(
                trace_id="12345678123456781234567812345678",
                source="frontend",
                input_text="Que es un transformer?",
                response_text="Respuesta",
                provider="ollama",
                model="granite4.1:8b",
                status="ok",
                retrieval_status="EVIDENCE_FOUND",
                chunk_ids=[375, 376],
                document_ids=[68],
                source_filenames=["Attention is all yout need.pdf"],
                latency_ms=42,
                error_code=None,
                error_message=None,
                warnings=[],
                use_rag=True,
                evidence_used=True,
                fallback_used=False,
                answer_mode="documentary_answer",
                path=trace_path,
            )

            with patch("app.auth.settings.chat_auth_mode", "local_open"):
                with patch("app.observability.chat_trace.settings.chat_trace_path", str(trace_path)):
                    response = TestClient(app).get("/api/evals/chat?limit=25")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["count"], 1)
        self.assertEqual(body["limit"], 25)
        item = body["items"][0]
        self.assertEqual(item["trace_id"], "12345678123456781234567812345678")
        self.assertEqual(item["retrieval_status"], "EVIDENCE_FOUND")
        self.assertEqual(item["source_filenames"], ["Attention is all yout need.pdf"])
        self.assertEqual(item["status"], "ok")

    def test_chat_eval_run_endpoint_returns_status_ok_and_summary(self):
        with TemporaryDirectory() as tmpdir:
            cases_path, baseline_path, runs_dir = self._write_eval_fixture_files(Path(tmpdir))
            with patch("app.auth.settings.chat_auth_mode", "local_open"):
                with patch("app.main.chat_eval_runner.DEFAULT_CASES_PATH", str(cases_path)):
                    with patch("app.main.chat_eval_runner.DEFAULT_BASELINE_PATH", str(baseline_path)):
                        with patch("app.main.chat_eval_runner.DEFAULT_OUT_DIR", str(runs_dir)):
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
                                        "latency_ms": 12,
                                    },
                                ):
                                    with patch("app.llm_client._list_ollama_models", return_value=["granite4.1:8b"]):
                                        response = TestClient(app).post("/api/evals/chat/run")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertEqual(body["summary"]["total"], 1)
        self.assertEqual(body["summary"]["passed"], 1)
        self.assertTrue(body["run_id"])
        self.assertTrue(body["run_path"].startswith("evals/runs/") or body["run_path"].endswith("_chat_eval_run.json"))

    def test_chat_eval_run_endpoint_creates_run_file_with_required_fields(self):
        with TemporaryDirectory() as tmpdir:
            cases_path, baseline_path, runs_dir = self._write_eval_fixture_files(Path(tmpdir))
            with patch("app.auth.settings.chat_auth_mode", "local_open"):
                with patch("app.main.chat_eval_runner.DEFAULT_CASES_PATH", str(cases_path)):
                    with patch("app.main.chat_eval_runner.DEFAULT_BASELINE_PATH", str(baseline_path)):
                        with patch("app.main.chat_eval_runner.DEFAULT_OUT_DIR", str(runs_dir)):
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
                                    },
                                ):
                                    with patch("app.llm_client._list_ollama_models", return_value=["granite4.1:8b"]):
                                        response = TestClient(app).post("/api/evals/chat/run")

            run_files = list(runs_dir.glob("*_chat_eval_run.json"))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(run_files), 1)
            payload = json.loads(run_files[0].read_text(encoding="utf-8"))

        self.assertIn("run_id", payload)
        self.assertIn("created_at", payload)
        self.assertIn("results", payload)
        self.assertIn("summary", payload)
        self.assertEqual(payload["source"], "frontend")
        self.assertEqual(payload["cases_file"], str(cases_path))
        self.assertEqual(payload["baseline_file"], str(baseline_path))

    def test_chat_endpoint_does_not_create_eval_run_files(self):
        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "runs"
            with patch("app.auth.settings.chat_auth_mode", "local_open"):
                with patch("app.main.chat_eval_runner.DEFAULT_OUT_DIR", str(runs_dir)):
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
                            },
                        ):
                            response = TestClient(app).post(
                                "/chat",
                                json={"message": "hola", "provider": "ollama", "model": "granite4.1:8b"},
                            )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(runs_dir.exists() and list(runs_dir.glob("*_chat_eval_run.json")))

    def test_importing_app_main_does_not_import_telegram_modules(self):
        telegram_modules = [name for name in sys.modules if "telegram" in name]
        self.assertEqual(telegram_modules, [])

    def test_chat_eval_cases_file_exists_and_is_valid_json(self):
        cases_path = Path("/home/jose-gonzalez-oliva/LOCALES/evals/cases/chat_cases.json")
        payload = json.loads(cases_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["version"], "chat_eval_cases.v1")
        self.assertIsInstance(payload["cases"], list)
        self.assertGreaterEqual(len(payload["cases"]), 1)

    def test_chat_baseline_file_exists_and_is_valid_json(self):
        baseline_path = Path("/home/jose-gonzalez-oliva/LOCALES/evals/baselines/chat_baseline.json")
        payload = json.loads(baseline_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["version"], "chat_baseline.v1")
        self.assertIsInstance(payload["baseline_items"], list)
        self.assertGreaterEqual(len(payload["baseline_items"]), 1)

    def test_every_baseline_case_id_exists_in_chat_cases(self):
        cases_path = Path("/home/jose-gonzalez-oliva/LOCALES/evals/cases/chat_cases.json")
        baseline_path = Path("/home/jose-gonzalez-oliva/LOCALES/evals/baselines/chat_baseline.json")
        cases_payload = json.loads(cases_path.read_text(encoding="utf-8"))
        baseline_payload = json.loads(baseline_path.read_text(encoding="utf-8"))

        case_ids = {item["id"] for item in cases_payload["cases"]}
        baseline_case_ids = {item["case_id"] for item in baseline_payload["baseline_items"]}

        self.assertTrue(baseline_case_ids.issubset(case_ids))

    def test_no_legacy_telegram_eval_runner_is_imported(self):
        loaded_names = set(sys.modules)
        self.assertNotIn("app.telegram_runtime", loaded_names)
        self.assertFalse(any("eval" in name and "telegram" in name for name in loaded_names))


if __name__ == "__main__":
    unittest.main()
