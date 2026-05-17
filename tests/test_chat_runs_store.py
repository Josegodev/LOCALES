import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.chat_runs.store import get_chat_run, load_chat_runs


class ChatRunsStoreTests(unittest.TestCase):
    def test_load_chat_runs_normalizes_ollama_style_metrics(self):
        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "CHAT_RUNS"
            runs_dir.mkdir()
            (runs_dir / "older.json").write_text(
                json.dumps(
                    {
                        "trace_id": "trace-older",
                        "created_at": "2026-05-16T10:00:00+00:00",
                        "provider": "ollama",
                        "model": "granite4.1:8b",
                        "temperature": 0.2,
                        "use_rag": True,
                        "retrieval_status": "EVIDENCE_FOUND",
                        "status": "ok",
                        "fallback_used": False,
                        "latency_ms": 240,
                        "retrieval_latency_ms": 40,
                        "generation_latency_ms": 200,
                        "prompt_eval_count": 12,
                        "eval_count": 24,
                        "prompt_eval_duration": 100000000,
                        "eval_duration": 200000000,
                        "total_duration": 350000000,
                        "load_duration": 50000000,
                        "chunk_ids": ["1", 2],
                        "source_filenames": ["doc-a.md"],
                    }
                ),
                encoding="utf-8",
            )
            (runs_dir / "newer.json").write_text(
                json.dumps(
                    {
                        "trace_id": "trace-newer",
                        "created_at": "2026-05-16T10:01:00+00:00",
                        "provider": "ollama",
                        "model": "granite4.1:8b",
                        "status": "ok",
                    }
                ),
                encoding="utf-8",
            )

            loaded = load_chat_runs(runs_dir=runs_dir)

        self.assertEqual(len(loaded.items), 2)
        self.assertEqual(loaded.items[0]["trace_id"], "trace-newer")
        normalized = loaded.items[1]
        self.assertEqual(normalized["tokens_input"], 12.0)
        self.assertEqual(normalized["tokens_output"], 24.0)
        self.assertEqual(normalized["tokens_total"], 36.0)
        self.assertEqual(normalized["output_tokens_per_second"], 120.0)
        self.assertEqual(normalized["chunk_ids"], [1, 2])
        self.assertEqual(normalized["source_filenames"], ["doc-a.md"])
        self.assertEqual(normalized["observability_level"], "provider_native")

    def test_load_chat_runs_keeps_missing_openai_metrics_as_none(self):
        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "CHAT_RUNS"
            runs_dir.mkdir()
            (runs_dir / "openai.json").write_text(
                json.dumps(
                    {
                        "trace_id": "trace-openai",
                        "created_at": "2026-05-16T12:00:00+00:00",
                        "provider": "openai",
                        "model": "gpt-5.5",
                        "temperature": 0.2,
                        "use_rag": False,
                        "status": "ok",
                        "latency_ms": 950,
                        "tokens_input": 50,
                        "tokens_output": 20,
                    }
                ),
                encoding="utf-8",
            )

            loaded = load_chat_runs(runs_dir=runs_dir)

        normalized = loaded.items[0]
        self.assertEqual(normalized["trace_id"], "trace-openai")
        self.assertIsNone(normalized["prompt_eval_duration"])
        self.assertIsNone(normalized["eval_duration"])
        self.assertIsNone(normalized["total_duration"])
        self.assertIsNone(normalized["load_duration"])
        self.assertIsNone(normalized["output_tokens_per_second"])
        self.assertEqual(normalized["tokens_total"], 70.0)
        self.assertEqual(normalized["observability_level"], "runtime_only")

    def test_load_chat_runs_reports_skipped_files(self):
        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "CHAT_RUNS"
            runs_dir.mkdir()
            (runs_dir / "broken.json").write_text("{not-valid-json", encoding="utf-8")
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

            loaded = load_chat_runs(runs_dir=runs_dir)

        self.assertEqual(loaded.skipped_files_count, 2)
        self.assertEqual(loaded.items, [])
        self.assertEqual(sorted(loaded.skipped_files), ["broken.json", "eval.json"])

    def test_get_chat_run_returns_normalized_run(self):
        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "CHAT_RUNS"
            runs_dir.mkdir()
            (runs_dir / "run.json").write_text(
                json.dumps(
                    {
                        "trace_id": "trace-1",
                        "created_at": "2026-05-16T12:00:00+00:00",
                        "provider": "openai",
                        "model": "gpt-5.5",
                        "status": "ok",
                    }
                ),
                encoding="utf-8",
            )

            run = get_chat_run("trace-1", runs_dir=runs_dir)

        self.assertIsNotNone(run)
        self.assertEqual(run["provider"], "openai")
