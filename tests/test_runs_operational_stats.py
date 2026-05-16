import unittest

from app.evals.metrics import (
    build_model_operational_stats,
    build_model_temperature_operational_stats,
)


class RunsOperationalStatsTests(unittest.TestCase):
    def test_groups_runs_by_model(self):
        runs = [
            {"model": "m1", "status": "ok"},
            {"model": "m1", "status": "error", "error_code": "boom"},
            {"model": "m2", "status": "ok"},
        ]

        stats = build_model_operational_stats(runs)

        self.assertEqual([item.model for item in stats], ["m1", "m2"])
        self.assertEqual(stats[0].runs, 2)
        self.assertEqual(stats[1].runs, 1)

    def test_counts_total_runs_even_with_incomplete_fields(self):
        runs = [
            {"model": "m1"},
            {"model": "m1", "latency_ms": 100},
            {"model": "m1", "tokens_output": 50},
        ]

        metrics = build_model_operational_stats(runs)[0]

        self.assertEqual(metrics.runs, 3)

    def test_calculates_avg_latency_ms(self):
        runs = [
            {"model": "m1", "latency_ms": 100},
            {"model": "m1", "latency_ms": 300},
        ]

        metrics = build_model_operational_stats(runs)[0]

        self.assertEqual(metrics.avg_latency_ms, 200.0)

    def test_calculates_p50_latency_ms(self):
        runs = [
            {"model": "m1", "latency_ms": 100},
            {"model": "m1", "latency_ms": 200},
            {"model": "m1", "latency_ms": 300},
        ]

        metrics = build_model_operational_stats(runs)[0]

        self.assertEqual(metrics.p50_latency_ms, 200.0)

    def test_calculates_p95_latency_ms(self):
        runs = [
            {"model": "m1", "latency_ms": 100},
            {"model": "m1", "latency_ms": 200},
            {"model": "m1", "latency_ms": 300},
            {"model": "m1", "latency_ms": 400},
            {"model": "m1", "latency_ms": 500},
        ]

        metrics = build_model_operational_stats(runs)[0]

        self.assertEqual(metrics.p95_latency_ms, 480.0)

    def test_ignores_missing_or_non_numeric_latency(self):
        runs = [
            {"model": "m1", "latency_ms": None},
            {"model": "m1", "latency_ms": "slow"},
            {"model": "m1", "latency_ms": 200},
        ]

        metrics = build_model_operational_stats(runs)[0]

        self.assertEqual(metrics.samples_valid_latency, 1)
        self.assertEqual(metrics.avg_latency_ms, 200.0)

    def test_calculates_success_rate_and_error_rate(self):
        runs = [
            {"model": "m1", "status": "ok"},
            {"model": "m1", "status": "error", "error_code": "boom"},
        ]

        metrics = build_model_operational_stats(runs)[0]

        self.assertEqual(metrics.success_rate, 0.5)
        self.assertEqual(metrics.error_rate, 0.5)
        self.assertEqual(metrics.timeout_rate, 0.0)

    def test_detects_timeout_by_status(self):
        runs = [{"model": "m1", "status": "timeout"}]

        metrics = build_model_operational_stats(runs)[0]

        self.assertEqual(metrics.timeout_count, 1)
        self.assertEqual(metrics.error_count, 0)

    def test_detects_timeout_by_error_type(self):
        runs = [{"model": "m1", "status": "error", "error_type": "timeout"}]

        metrics = build_model_operational_stats(runs)[0]

        self.assertEqual(metrics.timeout_count, 1)
        self.assertEqual(metrics.error_count, 0)

    def test_detects_timeout_by_latency_threshold(self):
        runs = [{"model": "m1", "status": "ok", "latency_ms": 10001}]

        metrics = build_model_operational_stats(runs, timeout_ms=10000)[0]

        self.assertEqual(metrics.timeout_count, 1)
        self.assertEqual(metrics.ok_count, 0)

    def test_calculates_tokens_per_second_only_for_ok_runs(self):
        runs = [
            {"model": "m1", "status": "ok", "latency_ms": 2000, "tokens_output": 100},
            {"model": "m1", "status": "error", "latency_ms": 1000, "tokens_output": 500},
        ]

        metrics = build_model_operational_stats(runs)[0]

        self.assertEqual(metrics.avg_tokens_per_second, 50.0)
        self.assertEqual(metrics.p50_tokens_per_second, 50.0)

    def test_does_not_crash_when_tokens_output_is_missing(self):
        runs = [
            {"model": "m1", "status": "ok", "latency_ms": 1000},
            {"model": "m1", "status": "ok", "latency_ms": 1200, "tokens_output": 24},
        ]

        metrics = build_model_operational_stats(runs)[0]

        self.assertEqual(metrics.avg_tokens_per_second, 20.0)

    def test_returns_null_when_no_valid_numeric_data(self):
        runs = [
            {"model": "m1", "status": "ok", "latency_ms": None, "tokens_total": None},
            {"model": "m1", "status": "error", "latency_ms": "bad", "tokens_total": "bad"},
        ]

        metrics = build_model_operational_stats(runs)[0]

        self.assertIsNone(metrics.avg_latency_ms)
        self.assertIsNone(metrics.p95_latency_ms)
        self.assertIsNone(metrics.avg_tokens_total)
        self.assertIsNone(metrics.avg_tokens_per_second)

    def test_keeps_compatibility_with_legacy_runs(self):
        runs = [
            {"model": "legacy", "status": "ok", "tokens_input": 10, "tokens_output": 5, "latency_ms": 100},
            {"model": "legacy", "status": "ok", "tokens_input": 30, "tokens_output": 15, "latency_ms": 200},
        ]

        metrics = build_model_operational_stats(runs)[0]

        self.assertEqual(metrics.samples_valid_tokens, 2)
        self.assertEqual(metrics.avg_tokens_total, 30.0)
        self.assertEqual(metrics.p50_tokens_total, 30.0)

    def test_groups_by_model_and_temperature(self):
        runs = [
            {"model": "m1", "temperature": 0.2, "status": "ok", "latency_ms": 100},
            {"model": "m1", "temperature": 0.7, "status": "ok", "latency_ms": 200},
            {"model": "m1", "temperature": 0.2, "status": "ok", "latency_ms": 300},
        ]

        stats = build_model_temperature_operational_stats(runs)

        self.assertEqual(len(stats), 2)
        first = next(item for item in stats if item.temperature == 0.2)
        second = next(item for item in stats if item.temperature == 0.7)
        self.assertEqual(first.runs, 2)
        self.assertEqual(second.runs, 1)
        self.assertEqual(first.p50_latency_ms, 200.0)

    def test_legacy_runs_without_temperature_are_grouped_as_null(self):
        runs = [
            {"model": "legacy", "status": "ok", "latency_ms": 100},
            {"model": "legacy", "temperature": 0.2, "status": "ok", "latency_ms": 200},
        ]

        stats = build_model_temperature_operational_stats(runs)

        self.assertEqual(len(stats), 2)
        null_group = next(item for item in stats if item.temperature is None)
        explicit_group = next(item for item in stats if item.temperature == 0.2)
        self.assertEqual(null_group.runs, 1)
        self.assertEqual(explicit_group.runs, 1)


if __name__ == "__main__":
    unittest.main()
