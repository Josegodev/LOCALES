import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import scripts.run_chat_evals as run_chat_evals


class ChatEvalsTests(unittest.TestCase):
    def test_load_cases_returns_required_fields(self):
        cases = run_chat_evals.load_cases()

        self.assertGreaterEqual(len(cases), 1)
        first_case = cases[0]
        self.assertIn("id", first_case)
        self.assertIn("input", first_case)
        self.assertIn("expected_contains", first_case)
        self.assertIn("forbidden_contains", first_case)
        self.assertIn("min_chars", first_case)
        self.assertIn("max_chars", first_case)
        self.assertIn("notes", first_case)

    def test_evaluate_expected_contains_detects_missing_terms(self):
        missing = run_chat_evals.evaluate_expected_contains(
            "Respuesta corta",
            ["respuesta", "asistente"],
        )

        self.assertEqual(missing, ["asistente"])

    def test_evaluate_forbidden_contains_detects_present_terms(self):
        forbidden = run_chat_evals.evaluate_forbidden_contains(
            "Este backend menciona LM Studio por error",
            ["LM Studio", "OpenAI API"],
        )

        self.assertEqual(forbidden, ["LM Studio"])

    def test_evaluate_length_checks_range(self):
        length_check = run_chat_evals.evaluate_length("hola", 3, 5)

        self.assertTrue(length_check["within_range"])
        self.assertFalse(length_check["too_short"])
        self.assertFalse(length_check["too_long"])

    def test_compare_against_baseline_detects_changes(self):
        baseline_run = {
            "results": [
                {
                    "case_id": "case_a",
                    "status": "ok",
                    "passed": True,
                    "response": "respuesta estable",
                    "response_chars": 16,
                    "forbidden_contains_present": [],
                    "latency_ms": 1000,
                    "tokens_input": 100,
                    "tokens_output": 50,
                    "output_tokens_per_second": 20.0,
                    "prompt_tokens_per_second": 40.0,
                    "total_duration_ns": 1_000_000_000,
                    "max_chars": 200,
                }
            ]
        }
        current_run = {
            "results": [
                {
                    "case_id": "case_a",
                    "status": "error",
                    "passed": False,
                    "response": "",
                    "response_chars": 0,
                    "forbidden_contains_present": ["LM Studio"],
                    "latency_ms": 2500,
                    "tokens_input": 160,
                    "tokens_output": 120,
                    "output_tokens_per_second": 8.0,
                    "prompt_tokens_per_second": 15.0,
                    "total_duration_ns": 2_500_000_000,
                    "max_chars": 200,
                }
            ]
        }

        comparison = run_chat_evals.compare_against_baseline(current_run, baseline_run)

        self.assertTrue(comparison["baseline_available"])
        self.assertEqual(comparison["cases_with_changes"], 1)
        change_types = {item["type"] for item in comparison["comparisons"][0]["changes"]}
        self.assertIn("status_changed", change_types)
        self.assertIn("pass_fail_changed", change_types)
        self.assertIn("response_empty", change_types)
        self.assertIn("new_forbidden_terms", change_types)
        self.assertIn("latency_changed_over_100_percent", change_types)
        self.assertIn("prompt_tokens_increase_over_50_percent", change_types)
        self.assertIn("output_tokens_increase_over_100_percent", change_types)
        self.assertIn("output_tokens_per_second_degraded_over_50_percent", change_types)
        self.assertIn("prompt_tokens_per_second_degraded_over_50_percent", change_types)
        self.assertIn("total_duration_increase_over_100_percent", change_types)

    def test_build_case_trace_id_returns_valid_uuid_hex(self):
        trace_id = run_chat_evals.build_case_trace_id("run_1", "case_a")
        other_trace_id = run_chat_evals.build_case_trace_id("run_1", "case_b")

        self.assertEqual(len(trace_id), 32)
        int(trace_id, 16)
        self.assertNotEqual(trace_id, other_trace_id)

    def test_extract_ollama_metrics_derives_token_rates(self):
        metrics = run_chat_evals.extract_ollama_metrics(
            {
                "prompt_eval_count": 50,
                "eval_count": 25,
                "prompt_eval_duration": 1_000_000_000,
                "eval_duration": 500_000_000,
                "total_duration": 2_000_000_000,
                "load_duration": 10_000_000,
            }
        )

        self.assertEqual(metrics["tokens_input"], 50)
        self.assertEqual(metrics["tokens_output"], 25)
        self.assertEqual(metrics["tokens_total"], 75)
        self.assertAlmostEqual(metrics["prompt_tokens_per_second"], 50.0)
        self.assertAlmostEqual(metrics["output_tokens_per_second"], 50.0)
        self.assertEqual(metrics["metric_failures"], [])

    def test_extract_ollama_metrics_warns_when_missing(self):
        metrics = run_chat_evals.extract_ollama_metrics({})

        self.assertTrue(any(warning.startswith("metric_missing:") for warning in metrics["warnings"]))
        self.assertEqual(metrics["metric_failures"], [])

    def test_run_evals_writes_run_and_baseline_files(self):
        fake_case = {
            "id": "case_a",
            "input": "hola",
            "expected_contains": ["ok"],
            "forbidden_contains": [],
            "min_chars": 1,
            "max_chars": 50,
            "notes": "test",
        }
        fake_result = {
            "case_id": "case_a",
            "trace_id": "12345678123456781234567812345678",
            "input": "hola",
            "notes": "test",
            "http_status": 200,
            "status": "ok",
            "passed": True,
            "latency_ms": 10,
            "client_latency_ms": 10,
            "error_code": None,
            "error_message": None,
            "response": "ok",
            "response_chars": 2,
            "expected_contains_missing": [],
            "forbidden_contains_present": [],
            "length_check": {"within_range": True},
            "checks": {
                "http_ok": True,
                "response_not_empty": True,
                "expected_contains": True,
                "forbidden_contains": True,
                "length_bounds": True,
                "metrics_valid": True,
            },
            "warnings": [],
            "metric_failures": [],
            "prompt_eval_count": 5,
            "eval_count": 3,
            "prompt_eval_duration": 10,
            "eval_duration": 10,
            "total_duration": 30,
            "load_duration": 1,
            "tokens_input": 5,
            "tokens_output": 3,
            "tokens_total": 8,
            "output_tokens_per_second": 300000000.0,
            "prompt_tokens_per_second": 500000000.0,
            "total_duration_ns": 30,
            "load_duration_ns": 1,
            "min_chars": 1,
            "max_chars": 50,
            "model": "granite4.1:8b",
        }

        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "runs"
            baseline_path = Path(tmpdir) / "baseline.json"
            with patch.object(run_chat_evals, "RUNS_DIR", runs_dir):
                with patch.object(run_chat_evals, "BASELINE_PATH", baseline_path):
                    with patch.object(run_chat_evals, "load_cases", return_value=[fake_case]):
                        with patch.object(run_chat_evals, "run_case", return_value=fake_result):
                            run_payload = run_chat_evals.run_evals(write_baseline=True)
                            self.assertTrue(Path(run_payload["output_path"]).exists())
                            self.assertTrue(baseline_path.exists())

    def test_run_evals_compare_baseline_works(self):
        fake_case = {
            "id": "case_a",
            "input": "hola",
            "expected_contains": ["ok"],
            "forbidden_contains": [],
            "min_chars": 1,
            "max_chars": 50,
            "notes": "test",
        }
        baseline_result = {
            "case_id": "case_a",
            "status": "ok",
            "passed": True,
            "response": "ok",
            "response_chars": 2,
            "forbidden_contains_present": [],
            "latency_ms": 10,
            "tokens_input": 5,
            "tokens_output": 3,
            "output_tokens_per_second": 300000000.0,
            "prompt_tokens_per_second": 500000000.0,
            "total_duration_ns": 30,
            "max_chars": 50,
        }
        current_result = {
            **baseline_result,
            "trace_id": "12345678123456781234567812345678",
            "input": "hola",
            "notes": "test",
            "http_status": 200,
            "client_latency_ms": 10,
            "error_code": None,
            "error_message": None,
            "expected_contains_missing": [],
            "length_check": {"within_range": True},
            "checks": {
                "http_ok": True,
                "response_not_empty": True,
                "expected_contains": True,
                "forbidden_contains": True,
                "length_bounds": True,
                "metrics_valid": True,
            },
            "warnings": [],
            "metric_failures": [],
            "prompt_eval_count": 5,
            "eval_count": 3,
            "prompt_eval_duration": 10,
            "eval_duration": 10,
            "total_duration": 30,
            "load_duration": 1,
            "tokens_total": 8,
            "load_duration_ns": 1,
            "min_chars": 1,
            "model": "granite4.1:8b",
        }

        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "runs"
            baseline_path = Path(tmpdir) / "baseline.json"
            baseline_path.write_text(
                '{"results":[{"case_id":"case_a","status":"ok","passed":true,"response":"ok","response_chars":2,"forbidden_contains_present":[],"latency_ms":10,"tokens_input":5,"tokens_output":3,"output_tokens_per_second":300000000.0,"prompt_tokens_per_second":500000000.0,"total_duration_ns":30,"max_chars":50}]}',
                encoding="utf-8",
            )
            with patch.object(run_chat_evals, "RUNS_DIR", runs_dir):
                with patch.object(run_chat_evals, "BASELINE_PATH", baseline_path):
                    with patch.object(run_chat_evals, "load_cases", return_value=[fake_case]):
                        with patch.object(run_chat_evals, "run_case", return_value=current_result):
                            run_payload = run_chat_evals.run_evals(compare_baseline=True)

        self.assertTrue(run_payload["baseline_comparison"]["baseline_available"])
        self.assertEqual(run_payload["baseline_comparison"]["cases_with_changes"], 0)

    def test_run_evals_does_not_write_failed_baseline(self):
        fake_case = {
            "id": "case_a",
            "input": "hola",
            "expected_contains": ["ok"],
            "forbidden_contains": [],
            "min_chars": 1,
            "max_chars": 50,
            "notes": "test",
        }
        failed_result = {
            "case_id": "case_a",
            "trace_id": "12345678123456781234567812345678",
            "input": "hola",
            "notes": "test",
            "http_status": 200,
            "status": "ok",
            "passed": False,
            "latency_ms": 10,
            "client_latency_ms": 10,
            "error_code": None,
            "error_message": None,
            "response": "respuesta inesperada",
            "response_chars": 20,
            "expected_contains_missing": ["ok"],
            "forbidden_contains_present": [],
            "length_check": {"within_range": True},
            "checks": {
                "http_ok": True,
                "response_not_empty": True,
                "expected_contains": False,
                "forbidden_contains": True,
                "length_bounds": True,
                "metrics_valid": True,
            },
            "warnings": [],
            "metric_failures": [],
            "prompt_eval_count": None,
            "eval_count": None,
            "prompt_eval_duration": None,
            "eval_duration": None,
            "total_duration": None,
            "load_duration": None,
            "tokens_input": None,
            "tokens_output": None,
            "tokens_total": None,
            "output_tokens_per_second": None,
            "prompt_tokens_per_second": None,
            "total_duration_ns": None,
            "load_duration_ns": None,
            "min_chars": 1,
            "max_chars": 50,
            "model": "granite4.1:8b",
        }

        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "runs"
            baseline_path = Path(tmpdir) / "baseline.json"
            with patch.object(run_chat_evals, "RUNS_DIR", runs_dir):
                with patch.object(run_chat_evals, "BASELINE_PATH", baseline_path):
                    with patch.object(run_chat_evals, "load_cases", return_value=[fake_case]):
                        with patch.object(run_chat_evals, "run_case", return_value=failed_result):
                            run_payload = run_chat_evals.run_evals(write_baseline=True)

        self.assertFalse(run_payload["baseline_written"])
        self.assertFalse(baseline_path.exists())


if __name__ == "__main__":
    unittest.main()
