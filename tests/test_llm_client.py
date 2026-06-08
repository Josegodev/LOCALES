import os
import unittest
from unittest.mock import patch

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

from app.llm_client import (
    LLMClientError,
    _is_openai_model,
    _normalize_model_name,
    resolve_provider_model,
)


class NormalizeModelNameTests(unittest.TestCase):
    def test_none_returns_none(self):
        self.assertIsNone(_normalize_model_name(None))

    def test_non_string_returns_none(self):
        self.assertIsNone(_normalize_model_name(123))

    def test_empty_string_returns_none(self):
        self.assertIsNone(_normalize_model_name(""))

    def test_whitespace_returns_none(self):
        self.assertIsNone(_normalize_model_name("   "))

    def test_strips_whitespace(self):
        self.assertEqual(_normalize_model_name("  gpt-5  "), "gpt-5")


class IsOpenaiModelTests(unittest.TestCase):
    def test_gpt_prefix(self):
        self.assertTrue(_is_openai_model("gpt-5.5"))

    def test_supported_model(self):
        self.assertTrue(_is_openai_model("gpt-4o-mini"))

    def test_non_openai_model(self):
        self.assertFalse(_is_openai_model("granite4.1:8b"))


class ResolveProviderModelTests(unittest.TestCase):
    def test_default_provider_is_ollama(self):
        provider, model = resolve_provider_model(None, None)
        self.assertEqual(provider, "ollama")

    def test_ollama_provider_with_default_model(self):
        provider, model = resolve_provider_model("ollama", None)
        self.assertEqual(provider, "ollama")
        self.assertIsInstance(model, str)

    def test_ollama_provider_with_custom_model(self):
        provider, model = resolve_provider_model("ollama", "my-model")
        self.assertEqual(model, "my-model")

    def test_ollama_rejects_openai_model(self):
        with self.assertRaises(LLMClientError) as ctx:
            resolve_provider_model("ollama", "gpt-5.5")
        self.assertEqual(ctx.exception.code, "invalid_provider_model_pair")

    def test_openai_provider_with_valid_model(self):
        provider, model = resolve_provider_model("openai", "gpt-5.5")
        self.assertEqual(provider, "openai")
        self.assertEqual(model, "gpt-5.5")

    def test_openai_provider_with_default_model(self):
        provider, model = resolve_provider_model("openai", None)
        self.assertEqual(provider, "openai")

    def test_openai_rejects_non_openai_model(self):
        with self.assertRaises(LLMClientError) as ctx:
            resolve_provider_model("openai", "granite4.1:8b")
        self.assertEqual(ctx.exception.code, "invalid_provider_model_pair")

    def test_unsupported_provider_raises_error(self):
        with self.assertRaises(LLMClientError) as ctx:
            resolve_provider_model("anthropic", None)
        self.assertEqual(ctx.exception.code, "llm_provider_error")

    def test_provider_is_case_insensitive(self):
        provider, _ = resolve_provider_model("OLLAMA", None)
        self.assertEqual(provider, "ollama")

    def test_provider_strips_whitespace(self):
        provider, _ = resolve_provider_model("  ollama  ", None)
        self.assertEqual(provider, "ollama")


if __name__ == "__main__":
    unittest.main()
