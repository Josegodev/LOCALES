import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class TelegramEvalEndpointTests(unittest.TestCase):
    def test_telegram_eval_endpoint_returns_normalized_runs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir)
            older = {
                "trace_id": "older-trace",
                "created_at": "2026-05-10T10:00:00+00:00",
                "source": "telegram",
                "model": "granite4.1:8b",
                "status": "ok",
                "retrieval_status": "EVIDENCE_FOUND",
                "latency_ms": 1200,
                "prompt_eval_count": 10,
                "eval_count": 5,
            }
            newer = {
                "trace_id": "newer-trace",
                "created_at": "2026-05-12T10:00:00+00:00",
                "source": "telegram",
                "model": "granite4.1:8b",
                "status": "error",
                "error_code": "ConnectTimeout",
                "error_message": (
                    "HTTPConnectionPool(host='192.168.1.20', port=8000): "
                    "Max retries exceeded with url: /chat "
                    "(Caused by ConnectTimeoutError())"
                ),
                "warnings": ["sample_warning"],
            }
            (runs_dir / "chat_eval_older.json").write_text(json.dumps(older), encoding="utf-8")
            (runs_dir / "chat_eval_newer.json").write_text(json.dumps(newer), encoding="utf-8")
            (runs_dir / "chat_eval_corrupt.json").write_text("{", encoding="utf-8")

            with patch("app.observability.telegram_trace.TELEGRAM_EVAL_RUNS_DIR", runs_dir):
                response = TestClient(app).get("/api/evals/telegram?limit=1")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["trace_id"], "newer-trace")
        self.assertEqual(payload[0]["status"], "error")
        self.assertEqual(payload[0]["tokens_input"], None)
        self.assertEqual(payload[0]["error_category"], "backend_connectivity")
        self.assertEqual(payload[0]["failed_phase"], "backend_request")
        self.assertEqual(payload[0]["warnings"], ["sample_warning"])


if __name__ == "__main__":
    unittest.main()
