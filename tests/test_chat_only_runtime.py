import unittest
from unittest.mock import patch

from app import llm_client
from app.main import app


class ChatOnlyRuntimeTests(unittest.TestCase):
    def test_main_module_imports_without_telegram_env_vars(self):
        __import__("app.main")

    def test_fastapi_routes_do_not_expose_telegram_or_eval_endpoints(self):
        paths = {route.path for route in app.routes}

        self.assertIn("/health", paths)
        self.assertIn("/api/models/chat", paths)
        self.assertIn("/chat", paths)
        self.assertIn("/api/chat/runs", paths)
        self.assertIn("/api/runs", paths)
        self.assertIn("/api/runs/summary", paths)
        self.assertIn("/api/runs/timeseries", paths)
        self.assertIn("/api/evals/chat", paths)
        self.assertIn("/api/evals/chat/run", paths)
        self.assertIn("/api/evals/runs", paths)
        self.assertIn("/api/traces/chat", paths)
        self.assertNotIn("/api/evals/telegram", paths)
        self.assertFalse(any(path.startswith("/telegram") for path in paths))

    def test_llm_client_passes_requests_module_to_ollama_adapter(self):
        with patch(
            "app.llm_client._ask_chat",
            return_value={"status": "ok", "answer": "hola"},
        ) as ask_chat_mock:
            result = llm_client.ask_chat("hola", provider="ollama")

        self.assertEqual(result["status"], "ok")
        self.assertIs(ask_chat_mock.call_args.kwargs["requests_module"], llm_client.requests)


if __name__ == "__main__":
    unittest.main()
