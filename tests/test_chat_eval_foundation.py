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
