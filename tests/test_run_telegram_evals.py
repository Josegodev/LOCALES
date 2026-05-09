import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from evals import run_telegram_evals


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = ""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text

    def json(self) -> dict:
        return self._payload


class RunTelegramEvalsTests(unittest.TestCase):
    def test_parse_temperatures_returns_expected_list(self):
        self.assertEqual(
            run_telegram_evals.parse_temperatures("0.2,0.7,1.0"),
            [0.2, 0.7, 1.0],
        )

    def test_parse_temperatures_empty_uses_default(self):
        self.assertEqual(
            run_telegram_evals.parse_temperatures("", [0.2, 0.7, 1.0]),
            [0.2, 0.7, 1.0],
        )

    def test_confirmation_positive_values_execute(self):
        for value in ("s", "sí", "yes"):
            self.assertTrue(run_telegram_evals.is_confirmation_positive(value))

    def test_confirmation_empty_or_n_cancels(self):
        for value in ("", "n", "N"):
            self.assertFalse(run_telegram_evals.is_confirmation_positive(value))

    def test_make_output_dir_includes_model_and_timestamp(self):
        output_dir = run_telegram_evals.make_output_dir(
            Path("/tmp/runs"),
            "20260509T125031157569Z",
            "mistral:latest",
        )

        self.assertEqual(
            output_dir.name,
            "telegram_eval_mistral-latest_20260509T125031157569Z",
        )

    def test_run_interactive_cancel_does_not_call_endpoint(self):
        prompts = iter(
            [
                "granite4.1:8b",
                "",
                "",
                "",
                "",
            ]
        )
        post_calls: list[dict] = []

        def fake_input(_: str) -> str:
            return next(prompts)

        def fake_post(*args, **kwargs):
            post_calls.append({"args": args, "kwargs": kwargs})
            raise AssertionError("No debería llamarse al backend")

        with TemporaryDirectory() as tmpdir:
            result = run_telegram_evals.run_interactive(
                input_fn=fake_input,
                print_fn=lambda *args, **kwargs: None,
                post_fn=fake_post,
                now=datetime(2026, 5, 9, 12, 30, 0, tzinfo=timezone.utc),
                output_root=Path(tmpdir),
            )

        self.assertTrue(result["cancelled"])
        self.assertEqual(post_calls, [])

    def test_evaluate_response_detects_expected_terms(self):
        result = run_telegram_evals.evaluate_response(
            run_telegram_evals.INITIAL_CASES[0],
            {
                "status": "ok",
                "retrieval_status": "EVIDENCE_FOUND",
                "chunk_ids": [1],
                "source_filenames": ["EVOLUTION_MAP.md"],
                "response": "El AgentRuntime es el orquestador de producción.",
            },
        )

        self.assertEqual(result["missing_expected_terms"], [])
        self.assertTrue(result["pass"])

    def test_evaluate_response_detects_forbidden_terms(self):
        result = run_telegram_evals.evaluate_response(
            run_telegram_evals.INITIAL_CASES[0],
            {
                "status": "ok",
                "retrieval_status": "EVIDENCE_FOUND",
                "chunk_ids": [1],
                "source_filenames": ["EVOLUTION_MAP.md"],
                "response": "Es un supervisor de producción.",
            },
        )

        self.assertIn("supervisor de producción", result["forbidden_terms_found"])
        self.assertFalse(result["pass"])
        self.assertEqual(result["drift_score"], 2)

    def test_evaluate_response_fails_when_forbidden_source_is_retrieved(self):
        result = run_telegram_evals.evaluate_response(
            run_telegram_evals.INITIAL_CASES[0],
            {
                "status": "ok",
                "retrieval_status": "EVIDENCE_FOUND",
                "chunk_ids": [1],
                "source_filenames": ["MEMORIA 27.12.2021.pdf"],
                "response": "El AgentRuntime es el orquestador de producción.",
            },
        )

        self.assertEqual(result["forbidden_sources_found"], ["MEMORIA 27.12.2021.pdf"])
        self.assertFalse(result["retrieval_source_ok"])
        self.assertFalse(result["pass"])
        self.assertEqual(result["drift_score"], 3)

    def test_evaluate_response_marks_expected_source_match_when_relevant_source_exists(self):
        result = run_telegram_evals.evaluate_response(
            run_telegram_evals.INITIAL_CASES[0],
            {
                "status": "ok",
                "retrieval_status": "EVIDENCE_FOUND",
                "chunk_ids": [1],
                "source_filenames": ["EVOLUTION_MAP.md"],
                "response": "El AgentRuntime es el orquestador de producción.",
            },
        )

        self.assertTrue(result["retrieval_source_ok"])
        self.assertTrue(result["source_filename_match"])
        self.assertEqual(result["forbidden_sources_found"], [])

    def test_evaluate_response_keeps_source_match_not_available_when_sources_are_missing(self):
        result = run_telegram_evals.evaluate_response(
            run_telegram_evals.INITIAL_CASES[0],
            {
                "status": "ok",
                "retrieval_status": "EVIDENCE_FOUND",
                "chunk_ids": [1],
                "source_filenames": [],
                "response": "El AgentRuntime es el orquestador de producción.",
            },
        )

        self.assertEqual(result["source_filename_match"], "not_available")
        self.assertTrue(result["retrieval_source_ok"])

    def test_sanitize_trace_removes_long_context(self):
        sanitized = run_telegram_evals.sanitize_trace_for_eval_record(
            {
                "context": "texto RAG muy largo",
                "response": "respuesta corta",
                "input": "pregunta",
            }
        )

        self.assertNotIn("context", sanitized)
        self.assertEqual(sanitized["response"], "respuesta corta")
        self.assertEqual(sanitized["input"], "pregunta")
        self.assertTrue(sanitized["rag_payload_sanitized"])
        self.assertIn("context", sanitized["sanitized_fields"])

    def test_sanitize_trace_removes_chunk_text_and_keeps_metadata(self):
        sanitized = run_telegram_evals.sanitize_trace_for_eval_record(
            {
                "chunks": [
                    {
                        "id": 202,
                        "text": "texto largo del chunk",
                        "source_path": "/tmp/docs/EVOLUTION_MAP.md",
                        "score": 0.87,
                    }
                ],
                "answer": "El AgentRuntime es el orquestador de producción.",
                "eval_result": {"pass": True},
            }
        )

        self.assertNotIn("chunks", sanitized)
        self.assertEqual(sanitized["chunk_ids"], [202])
        self.assertEqual(sanitized["source_filenames"], ["EVOLUTION_MAP.md"])
        self.assertEqual(sanitized["scores"], [0.87])
        self.assertEqual(sanitized["answer"], "El AgentRuntime es el orquestador de producción.")
        self.assertEqual(sanitized["eval_result"], {"pass": True})
        self.assertTrue(sanitized["rag_payload_sanitized"])

    def test_build_summary_groups_by_temperature(self):
        config = {
            "model": "granite4.1:8b",
            "endpoint": "http://127.0.0.1:8000/chat",
            "temperatures": [0.2, 0.7],
            "runs_per_temperature": 2,
        }
        records = [
            {
                "eval_temperature": 0.2,
                "status": "ok",
                "retrieval_status": "EVIDENCE_FOUND",
                "latency_ms": 100,
                "tokens_input": 10,
                "tokens_output": 5,
                "tokens_total": 15,
                "eval_result": {"pass": True, "drift_score": 0, "forbidden_terms_found": []},
            },
            {
                "eval_temperature": 0.2,
                "status": "ok",
                "retrieval_status": "EVIDENCE_FOUND",
                "latency_ms": 200,
                "tokens_input": 20,
                "tokens_output": 10,
                "tokens_total": 30,
                "eval_result": {
                    "pass": False,
                    "drift_score": 3,
                    "forbidden_terms_found": [],
                    "forbidden_sources_found": ["MEMORIA 27.12.2021.pdf"],
                    "source_filename_match": False,
                    "retrieval_source_ok": False,
                },
            },
            {
                "eval_temperature": 0.7,
                "status": "error",
                "retrieval_status": "NO_EVIDENCE",
                "latency_ms": 300,
                "tokens_input": 30,
                "tokens_output": 15,
                "tokens_total": 45,
                "eval_result": {
                    "pass": False,
                    "drift_score": 3,
                    "forbidden_terms_found": ["x"],
                },
            },
        ]

        summary = run_telegram_evals.build_summary(
            records=records,
            config=config,
            created_at="2026-05-09T12:30:00+00:00",
            cases_count=1,
        )

        self.assertEqual(summary["total_runs"], 3)
        self.assertEqual(len(summary["grouped_by_temperature"]), 2)
        self.assertEqual(summary["grouped_by_temperature"][0]["temperature"], 0.2)
        self.assertEqual(summary["grouped_by_temperature"][0]["runs"], 2)
        self.assertEqual(summary["grouped_by_temperature"][0]["forbidden_sources_total"], 1)
        self.assertEqual(summary["grouped_by_temperature"][0]["source_match_failures"], 1)
        self.assertEqual(summary["grouped_by_temperature"][0]["retrieval_source_failures"], 1)
        self.assertEqual(summary["grouped_by_temperature"][1]["temperature"], 0.7)
        self.assertEqual(summary["grouped_by_temperature"][1]["status_counts"]["error"], 1)

    def test_write_jsonl_preserves_original_backend_fields(self):
        row = {
            "trace_id": "trace-1",
            "request_id": "req-1",
            "provider": "ollama",
            "backend_extra": "keep-me",
            "eval_result": {"pass": True},
        }

        with TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "runs.jsonl"
            run_telegram_evals.write_jsonl(path, [row])
            loaded = json.loads(path.read_text(encoding="utf-8").splitlines()[0])

        self.assertEqual(loaded["backend_extra"], "keep-me")
        self.assertEqual(loaded["trace_id"], "trace-1")

    def test_execute_evaluation_creates_expected_files(self):
        now = datetime(2026, 5, 9, 12, 45, 0, tzinfo=timezone.utc)
        config = {
            "model": "granite4.1:8b",
            "temperatures": [0.2],
            "runs_per_temperature": 1,
            "endpoint": "http://127.0.0.1:8000/chat",
            "timestamp": run_telegram_evals.build_timestamp(now),
            "message_field": "message",
            "use_rag": True,
            "top_k": 3,
            "source": "telegram_eval",
            "command": "eval",
        }

        def fake_post(*args, **kwargs):
            self.assertEqual(
                kwargs["json"]["allowed_source_filenames"],
                run_telegram_evals.NUCLEO_ALLOWED_SOURCE_FILENAMES,
            )
            return FakeResponse(
                200,
                {
                    "status": "ok",
                    "answer": "El AgentRuntime es el orquestador de producción.",
                    "retrieval_status": "EVIDENCE_FOUND",
                    "chunk_ids": [202],
                    "source_filenames": ["EVOLUTION_MAP.md"],
                    "tokens_input": 10,
                    "tokens_output": 5,
                    "tokens_total": 15,
                    "latency_ms": 123,
                    "model": "granite4.1:8b",
                },
            )

        with TemporaryDirectory() as tmpdir:
            result = run_telegram_evals.execute_evaluation(
                config=config,
                post_fn=fake_post,
                output_root=Path(tmpdir),
            )
            runs_path = result["runs_path"]
            summary_json_path = result["summary_json_path"]
            summary_md_path = result["summary_md_path"]
            loaded_run = json.loads(runs_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertTrue(runs_path.exists())
            self.assertTrue(summary_json_path.exists())
            self.assertTrue(summary_md_path.exists())
            self.assertIn("answer", loaded_run)
            self.assertEqual(loaded_run["response"], "El AgentRuntime es el orquestador de producción.")
            self.assertIn("eval_result", loaded_run)

    def test_execute_evaluation_writes_sanitized_run_record(self):
        now = datetime(2026, 5, 9, 12, 46, 0, tzinfo=timezone.utc)
        config = {
            "model": "granite4.1:8b",
            "temperatures": [0.2],
            "runs_per_temperature": 1,
            "endpoint": "http://127.0.0.1:8000/chat",
            "timestamp": run_telegram_evals.build_timestamp(now),
            "message_field": "message",
            "use_rag": True,
            "top_k": 3,
            "source": "telegram_eval",
            "command": "eval",
        }

        def fake_post(*args, **kwargs):
            return FakeResponse(
                200,
                {
                    "status": "ok",
                    "answer": "El AgentRuntime es el orquestador de producción.",
                    "retrieval_status": "EVIDENCE_FOUND",
                    "chunks": [
                        {
                            "id": 202,
                            "text": "texto largo del chunk",
                            "source_path": "/tmp/docs/EVOLUTION_MAP.md",
                        }
                    ],
                    "context": "prompt RAG largo",
                    "tokens_input": 10,
                    "tokens_output": 5,
                    "tokens_total": 15,
                    "latency_ms": 123,
                    "model": "granite4.1:8b",
                },
            )

        with TemporaryDirectory() as tmpdir:
            result = run_telegram_evals.execute_evaluation(
                config=config,
                post_fn=fake_post,
                output_root=Path(tmpdir),
            )
            loaded_run = json.loads(result["runs_path"].read_text(encoding="utf-8").splitlines()[0])

        self.assertNotIn("chunks", loaded_run)
        self.assertNotIn("context", loaded_run)
        self.assertEqual(loaded_run["chunk_ids"], [202])
        self.assertEqual(loaded_run["source_filenames"], ["EVOLUTION_MAP.md"])
        self.assertEqual(loaded_run["answer"], "El AgentRuntime es el orquestador de producción.")
        self.assertIn("eval_result", loaded_run)
        self.assertTrue(loaded_run["rag_payload_sanitized"])


if __name__ == "__main__":
    unittest.main()
