import unittest

from app.chat_runs.metrics import group_by_model, group_by_provider, percentile, summarize_runs


class ChatRunsMetricsTests(unittest.TestCase):
    def test_percentile_ignores_none_values(self):
        self.assertEqual(percentile([100, None, 300], 50), 200.0)
        self.assertEqual(percentile([], 95), None)

    def test_summarize_runs_ignores_missing_metrics_and_keeps_nulls(self):
        runs = [
            {
                "trace_id": "r1",
                "provider": "ollama",
                "model": "granite4.1:8b",
                "status": "ok",
                "use_rag": True,
                "retrieval_status": "EVIDENCE_FOUND",
                "fallback_used": False,
                "latency_ms": 100,
                "output_tokens_per_second": 20,
            },
            {
                "trace_id": "r2",
                "provider": "openai",
                "model": "gpt-5.5",
                "status": "ok",
                "use_rag": True,
                "retrieval_status": None,
                "fallback_used": True,
                "latency_ms": None,
                "output_tokens_per_second": None,
            },
            {
                "trace_id": "r3",
                "provider": "openai",
                "model": "gpt-5.5",
                "status": "error",
                "use_rag": False,
                "fallback_used": False,
                "latency_ms": 400,
                "output_tokens_per_second": None,
            },
        ]

        summary = summarize_runs(runs)

        self.assertEqual(summary["total_runs"], 3)
        self.assertEqual(summary["ok_runs"], 2)
        self.assertEqual(summary["error_runs"], 1)
        self.assertEqual(summary["error_rate"], 0.3333)
        self.assertEqual(summary["avg_latency_ms"], 250.0)
        self.assertEqual(summary["p50_latency_ms"], 250.0)
        self.assertEqual(summary["avg_tokens_per_second"], 20.0)
        self.assertEqual(summary["fallback_rate"], 0.3333)
        self.assertEqual(summary["rag_hit_rate"], 0.5)

    def test_group_by_model_and_provider(self):
        runs = [
            {"model": "granite4.1:8b", "provider": "ollama", "status": "ok", "latency_ms": 100},
            {"model": "granite4.1:8b", "provider": "ollama", "status": "error", "latency_ms": 300},
            {"model": "gpt-5.5", "provider": "openai", "status": "ok", "latency_ms": None},
        ]

        by_model = group_by_model(runs)
        by_provider = group_by_provider(runs)

        self.assertEqual([item["model"] for item in by_model], ["granite4.1:8b", "gpt-5.5"])
        self.assertEqual(by_model[0]["avg_latency_ms"], 200.0)
        self.assertEqual(by_model[1]["avg_latency_ms"], None)
        self.assertEqual([item["provider"] for item in by_provider], ["ollama", "openai"])
        self.assertEqual(by_provider[0]["error_rate"], 0.5)
