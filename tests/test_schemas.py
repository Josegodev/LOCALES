import os
import unittest

from pydantic import ValidationError

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

from app.schemas import (
    ChatRequest,
    ChatResponse,
    CreateDocumentRequest,
    ErrorResponse,
)

REQUEST_ID = "12345678123456781234567812345678"


class ChatRequestValidationTests(unittest.TestCase):
    def test_valid_minimal_request(self):
        req = ChatRequest(message="hola")
        self.assertEqual(req.message, "hola")
        self.assertIsNone(req.provider)
        self.assertEqual(req.temperature, 0.2)

    def test_trace_id_valid_uuid_hex(self):
        req = ChatRequest(message="hi", trace_id=REQUEST_ID)
        self.assertEqual(req.trace_id, REQUEST_ID)

    def test_trace_id_valid_uuid_with_dashes(self):
        req = ChatRequest(message="hi", trace_id="12345678-1234-5678-1234-567812345678")
        self.assertEqual(req.trace_id, "12345678-1234-5678-1234-567812345678")

    def test_trace_id_invalid_raises_error(self):
        with self.assertRaises(ValidationError):
            ChatRequest(message="hi", trace_id="not-a-valid-uuid-at-all-xxxxx")

    def test_trace_id_none_is_allowed(self):
        req = ChatRequest(message="hi", trace_id=None)
        self.assertIsNone(req.trace_id)

    def test_temperature_nan_rejected(self):
        with self.assertRaises(ValidationError):
            ChatRequest(message="hi", temperature=float("nan"))

    def test_temperature_inf_rejected(self):
        with self.assertRaises(ValidationError):
            ChatRequest(message="hi", temperature=float("inf"))

    def test_message_too_long_rejected(self):
        with self.assertRaises(ValidationError):
            ChatRequest(message="x" * 4001)

    def test_empty_message_rejected(self):
        with self.assertRaises(ValidationError):
            ChatRequest(message="")


class CreateDocumentRequestValidationTests(unittest.TestCase):
    def _valid_kwargs(self):
        return {
            "request_id": REQUEST_ID,
            "filename": "test.md",
            "content": "some content",
            "user_id": 123,
            "chat_id": 456,
        }

    def test_valid_request(self):
        req = CreateDocumentRequest(**self._valid_kwargs())
        self.assertEqual(req.filename, "test.md")

    def test_invalid_request_id_rejected(self):
        kwargs = self._valid_kwargs()
        kwargs["request_id"] = "not-valid"
        with self.assertRaises(ValidationError):
            CreateDocumentRequest(**kwargs)

    def test_absolute_path_rejected(self):
        kwargs = self._valid_kwargs()
        kwargs["filename"] = "/etc/test.md"
        with self.assertRaises(ValidationError):
            CreateDocumentRequest(**kwargs)

    def test_parent_traversal_rejected(self):
        kwargs = self._valid_kwargs()
        kwargs["filename"] = "../test.md"
        with self.assertRaises(ValidationError):
            CreateDocumentRequest(**kwargs)

    def test_path_separator_rejected(self):
        kwargs = self._valid_kwargs()
        kwargs["filename"] = "sub/test.md"
        with self.assertRaises(ValidationError):
            CreateDocumentRequest(**kwargs)

    def test_non_md_extension_rejected(self):
        kwargs = self._valid_kwargs()
        kwargs["filename"] = "test.txt"
        with self.assertRaises(ValidationError):
            CreateDocumentRequest(**kwargs)

    def test_empty_content_rejected(self):
        kwargs = self._valid_kwargs()
        kwargs["content"] = "   "
        with self.assertRaises(ValidationError):
            CreateDocumentRequest(**kwargs)

    def test_extra_fields_rejected(self):
        kwargs = self._valid_kwargs()
        kwargs["extra_field"] = "not allowed"
        with self.assertRaises(ValidationError):
            CreateDocumentRequest(**kwargs)

    def test_overwrite_true_rejected(self):
        kwargs = self._valid_kwargs()
        kwargs["overwrite"] = True
        with self.assertRaises(ValidationError):
            CreateDocumentRequest(**kwargs)

    def test_empty_filename_after_strip_rejected(self):
        kwargs = self._valid_kwargs()
        kwargs["filename"] = "   "
        with self.assertRaises(ValidationError):
            CreateDocumentRequest(**kwargs)


class ErrorResponseTests(unittest.TestCase):
    def test_construction(self):
        err = ErrorResponse(status="error", code="test_code", message="test message")
        self.assertEqual(err.code, "test_code")


if __name__ == "__main__":
    unittest.main()
