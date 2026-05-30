import unittest
from unittest.mock import patch

from app.llm_client import LLMClientError, resolve_provider_model


class ProviderModelResolutionTests(unittest.TestCase):
    def test_ollama_provider_rejects_openai_model_name(self):
        with self.assertRaises(LLMClientError) as context:
            resolve_provider_model("ollama", "gpt-5.5")

        self.assertEqual(context.exception.code, "invalid_provider_model_pair")

    def test_openai_provider_rejects_ollama_model_name(self):
        with self.assertRaises(LLMClientError) as context:
            resolve_provider_model("openai", "granite4.1:8b")

        self.assertEqual(context.exception.code, "invalid_provider_model_pair")

    def test_openai_provider_uses_default_model_when_missing(self):
        provider, model = resolve_provider_model("openai", None)

        self.assertEqual(provider, "openai")
        self.assertEqual(model, "gpt-5.5")

    def test_ollama_provider_resolves_unique_prefix_match(self):
        with patch("app.llm_client._list_ollama_models", return_value=["granite4.1:8b", "mistral:latest"]):
            provider, model = resolve_provider_model("ollama", "granite")

        self.assertEqual(provider, "ollama")
        self.assertEqual(model, "granite4.1:8b")


if __name__ == "__main__":
    unittest.main()
