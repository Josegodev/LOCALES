import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class RunsRouterTests(unittest.TestCase):
    def _write_run(self, runs_dir: Path, *, trace_id: str, created_at: str, model: str, status: str) -> None:
        (runs_dir / f"{trace_id}.json").write_text(
            json.dumps(
                {
                    "trace_id": trace_id,
                    "created_at": created_at,
                    "model": model,
                    "status": status,
                    "latency_ms": 120,
                    "tokens_input": 10,
                    "tokens_output": 5,
                    "tokens_total": 15,
                    "retrieval_status": "EVIDENCE_FOUND",
                    "fallback_used": False,
                }
            ),
            encoding="utf-8",
        )

    def test_get_runs_summary_returns_200(self):
        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "CHAT_RUNS"
            runs_dir.mkdir()
            self._write_run(
                runs_dir,
                trace_id="trace-1",
                created_at="2026-05-16T10:00:00+00:00",
                model="granite4.1:8b",
                status="ok",
            )

            with patch("app.auth.settings.chat_auth_mode", "local_open"):
                with patch.dict(os.environ, {"CHAT_RUNS_DIR": str(runs_dir)}, clear=False):
                    response = TestClient(app).get("/api/runs/summary")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_runs"], 1)

    def test_get_runs_timeseries_returns_200(self):
        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "CHAT_RUNS"
            runs_dir.mkdir()
            self._write_run(
                runs_dir,
                trace_id="trace-1",
                created_at="2026-05-16T10:00:00+00:00",
                model="granite4.1:8b",
                status="ok",
            )

            with patch("app.auth.settings.chat_auth_mode", "local_open"):
                with patch.dict(os.environ, {"CHAT_RUNS_DIR": str(runs_dir)}, clear=False):
                    response = TestClient(app).get("/api/runs/timeseries")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        self.assertEqual(response.json()["items"][0]["trace_id"], "trace-1")

    def test_get_runs_operational_stats_returns_200(self):
        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "CHAT_RUNS"
            runs_dir.mkdir()
            self._write_run(
                runs_dir,
                trace_id="trace-1",
                created_at="2026-05-16T10:00:00+00:00",
                model="granite4.1:8b",
                status="ok",
            )

            with patch("app.auth.settings.chat_auth_mode", "local_open"):
                with patch("app.evals.router.settings.operation_timeout_ms", 10000):
                    with patch.dict(os.environ, {"CHAT_RUNS_DIR": str(runs_dir)}, clear=False):
                        response = TestClient(app).get("/api/runs/operational-stats")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["timeout_ms"], 10000)
        self.assertEqual(len(response.json()["models"]), 1)
        self.assertEqual(response.json()["models"][0]["model"], "granite4.1:8b")
