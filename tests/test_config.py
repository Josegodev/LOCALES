import os
import unittest
from unittest.mock import patch

from app.config import Settings


class SettingsUrlMethodsTests(unittest.TestCase):
    def test_lmstudio_v1_base_url_appends_v1(self):
        s = Settings(lmstudio_base_url="http://localhost:1234")
        self.assertEqual(s.lmstudio_v1_base_url(), "http://localhost:1234/v1")

    def test_lmstudio_v1_base_url_does_not_duplicate_v1(self):
        s = Settings(lmstudio_base_url="http://localhost:1234/v1")
        self.assertEqual(s.lmstudio_v1_base_url(), "http://localhost:1234/v1")

    def test_lmstudio_v1_base_url_strips_trailing_slash(self):
        s = Settings(lmstudio_base_url="http://localhost:1234/")
        self.assertEqual(s.lmstudio_v1_base_url(), "http://localhost:1234/v1")

    def test_ollama_api_base_url_strips_v1_suffix(self):
        s = Settings(ollama_base_url="http://localhost:11434/v1")
        self.assertEqual(s.ollama_api_base_url(), "http://localhost:11434")

    def test_ollama_api_base_url_returns_base_when_no_v1(self):
        s = Settings(ollama_base_url="http://localhost:11434")
        self.assertEqual(s.ollama_api_base_url(), "http://localhost:11434")

    def test_ollama_v1_base_url_appends_v1(self):
        s = Settings(ollama_base_url="http://localhost:11434")
        self.assertEqual(s.ollama_v1_base_url(), "http://localhost:11434/v1")

    def test_ollama_v1_base_url_does_not_duplicate_v1(self):
        s = Settings(ollama_base_url="http://localhost:11434/v1")
        self.assertEqual(s.ollama_v1_base_url(), "http://localhost:11434/v1")

    def test_effective_ollama_model_returns_configured_model(self):
        s = Settings(ollama_model="my-model:latest")
        self.assertEqual(s.effective_ollama_model(), "my-model:latest")

    def test_effective_ollama_timeout_seconds_returns_configured_value(self):
        s = Settings(ollama_timeout_seconds=99.0)
        self.assertEqual(s.effective_ollama_timeout_seconds(), 99.0)


if __name__ == "__main__":
    unittest.main()
