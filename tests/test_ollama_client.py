import os
import unittest

import requests

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

from app.adapters.ollama_client import (
    OllamaClientError,
    _error_from_response,
    ask_chat,
    generate_markdown,
)
from app.config import Settings


class FakeResponse:
    def __init__(self, status_code, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class FakeRequestsModule:
    def __init__(self, response=None, side_effect=None):
        self._response = response
        self._side_effect = side_effect
        self.last_call = None

    def post(self, url, **kwargs):
        self.last_call = {"url": url, **kwargs}
        if self._side_effect:
            raise self._side_effect
        return self._response


class ErrorFromResponseTests(unittest.TestCase):
    def test_non_json_response_returns_http_error(self):
        resp = FakeResponse(500)
        code, msg = _error_from_response(resp)
        self.assertEqual(code, "llm_http_error")

    def test_model_not_found_returns_model_not_available(self):
        resp = FakeResponse(404, {"error": "model 'xyz' not found"})
        code, msg = _error_from_response(resp)
        self.assertEqual(code, "llm_model_not_available")

    def test_model_not_available_returns_model_not_available(self):
        resp = FakeResponse(404, {"error": "model 'xyz' is not available"})
        code, msg = _error_from_response(resp)
        self.assertEqual(code, "llm_model_not_available")

    def test_generic_error_string_returns_http_error(self):
        resp = FakeResponse(500, {"error": "something went wrong"})
        code, msg = _error_from_response(resp)
        self.assertEqual(code, "llm_http_error")
        self.assertEqual(msg, "something went wrong")

    def test_non_string_error_returns_http_error(self):
        resp = FakeResponse(500, {"error": 12345})
        code, msg = _error_from_response(resp)
        self.assertEqual(code, "llm_http_error")


class GenerateMarkdownTests(unittest.TestCase):
    def _settings(self):
        return Settings(
            ollama_base_url="http://localhost:11434",
            ollama_model="test-model",
            ollama_timeout_seconds=10.0,
            temperature=0.3,
        )

    def test_success_returns_content(self):
        resp = FakeResponse(200, {"choices": [{"message": {"content": "# Title\nBody"}}]})
        req = FakeRequestsModule(response=resp)
        result = generate_markdown("write a doc", "req123", requests_module=req, settings_obj=self._settings())
        self.assertEqual(result, "# Title\nBody")

    def test_empty_prompt_raises_error(self):
        with self.assertRaises(OllamaClientError) as ctx:
            generate_markdown("", "req123", settings_obj=self._settings())
        self.assertEqual(ctx.exception.code, "llm_generation_failed")

    def test_empty_request_id_raises_error(self):
        with self.assertRaises(OllamaClientError) as ctx:
            generate_markdown("prompt", "  ", settings_obj=self._settings())
        self.assertEqual(ctx.exception.code, "llm_generation_failed")

    def test_connection_error_raises_unavailable(self):
        req = FakeRequestsModule(side_effect=requests.exceptions.ConnectionError("refused"))
        with self.assertRaises(OllamaClientError) as ctx:
            generate_markdown("prompt", "req123", requests_module=req, settings_obj=self._settings())
        self.assertEqual(ctx.exception.code, "llm_unavailable")

    def test_timeout_raises_llm_timeout(self):
        req = FakeRequestsModule(side_effect=requests.exceptions.Timeout("timed out"))
        with self.assertRaises(OllamaClientError) as ctx:
            generate_markdown("prompt", "req123", requests_module=req, settings_obj=self._settings())
        self.assertEqual(ctx.exception.code, "llm_timeout")

    def test_generic_request_error_raises_generation_failed(self):
        req = FakeRequestsModule(side_effect=requests.exceptions.RequestException("generic"))
        with self.assertRaises(OllamaClientError) as ctx:
            generate_markdown("prompt", "req123", requests_module=req, settings_obj=self._settings())
        self.assertEqual(ctx.exception.code, "llm_generation_failed")

    def test_non_200_raises_generation_failed(self):
        resp = FakeResponse(500, {"error": "internal error"})
        req = FakeRequestsModule(response=resp)
        with self.assertRaises(OllamaClientError) as ctx:
            generate_markdown("prompt", "req123", requests_module=req, settings_obj=self._settings())
        self.assertEqual(ctx.exception.code, "llm_generation_failed")

    def test_model_not_found_raises_model_not_available(self):
        resp = FakeResponse(404, {"error": "model 'xyz' not found"})
        req = FakeRequestsModule(response=resp)
        with self.assertRaises(OllamaClientError) as ctx:
            generate_markdown("prompt", "req123", requests_module=req, settings_obj=self._settings())
        self.assertEqual(ctx.exception.code, "llm_model_not_available")

    def test_invalid_json_response_raises_invalid_json(self):
        resp = FakeResponse(200)
        req = FakeRequestsModule(response=resp)
        with self.assertRaises(OllamaClientError) as ctx:
            generate_markdown("prompt", "req123", requests_module=req, settings_obj=self._settings())
        self.assertEqual(ctx.exception.code, "llm_invalid_json")

    def test_missing_content_key_raises_invalid_response(self):
        resp = FakeResponse(200, {"choices": [{"message": {}}]})
        req = FakeRequestsModule(response=resp)
        with self.assertRaises(OllamaClientError) as ctx:
            generate_markdown("prompt", "req123", requests_module=req, settings_obj=self._settings())
        self.assertEqual(ctx.exception.code, "llm_invalid_response")

    def test_non_string_content_raises_invalid_response(self):
        resp = FakeResponse(200, {"choices": [{"message": {"content": 42}}]})
        req = FakeRequestsModule(response=resp)
        with self.assertRaises(OllamaClientError) as ctx:
            generate_markdown("prompt", "req123", requests_module=req, settings_obj=self._settings())
        self.assertEqual(ctx.exception.code, "llm_invalid_response")


class AskChatTests(unittest.TestCase):
    def _settings(self):
        return Settings(
            ollama_base_url="http://localhost:11434",
            ollama_model="test-model",
            ollama_timeout_seconds=10.0,
            temperature=0.3,
        )

    def _ok_response(self, content="respuesta", model="test-model"):
        return FakeResponse(200, {
            "message": {"content": content},
            "model": model,
            "prompt_eval_count": 10,
            "eval_count": 5,
            "prompt_eval_duration": 100,
            "eval_duration": 200,
            "total_duration": 400,
            "load_duration": 50,
        })

    def test_empty_message_raises_error(self):
        with self.assertRaises(OllamaClientError) as ctx:
            ask_chat("", settings_obj=self._settings())
        self.assertEqual(ctx.exception.code, "llm_generation_failed")

    def test_success_returns_dict_with_answer(self):
        resp = self._ok_response()
        req = FakeRequestsModule(response=resp)
        result = ask_chat("hola", requests_module=req, settings_obj=self._settings())
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["answer"], "respuesta")
        self.assertEqual(result["provider"], "ollama")
        self.assertEqual(result["model"], "test-model")
        self.assertEqual(result["temperature"], 0.3)
        self.assertFalse(result["temperature_ignored"])
        self.assertEqual(result["prompt_eval_count"], 10)
        self.assertEqual(result["eval_count"], 5)

    def test_custom_model_and_temperature(self):
        resp = self._ok_response(model="custom")
        req = FakeRequestsModule(response=resp)
        result = ask_chat("hola", model="custom", temperature=0.9, requests_module=req, settings_obj=self._settings())
        self.assertEqual(result["model"], "custom")
        self.assertEqual(result["temperature"], 0.9)

    def test_system_prompt_included_in_messages(self):
        resp = self._ok_response()
        req = FakeRequestsModule(response=resp)
        ask_chat("hola", system_prompt="You are helpful", requests_module=req, settings_obj=self._settings())
        payload = req.last_call["json"]
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(payload["messages"][0]["content"], "You are helpful")

    def test_no_system_prompt_skips_system_message(self):
        resp = self._ok_response()
        req = FakeRequestsModule(response=resp)
        ask_chat("hola", requests_module=req, settings_obj=self._settings())
        payload = req.last_call["json"]
        self.assertEqual(len(payload["messages"]), 1)
        self.assertEqual(payload["messages"][0]["role"], "user")

    def test_connection_error_raises_unavailable(self):
        req = FakeRequestsModule(side_effect=requests.exceptions.ConnectionError("refused"))
        with self.assertRaises(OllamaClientError) as ctx:
            ask_chat("hola", requests_module=req, settings_obj=self._settings())
        self.assertEqual(ctx.exception.code, "llm_unavailable")

    def test_timeout_raises_llm_timeout(self):
        req = FakeRequestsModule(side_effect=requests.exceptions.Timeout("timed out"))
        with self.assertRaises(OllamaClientError) as ctx:
            ask_chat("hola", requests_module=req, settings_obj=self._settings())
        self.assertEqual(ctx.exception.code, "llm_timeout")

    def test_generic_request_error_raises_http_error(self):
        req = FakeRequestsModule(side_effect=requests.exceptions.RequestException("generic"))
        with self.assertRaises(OllamaClientError) as ctx:
            ask_chat("hola", requests_module=req, settings_obj=self._settings())
        self.assertEqual(ctx.exception.code, "llm_http_error")

    def test_non_200_raises_error_from_response(self):
        resp = FakeResponse(500, {"error": "internal error"})
        req = FakeRequestsModule(response=resp)
        with self.assertRaises(OllamaClientError) as ctx:
            ask_chat("hola", requests_module=req, settings_obj=self._settings())
        self.assertEqual(ctx.exception.code, "llm_http_error")

    def test_invalid_json_raises_invalid_json(self):
        resp = FakeResponse(200)
        req = FakeRequestsModule(response=resp)
        with self.assertRaises(OllamaClientError) as ctx:
            ask_chat("hola", requests_module=req, settings_obj=self._settings())
        self.assertEqual(ctx.exception.code, "llm_invalid_json")

    def test_missing_message_content_raises_error(self):
        resp = FakeResponse(200, {"model": "test", "other": "data"})
        req = FakeRequestsModule(response=resp)
        with self.assertRaises(OllamaClientError) as ctx:
            ask_chat("hola", requests_module=req, settings_obj=self._settings())
        self.assertEqual(ctx.exception.code, "llm_missing_content")

    def test_empty_content_raises_missing_content(self):
        resp = FakeResponse(200, {"message": {"content": "  "}, "model": "test"})
        req = FakeRequestsModule(response=resp)
        with self.assertRaises(OllamaClientError) as ctx:
            ask_chat("hola", requests_module=req, settings_obj=self._settings())
        self.assertEqual(ctx.exception.code, "llm_missing_content")

    def test_missing_response_model_uses_selected_model(self):
        resp = FakeResponse(200, {"message": {"content": "answer"}})
        req = FakeRequestsModule(response=resp)
        result = ask_chat("hola", model="fallback", requests_module=req, settings_obj=self._settings())
        self.assertEqual(result["model"], "fallback")

    def test_num_predict_passed_in_options(self):
        resp = self._ok_response()
        req = FakeRequestsModule(response=resp)
        ask_chat("hola", num_predict=42, requests_module=req, settings_obj=self._settings())
        payload = req.last_call["json"]
        self.assertEqual(payload["options"]["num_predict"], 42)

    def test_default_num_predict_is_300(self):
        resp = self._ok_response()
        req = FakeRequestsModule(response=resp)
        ask_chat("hola", requests_module=req, settings_obj=self._settings())
        payload = req.last_call["json"]
        self.assertEqual(payload["options"]["num_predict"], 300)


if __name__ == "__main__":
    unittest.main()
