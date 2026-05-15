import importlib.util
import json
import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory


def _load_runner_module():
    module_path = Path("/home/jose-gonzalez-oliva/LOCALES/scripts/run_chat_evals.py")
    spec = importlib.util.spec_from_file_location("run_chat_evals_module", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


runner = _load_runner_module()


class ChatEvalRunnerTests(unittest.TestCase):
    def test_loading_cases_and_baseline(self):
        with TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            cases_path = tmp_path / "cases.json"
            baseline_path = tmp_path / "baseline.json"
            cases_path.write_text(
                json.dumps({"cases": [{"id": "case_1", "input": "hola"}]}),
                encoding="utf-8",
            )
            baseline_path.write_text(
                json.dumps({"baseline_items": [{"case_id": "case_1", "expected_status": "ok"}]}),
                encoding="utf-8",
            )

            cases = runner.load_cases(cases_path)
            baseline = runner.load_baseline(baseline_path)

        self.assertEqual(cases[0]["id"], "case_1")
        self.assertEqual(baseline[0]["case_id"], "case_1")

    def test_baseline_references_valid_case_ids(self):
        cases = [{"id": "case_1", "input": "hola"}]
        baseline_items = [{"case_id": "case_1", "expected_status": "ok"}]

        runner.validate_baseline_case_ids(cases, baseline_items)

    def test_comparison_passes_when_expected_fields_match(self):
        case = {
            "id": "case_1",
            "input": "Que es un transformer?",
            "forbidden_terms": [],
        }
        baseline_item = {
            "case_id": "case_1",
            "expected_status": "ok",
            "expected_retrieval_status": "EVIDENCE_FOUND",
            "expected_source_filenames": ["Attention is all yout need.pdf"],
            "expected_min_chunk_count": 1,
            "expected_answer_contains": ["Transformer", "attention"],
        }
        actual = {
            "status": "ok",
            "error_code": None,
            "retrieval_status": "EVIDENCE_FOUND",
            "source_filenames": ["Attention is all yout need.pdf"],
            "chunk_ids": [375],
            "response_text": "Transformer basado en attention.",
        }

        passed, checks = runner.compare_case_result(case=case, baseline_item=baseline_item, actual=actual)

        self.assertTrue(passed)
        self.assertTrue(all(check["passed"] for check in checks))

    def test_comparison_fails_when_required_source_filename_is_missing(self):
        case = {"id": "case_1", "input": "hola", "forbidden_terms": []}
        baseline_item = {
            "case_id": "case_1",
            "expected_status": "ok",
            "expected_retrieval_status": "EVIDENCE_FOUND",
            "expected_source_filenames": ["Attention is all yout need.pdf"],
            "expected_min_chunk_count": 1,
            "expected_answer_contains": [],
        }
        actual = {
            "status": "ok",
            "error_code": None,
            "retrieval_status": "EVIDENCE_FOUND",
            "source_filenames": ["other.pdf"],
            "chunk_ids": [1],
            "response_text": "ok",
        }

        passed, checks = runner.compare_case_result(case=case, baseline_item=baseline_item, actual=actual)

        self.assertFalse(passed)
        source_check = next(check for check in checks if check["name"] == "source_filenames")
        self.assertFalse(source_check["passed"])

    def test_comparison_fails_when_expected_answer_term_is_missing(self):
        case = {"id": "case_1", "input": "hola", "forbidden_terms": []}
        baseline_item = {
            "case_id": "case_1",
            "expected_status": "ok",
            "expected_retrieval_status": "EVIDENCE_FOUND",
            "expected_source_filenames": [],
            "expected_min_chunk_count": 0,
            "expected_answer_contains": ["attention"],
        }
        actual = {
            "status": "ok",
            "error_code": None,
            "retrieval_status": "EVIDENCE_FOUND",
            "source_filenames": [],
            "chunk_ids": [],
            "response_text": "Respuesta sin termino esperado.",
        }

        passed, checks = runner.compare_case_result(case=case, baseline_item=baseline_item, actual=actual)

        self.assertFalse(passed)
        answer_check = next(check for check in checks if check["name"] == "expected_answer_contains")
        self.assertFalse(answer_check["passed"])

    def test_forbidden_terms_fail_when_present(self):
        case = {"id": "case_1", "input": "hola", "forbidden_terms": ["inventado"]}
        baseline_item = {
            "case_id": "case_1",
            "expected_status": "ok",
            "expected_retrieval_status": "EVIDENCE_FOUND",
            "expected_source_filenames": [],
            "expected_min_chunk_count": 0,
            "expected_answer_contains": [],
        }
        actual = {
            "status": "ok",
            "error_code": None,
            "retrieval_status": "EVIDENCE_FOUND",
            "source_filenames": [],
            "chunk_ids": [],
            "response_text": "Termino inventado presente.",
        }

        passed, checks = runner.compare_case_result(case=case, baseline_item=baseline_item, actual=actual)

        self.assertFalse(passed)
        forbidden_check = next(check for check in checks if check["name"] == "forbidden_terms")
        self.assertFalse(forbidden_check["passed"])

    def test_run_summary_counts_total_passed_failed_errors_correctly(self):
        results = [
            {"passed": True, "status": "ok"},
            {"passed": False, "status": "ok"},
            {"passed": False, "status": "error"},
        ]

        summary = runner.summarize_results(results)

        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["passed"], 1)
        self.assertEqual(summary["failed"], 2)
        self.assertEqual(summary["errors"], 1)
        self.assertEqual(summary["pass_rate"], 0.3333)

    def test_run_filename_and_output_schema_have_required_fields(self):
        created_at = datetime(2026, 5, 15, 16, 0, 0, tzinfo=timezone.utc)
        filename = runner.build_run_filename(created_at)
        payload = runner.build_run_payload(
            run_id="run_1",
            created_at=created_at.isoformat(),
            base_url="http://127.0.0.1:8000",
            cases_path="evals/cases/chat_cases.json",
            baseline_path="evals/baselines/chat_baseline.json",
            results=[],
        )

        self.assertEqual(filename, "20260515_160000_chat_eval_run.json")
        self.assertEqual(payload["version"], "chat_eval_run.v1")
        self.assertIn("summary", payload)
        self.assertIn("results", payload)
        self.assertIn("run_id", payload)


if __name__ == "__main__":
    unittest.main()
