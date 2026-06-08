import os
import unittest

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

from app.adapters.backend_client import (
    BackendClientError,
    _response_error_reason,
    ask_chat,
    create_document,
)
from app.schemas import CreateDocumentRequest

REQUEST_ID = "12345678123456781234567812345678"


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


class ResponseErrorReasonTests(unittest.TestCase):
    def test_detail_dict_returns_code(self):
        resp = FakeResponse(400, {"detail": {"code": "file_exists", "message": "ya existe"}})
        self.assertEqual(_response_error_reason(resp), "file_exists")

    def test_detail_dict_falls_back_to_message(self):
        resp = FakeResponse(400, {"detail": {"message": "custom error"}})
        self.assertEqual(_response_error_reason(resp), "custom error")

    def test_detail_dict_defaults_to_backend_error(self):
        resp = FakeResponse(400, {"detail": {}})
        self.assertEqual(_response_error_reason(resp), "backend_error")

    def test_detail_string_returns_string(self):
        resp = FakeResponse(400, {"detail": "some string error"})
        self.assertEqual(_response_error_reason(resp), "some string error")

    def test_no_json_returns_text(self):
        resp = FakeResponse(400, text="raw error text")
        self.assertEqual(_response_error_reason(resp), "raw error text")

    def test_empty_text_returns_backend_error(self):
        resp = FakeResponse(400, text="")
        self.assertEqual(_response_error_reason(resp), "backend_error")


class CreateDocumentTests(unittest.TestCase):
    def _request(self):
        return CreateDocumentRequest(
            request_id=REQUEST_ID,
            filename="test.md",
            content="some content",
            overwrite=False,
            user_id=123,
            chat_id=456,
        )

    def test_success_returns_json(self):
        expected = {"filename": "test.md", "chars": 12}
        resp = FakeResponse(200, expected)
        req = FakeRequestsModule(response=resp)
        result = create_document(self._request(), requests_module=req)
        self.assertEqual(result, expected)
        self.assertIn("/documents", req.last_call["url"])

    def test_400_error_raises_backend_client_error(self):
        resp = FakeResponse(400, {"detail": {"code": "file_exists"}})
        req = FakeRequestsModule(response=resp)
        with self.assertRaises(BackendClientError) as ctx:
            create_document(self._request(), requests_module=req)
        self.assertEqual(ctx.exception.code, "file_exists")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_500_error_raises_backend_client_error(self):
        resp = FakeResponse(500, {"detail": {"code": "internal_error"}})
        req = FakeRequestsModule(response=resp)
        with self.assertRaises(BackendClientError) as ctx:
            create_document(self._request(), requests_module=req)
        self.assertEqual(ctx.exception.status_code, 500)

    def test_invalid_json_on_success_raises_invalid_response(self):
        resp = FakeResponse(200)
        req = FakeRequestsModule(response=resp)
        with self.assertRaises(BackendClientError) as ctx:
            create_document(self._request(), requests_module=req)
        self.assertEqual(ctx.exception.code, "backend_invalid_response")
        self.assertEqual(ctx.exception.status_code, 502)

    def test_custom_base_url(self):
        resp = FakeResponse(200, {"ok": True})
        req = FakeRequestsModule(response=resp)
        create_document(self._request(), requests_module=req, base_url="http://custom:9000")
        self.assertTrue(req.last_call["url"].startswith("http://custom:9000"))


class AskChatTests(unittest.TestCase):
    def test_success_returns_json(self):
        expected = {"answer": "respuesta", "status": "ok"}
        resp = FakeResponse(200, expected)
        req = FakeRequestsModule(response=resp)
        result = ask_chat("hola", requests_module=req)
        self.assertEqual(result, expected)

    def test_optional_fields_included_in_payload(self):
        resp = FakeResponse(200, {"answer": "ok"})
        req = FakeRequestsModule(response=resp)
        ask_chat(
            "hola",
            trace_id=REQUEST_ID,
            user_id=123,
            chat_id=456,
            model="gpt-5.5",
            max_tokens=100,
            temperature=0.5,
            top_k=5,
            requests_module=req,
        )
        payload = req.last_call["json"]
        self.assertEqual(payload["message"], "hola")
        self.assertEqual(payload["trace_id"], REQUEST_ID)
        self.assertEqual(payload["user_id"], 123)
        self.assertEqual(payload["model"], "gpt-5.5")
        self.assertEqual(payload["top_k"], 5)

    def test_none_optional_fields_excluded(self):
        resp = FakeResponse(200, {"answer": "ok"})
        req = FakeRequestsModule(response=resp)
        ask_chat("hola", requests_module=req)
        payload = req.last_call["json"]
        self.assertEqual(list(payload.keys()), ["message"])

    def test_400_raises_backend_client_error(self):
        resp = FakeResponse(400, {"detail": {"code": "bad_request"}})
        req = FakeRequestsModule(response=resp)
        with self.assertRaises(BackendClientError) as ctx:
            ask_chat("hola", requests_module=req)
        self.assertEqual(ctx.exception.code, "bad_request")

    def test_invalid_json_on_success_raises_error(self):
        resp = FakeResponse(200)
        req = FakeRequestsModule(response=resp)
        with self.assertRaises(BackendClientError) as ctx:
            ask_chat("hola", requests_module=req)
        self.assertEqual(ctx.exception.code, "backend_invalid_response")

    def test_custom_base_url_and_timeout(self):
        resp = FakeResponse(200, {"answer": "ok"})
        req = FakeRequestsModule(response=resp)
        ask_chat("hola", requests_module=req, base_url="http://custom:8080", timeout_seconds=5)
        self.assertTrue(req.last_call["url"].startswith("http://custom:8080"))
        self.assertEqual(req.last_call["timeout"], 5)


if __name__ == "__main__":
    unittest.main()
