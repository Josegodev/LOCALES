import unittest
from unittest.mock import Mock, patch

from app import llm_client
from app.main import app


class ChatOnlyRuntimeTests(unittest.TestCase):
    def test_main_module_imports_without_telegram_env_vars(self):
        __import__("app.main")

    def test_fastapi_routes_do_not_expose_telegram_or_eval_endpoints(self):
        paths = {route.path for route in app.routes}

        self.assertIn("/health", paths)
        self.assertIn("/api/models/chat", paths)
        self.assertIn("/api/chat/options", paths)
        self.assertIn("/chat", paths)
        self.assertIn("/api/chat/runs", paths)
        self.assertIn("/api/runs", paths)
        self.assertIn("/api/runs/summary", paths)
        self.assertIn("/api/runs/operational-stats", paths)
        self.assertIn("/api/runs/timeseries", paths)
        self.assertIn("/api/evals/chat", paths)
        self.assertIn("/api/evals/chat/run", paths)
        self.assertIn("/api/evals/runs", paths)
        self.assertIn("/api/traces/chat", paths)
        self.assertNotIn("/api/evals/telegram", paths)
        self.assertFalse(any(path.startswith("/telegram") for path in paths))

    def test_llm_client_passes_requests_module_to_ollama_adapter(self):
        fake_requests = Mock()

        with patch.object(llm_client, "requests", fake_requests), patch(
            "app.llm_client._list_ollama_models",
            return_value=["granite4.1:8b"],
        ) as list_models_mock, patch(
            "app.llm_client._ask_chat",
            return_value={"status": "ok", "answer": "hola"},
        ) as ask_chat_mock:
            result = llm_client.ask_chat("hola", provider="ollama")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(ask_chat_mock.call_args.kwargs["model"], "granite4.1:8b")
        self.assertIs(ask_chat_mock.call_args.kwargs["requests_module"], fake_requests)
        list_models_mock.assert_called_once_with()
        fake_requests.get.assert_not_called()
        fake_requests.post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
