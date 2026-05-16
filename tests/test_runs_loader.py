import json
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app.evals.loader import load_runs


class RunsLoaderTests(unittest.TestCase):
    def test_loads_valid_run_json(self):
        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "CHAT_RUNS"
            runs_dir.mkdir()
            (runs_dir / "run.json").write_text(
                json.dumps(
                    {
                        "trace_id": "trace-1",
                        "created_at": "2026-05-16T10:00:00+00:00",
                        "model": "granite4.1:8b",
                        "status": "ok",
                        "tokens_input": 10,
                        "tokens_output": 5,
                    }
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"CHAT_RUNS_DIR": str(runs_dir)}, clear=False):
                loaded = load_runs()

        self.assertEqual(len(loaded.items), 1)
        self.assertEqual(loaded.items[0].trace_id, "trace-1")
        self.assertEqual(loaded.items[0].tokens_total, 15)
        self.assertEqual(loaded.items[0].raw_filename, "run.json")

    def test_ignores_corrupt_json(self):
        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "CHAT_RUNS"
            runs_dir.mkdir()
            (runs_dir / "broken.json").write_text("{not-valid-json", encoding="utf-8")

            with patch.dict(os.environ, {"CHAT_RUNS_DIR": str(runs_dir)}, clear=False):
                loaded = load_runs()

        self.assertEqual(len(loaded.items), 0)
        self.assertEqual(loaded.corrupt_files, ["broken.json"])

    def test_tolerates_missing_directory(self):
        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "missing"
            with patch.dict(os.environ, {"CHAT_RUNS_DIR": str(runs_dir)}, clear=False):
                loaded = load_runs()

        self.assertEqual(len(loaded.items), 0)
        self.assertEqual(loaded.corrupt_files, [])
        self.assertEqual(loaded.skipped_files, [])

    def test_skips_incompatible_batch_eval_runs(self):
        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "evals" / "runs"
            runs_dir.mkdir(parents=True)
            (runs_dir / "eval.json").write_text(
                json.dumps(
                    {
                        "version": "chat_eval_run.v1",
                        "run_id": "batch-1",
                        "summary": {"total": 1},
                        "results": [],
                    }
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, {"EVAL_RUNS_DIR": str(runs_dir)}, clear=False):
                loaded = load_runs()

        self.assertEqual(len(loaded.items), 0)
        self.assertEqual(loaded.skipped_files, ["eval.json"])
