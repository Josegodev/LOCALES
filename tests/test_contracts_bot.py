import os
import unittest

from pydantic import ValidationError

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

from app.contracts.bot import (
    ParsedDocAiCommand,
    ParsedDocCommand,
    TelegramMessage,
    TraceContext,
    _validate_trace_id,
)

VALID_TRACE_ID = "12345678123456781234567812345678"


class ValidateTraceIdTests(unittest.TestCase):
    def test_valid_hex(self):
        self.assertEqual(_validate_trace_id(VALID_TRACE_ID), VALID_TRACE_ID)

    def test_valid_dashed_uuid(self):
        result = _validate_trace_id("12345678-1234-5678-1234-567812345678")
        self.assertEqual(result, "12345678-1234-5678-1234-567812345678")

    def test_invalid_raises_value_error(self):
        with self.assertRaises(ValueError):
            _validate_trace_id("not-a-valid-uuid")

    def test_non_canonical_raises_value_error(self):
        with self.assertRaises(ValueError):
            _validate_trace_id("1234567812345678123456781234567X")


class TraceContextTests(unittest.TestCase):
    def test_valid(self):
        ctx = TraceContext(trace_id=VALID_TRACE_ID, user_id=1, chat_id=2)
        self.assertEqual(ctx.trace_id, VALID_TRACE_ID)

    def test_extra_fields_rejected(self):
        with self.assertRaises(ValidationError):
            TraceContext(trace_id=VALID_TRACE_ID, extra="bad")


class TelegramMessageTests(unittest.TestCase):
    def test_defaults(self):
        msg = TelegramMessage(chat_id=123)
        self.assertIsNone(msg.user_id)
        self.assertEqual(msg.text, "")

    def test_extra_rejected(self):
        with self.assertRaises(ValidationError):
            TelegramMessage(chat_id=123, extra="bad")


class ParsedDocCommandTests(unittest.TestCase):
    def test_valid(self):
        cmd = ParsedDocCommand(filename="f.md", content="c", user_id=1, chat_id=2)
        self.assertEqual(cmd.command, "doc.create")

    def test_extra_rejected(self):
        with self.assertRaises(ValidationError):
            ParsedDocCommand(filename="f.md", content="c", user_id=1, chat_id=2, extra="bad")


class ParsedDocAiCommandTests(unittest.TestCase):
    def test_valid(self):
        cmd = ParsedDocAiCommand(filename="f.md", prompt="p", user_id=1, chat_id=2)
        self.assertEqual(cmd.command, "doc_ai.create")

    def test_extra_rejected(self):
        with self.assertRaises(ValidationError):
            ParsedDocAiCommand(filename="f.md", prompt="p", user_id=1, chat_id=2, extra="bad")


if __name__ == "__main__":
    unittest.main()
