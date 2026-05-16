import unittest

from app.evals.metrics import compute_by_model, compute_summary, percentile, safe_mean
from app.evals.schemas import RunRecord


class RunsMetricsTests(unittest.TestCase):
    def test_safe_mean_ignores_none(self):
        self.assertEqual(safe_mean([10, None, 20]), 15.0)

    def test_percentiles_are_calculated(self):
        values = [10, 20, 30, 40, 50]
        self.assertEqual(percentile(values, 50), 30.0)
        self.assertEqual(percentile(values, 95), 48.0)

    def test_error_rate_is_calculated(self):
        runs = [
            RunRecord(model="m1", status="ok"),
            RunRecord(model="m1", status="error", error_code="boom"),
        ]
        summary = compute_summary(runs)
        self.assertEqual(summary["error_rate"], 0.5)

    def test_fallback_and_no_evidence_rates_are_calculated(self):
        runs = [
            RunRecord(model="m1", status="ok", fallback_used=True, retrieval_status="NO_EVIDENCE"),
            RunRecord(model="m1", status="ok", fallback_used=False, retrieval_status="EVIDENCE_FOUND"),
        ]
        metrics = compute_by_model(runs)[0]
        self.assertEqual(metrics.fallback_rate, 0.5)
        self.assertEqual(metrics.no_evidence_rate, 0.5)

    def test_grouping_by_model(self):
        runs = [
            RunRecord(model="granite4.1:8b", status="ok", latency_ms=100, tokens_total=10),
            RunRecord(model="granite4.1:8b", status="ok", latency_ms=300, tokens_total=30),
            RunRecord(model="gpt-5.5", status="error", error_code="failure"),
        ]
        by_model = compute_by_model(runs)

        self.assertEqual(len(by_model), 2)
        granite_metrics = next(item for item in by_model if item.model == "granite4.1:8b")
        self.assertEqual(granite_metrics.runs, 2)
        self.assertEqual(granite_metrics.avg_latency_ms, 200.0)
        self.assertEqual(granite_metrics.avg_tokens_total, 20.0)

    def test_summary_ignores_none_numeric_values(self):
        runs = [
            RunRecord(model="m1", status="ok", latency_ms=None),
            RunRecord(model="m1", status="ok", latency_ms=200),
        ]
        metrics = compute_by_model(runs)[0]
        self.assertEqual(metrics.avg_latency_ms, 200.0)
