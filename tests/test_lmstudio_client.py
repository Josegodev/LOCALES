import os
import unittest
from unittest.mock import MagicMock, patch

import requests

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

from app.lmstudio_client import LLMError, ask_lmstudio


class FakeResponse:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class AskLmstudioTests(unittest.TestCase):
    def _ok_response(self, answer="respuesta ok"):
        return FakeResponse(
            200,
            {
                "choices": [{"message": {"content": answer}, "finish_reason": "stop"}],
                "model": "granite",
            },
        )

    @patch("app.lmstudio_client.requests")
    def test_returns_answer_on_success(self, mock_requests):
        mock_requests.post.return_value = self._ok_response("hola mundo")
        result = ask_lmstudio("pregunta")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["answer"], "hola mundo")
        self.assertIn("latency_ms", result)
        mock_requests.post.assert_called_once()

    @patch("app.lmstudio_client.requests")
    def test_uses_custom_model(self, mock_requests):
        mock_requests.post.return_value = self._ok_response()
        result = ask_lmstudio("pregunta", model="custom-model")
        self.assertEqual(result["model"], "custom-model")

    @patch("app.lmstudio_client.requests")
    def test_connection_error_raises_lmstudio_unavailable(self, mock_requests):
        mock_requests.post.side_effect = requests.exceptions.ConnectionError("refused")
        mock_requests.exceptions = requests.exceptions
        with self.assertRaises(LLMError) as ctx:
            ask_lmstudio("pregunta")
        self.assertEqual(ctx.exception.code, "LMSTUDIO_UNAVAILABLE")

    @patch("app.lmstudio_client.requests")
    def test_timeout_raises_timeout_error(self, mock_requests):
        mock_requests.post.side_effect = requests.exceptions.Timeout("timed out")
        mock_requests.exceptions = requests.exceptions
        with self.assertRaises(LLMError) as ctx:
            ask_lmstudio("pregunta")
        self.assertEqual(ctx.exception.code, "TIMEOUT")

    @patch("app.lmstudio_client.requests")
    def test_generic_request_exception_raises_http_error(self, mock_requests):
        mock_requests.post.side_effect = requests.exceptions.RequestException("generic")
        mock_requests.exceptions = requests.exceptions
        with self.assertRaises(LLMError) as ctx:
            ask_lmstudio("pregunta")
        self.assertEqual(ctx.exception.code, "HTTP_ERROR")

    @patch("app.lmstudio_client.requests")
    def test_non_200_status_raises_lmstudio_http_error(self, mock_requests):
        mock_requests.post.return_value = FakeResponse(500, text="internal error")
        mock_requests.exceptions = requests.exceptions
        with self.assertRaises(LLMError) as ctx:
            ask_lmstudio("pregunta")
        self.assertEqual(ctx.exception.code, "LMSTUDIO_HTTP_ERROR")

    @patch("app.lmstudio_client.requests")
    def test_malformed_json_raises_invalid_response(self, mock_requests):
        mock_requests.post.return_value = FakeResponse(200, payload={"bad": "shape"})
        mock_requests.exceptions = requests.exceptions
        with self.assertRaises(LLMError) as ctx:
            ask_lmstudio("pregunta")
        self.assertEqual(ctx.exception.code, "INVALID_RESPONSE")

    @patch("app.lmstudio_client.requests")
    def test_empty_content_raises_empty_response(self, mock_requests):
        mock_requests.post.return_value = FakeResponse(
            200,
            {
                "choices": [{"message": {"content": ""}, "finish_reason": "stop"}],
                "model": "granite",
            },
        )
        mock_requests.exceptions = requests.exceptions
        with self.assertRaises(LLMError) as ctx:
            ask_lmstudio("pregunta")
        self.assertEqual(ctx.exception.code, "EMPTY_RESPONSE")

    @patch("app.lmstudio_client.requests")
    def test_none_content_raises_empty_response(self, mock_requests):
        mock_requests.post.return_value = FakeResponse(
            200,
            {
                "choices": [{"message": {"content": None, "reasoning_content": "thinking..."}, "finish_reason": "stop"}],
                "model": "granite",
            },
        )
        mock_requests.exceptions = requests.exceptions
        with self.assertRaises(LLMError) as ctx:
            ask_lmstudio("pregunta")
        self.assertEqual(ctx.exception.code, "EMPTY_RESPONSE")

    @patch("app.lmstudio_client.requests")
    def test_custom_temperature_and_max_tokens_passed_to_payload(self, mock_requests):
        mock_requests.post.return_value = self._ok_response()
        mock_requests.exceptions = requests.exceptions
        ask_lmstudio("pregunta", temperature=0.8, max_tokens=100)
        call_payload = mock_requests.post.call_args.kwargs["json"]
        self.assertEqual(call_payload["temperature"], 0.8)
        self.assertEqual(call_payload["max_tokens"], 100)


if __name__ == "__main__":
    unittest.main()
