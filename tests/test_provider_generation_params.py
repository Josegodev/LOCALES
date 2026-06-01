import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests

from app.adapters import ollama_client, openai_client


class _FakeOllamaResponse:
    status_code = 200

    def json(self):
        return {
            "model": "granite4.1:8b",
            "message": {"content": "ok"},
            "prompt_eval_count": 12,
            "eval_count": 20,
        }


class ProviderGenerationParamsTests(unittest.TestCase):
    def test_ollama_receives_temperature_top_p_and_top_k(self):
        requests_module = SimpleNamespace(
            post=Mock(return_value=_FakeOllamaResponse()),
            exceptions=requests.exceptions,
        )
        settings_obj = SimpleNamespace(
            temperature=0.2,
            max_tokens=512,
            ollama_api_base_url=lambda: "http://ollama.local",
            effective_ollama_timeout_seconds=lambda: 45.0,
        )

        result = ollama_client.ask_chat(
            "hola",
            model="granite4.1:8b",
            temperature=0.2,
            top_p=0.9,
            top_k=40,
            requests_module=requests_module,
            settings_obj=settings_obj,
        )

        payload = requests_module.post.call_args.kwargs["json"]
        self.assertEqual(payload["options"]["temperature"], 0.2)
        self.assertEqual(payload["options"]["top_p"], 0.9)
        self.assertEqual(payload["options"]["top_k"], 40)
        self.assertEqual(result["top_p"], 0.9)
        self.assertEqual(result["top_k"], 40)

    def test_openai_forwards_top_p_and_ignores_top_k(self):
        create_mock = Mock(return_value=SimpleNamespace(output_text="ok"))
        client = SimpleNamespace(responses=SimpleNamespace(create=create_mock))
        settings_obj = SimpleNamespace(
            temperature=0.2,
            max_tokens=512,
            llm_timeout_seconds=60.0,
            openai_api_key="test-key",
        )

        with patch("app.adapters.openai_client._build_client", return_value=client):
            result = openai_client.ask_chat(
                "hola",
                model="gpt-5.5",
                temperature=0.2,
                top_p=0.9,
                top_k=40,
                settings_obj=settings_obj,
            )

        payload = create_mock.call_args.kwargs
        self.assertEqual(payload["temperature"], 0.2)
        self.assertEqual(payload["top_p"], 0.9)
        self.assertNotIn("top_k", payload)
        self.assertIsNone(result["top_k"])


if __name__ == "__main__":
    unittest.main()
