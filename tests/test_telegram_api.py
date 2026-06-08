import os
import unittest

import requests

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

from app.adapters.telegram_api import (
    TelegramApiError,
    _bot_token,
    _truncate_response_body,
    _safe_response_json,
    _safe_response_body,
    _extract_retry_after,
    classify_telegram_http_error,
    classify_telegram_request_error,
    get_updates,
    send_message,
)


class FakeResponse:
    def __init__(self, status_code, payload=None, text="", url="", headers=None):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.url = url
        self.headers = headers or {}

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            exc = requests.exceptions.HTTPError(response=self)
            raise exc


class FakeRequestsModule:
    def __init__(self, response=None):
        self._response = response
        self.last_call = None
        self.last_method = None

    def get(self, url, **kwargs):
        self.last_method = "get"
        self.last_call = {"url": url, **kwargs}
        return self._response

    def post(self, url, **kwargs):
        self.last_method = "post"
        self.last_call = {"url": url, **kwargs}
        return self._response


class BotTokenTests(unittest.TestCase):
    def test_explicit_token_is_used(self):
        self.assertEqual(_bot_token("my-explicit-token"), "my-explicit-token")

    def test_missing_token_raises_error(self):
        from unittest.mock import patch
        from app.config import Settings
        s = Settings(telegram_bot_token=None)
        with patch("app.adapters.telegram_api.settings", s):
            with self.assertRaises(TelegramApiError) as ctx:
                _bot_token(None)
            self.assertEqual(ctx.exception.code, "telegram_token_missing")


class TruncateResponseBodyTests(unittest.TestCase):
    def test_short_body_returned_as_is(self):
        self.assertEqual(_truncate_response_body("short", 10), "short")

    def test_long_body_truncated(self):
        self.assertEqual(len(_truncate_response_body("x" * 600, 500)), 500)


class SafeResponseJsonTests(unittest.TestCase):
    def test_valid_json_dict(self):
        resp = FakeResponse(200, {"ok": True})
        self.assertEqual(_safe_response_json(resp), {"ok": True})

    def test_invalid_json_returns_none(self):
        resp = FakeResponse(200)
        self.assertIsNone(_safe_response_json(resp))

    def test_non_dict_json_returns_none(self):
        resp = FakeResponse(200, payload=[1, 2, 3])
        # This won't return a list, should be None
        result = _safe_response_json(resp)
        self.assertIsNone(result)


class SafeResponseBodyTests(unittest.TestCase):
    def test_text_available(self):
        resp = FakeResponse(200, text="hello")
        self.assertEqual(_safe_response_body(resp), "hello")

    def test_fallback_to_json(self):
        resp = FakeResponse(200, payload={"ok": True}, text="")
        result = _safe_response_body(resp)
        self.assertIsNotNone(result)

    def test_no_text_no_json_returns_none(self):
        resp = FakeResponse(200, text="")
        self.assertIsNone(_safe_response_body(resp))


class ExtractRetryAfterTests(unittest.TestCase):
    def test_from_payload_parameters(self):
        resp = FakeResponse(200)
        payload = {"parameters": {"retry_after": 30}}
        self.assertEqual(_extract_retry_after(resp, payload), 30)

    def test_string_retry_after_in_payload(self):
        resp = FakeResponse(200)
        payload = {"parameters": {"retry_after": "10"}}
        self.assertEqual(_extract_retry_after(resp, payload), 10)

    def test_from_header(self):
        resp = FakeResponse(200, headers={"Retry-After": "15"})
        self.assertEqual(_extract_retry_after(resp, {}), 15)

    def test_no_retry_after_returns_none(self):
        resp = FakeResponse(200)
        self.assertIsNone(_extract_retry_after(resp, {}))


class ClassifyHttpErrorGenericTests(unittest.TestCase):
    def _build_http_error(self, resp):
        return requests.exceptions.HTTPError("error", response=resp)

    def test_unclassified_4xx_returns_telegram_http_error(self):
        resp = FakeResponse(403, text="Forbidden")
        classified = classify_telegram_http_error(
            self._build_http_error(resp), endpoint="sendMessage"
        )
        self.assertEqual(classified["code"], "telegram_http_error")
        self.assertEqual(classified["status_code"], 403)


class ClassifyRequestErrorTests(unittest.TestCase):
    def test_timeout_returns_network_error(self):
        classified = classify_telegram_request_error(
            requests.exceptions.Timeout("timed out"), endpoint="getUpdates"
        )
        self.assertEqual(classified["code"], "network_error")
        self.assertEqual(classified["reason"], "timeout")

    def test_generic_exception_returns_network_error(self):
        classified = classify_telegram_request_error(
            requests.exceptions.RequestException("generic"), endpoint="getUpdates"
        )
        self.assertEqual(classified["code"], "network_error")

    def test_http_error_delegates_to_classify_http_error(self):
        resp = FakeResponse(401, text="Unauthorized")
        exc = requests.exceptions.HTTPError("error", response=resp)
        classified = classify_telegram_request_error(exc, endpoint="getUpdates")
        self.assertEqual(classified["code"], "invalid_token")


class GetUpdatesTests(unittest.TestCase):
    def test_success_returns_results(self):
        updates = [{"update_id": 1, "message": {"text": "hi"}}]
        resp = FakeResponse(200, {"ok": True, "result": updates})
        req = FakeRequestsModule(response=resp)
        result = get_updates(last_update_id=None, requests_module=req, bot_token="TOKEN")
        self.assertEqual(result, updates)

    def test_offset_set_from_last_update_id(self):
        resp = FakeResponse(200, {"ok": True, "result": []})
        req = FakeRequestsModule(response=resp)
        get_updates(last_update_id=42, requests_module=req, bot_token="TOKEN")
        self.assertEqual(req.last_call["params"]["offset"], 43)

    def test_not_ok_raises_error(self):
        resp = FakeResponse(200, {"ok": False, "description": "bad"})
        req = FakeRequestsModule(response=resp)
        with self.assertRaises(TelegramApiError) as ctx:
            get_updates(last_update_id=None, requests_module=req, bot_token="TOKEN")
        self.assertEqual(ctx.exception.code, "telegram_api_error")


class SendMessageTests(unittest.TestCase):
    def test_success_no_exception(self):
        resp = FakeResponse(200, {"ok": True, "result": {}})
        req = FakeRequestsModule(response=resp)
        send_message(123, "hello", requests_module=req, bot_token="TOKEN")
        self.assertIn("sendMessage", req.last_call["url"])
        self.assertEqual(req.last_call["json"]["chat_id"], 123)

    def test_text_truncated_to_4000(self):
        resp = FakeResponse(200, {"ok": True, "result": {}})
        req = FakeRequestsModule(response=resp)
        send_message(123, "x" * 5000, requests_module=req, bot_token="TOKEN")
        self.assertEqual(len(req.last_call["json"]["text"]), 4000)

    def test_not_ok_response_raises_error(self):
        resp = FakeResponse(200, {"ok": False, "description": "bot blocked"})
        req = FakeRequestsModule(response=resp)
        with self.assertRaises(TelegramApiError) as ctx:
            send_message(123, "hi", requests_module=req, bot_token="TOKEN")
        self.assertEqual(ctx.exception.code, "telegram_api_error")


if __name__ == "__main__":
    unittest.main()
