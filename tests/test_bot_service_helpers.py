import os
import unittest

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

from app.services.bot_service import (
    DocCommandParseError,
    LLMOutputValidationError,
    _chat_trace_metadata,
    _message_command,
    _safe_token_rate,
    _validate_llm_markdown_output,
    build_llm_prompt,
    parse_doc_ai_command,
    parse_doc_command,
)


class BuildLlmPromptTests(unittest.TestCase):
    def test_strips_whitespace(self):
        self.assertEqual(build_llm_prompt("  hello  "), "hello")


class MessageCommandTests(unittest.TestCase):
    def test_doc_ai(self):
        self.assertEqual(_message_command("/doc_ai algo"), "doc_ai")

    def test_doc(self):
        self.assertEqual(_message_command("/doc algo"), "doc")

    def test_chat(self):
        self.assertEqual(_message_command("hola"), "chat")

    def test_doc_ai_takes_precedence_over_doc(self):
        self.assertEqual(_message_command("/doc_ai"), "doc_ai")


class SafeTokenRateTests(unittest.TestCase):
    def test_valid_values(self):
        rate = _safe_token_rate(100, 1_000_000_000)
        self.assertAlmostEqual(rate, 100.0)

    def test_none_count(self):
        self.assertIsNone(_safe_token_rate(None, 1_000_000_000))

    def test_none_duration(self):
        self.assertIsNone(_safe_token_rate(100, None))

    def test_zero_count(self):
        self.assertIsNone(_safe_token_rate(0, 1_000_000_000))

    def test_zero_duration(self):
        self.assertIsNone(_safe_token_rate(100, 0))

    def test_negative_count(self):
        self.assertIsNone(_safe_token_rate(-1, 1_000_000_000))

    def test_non_int_count(self):
        self.assertIsNone(_safe_token_rate("100", 1_000_000_000))


class ChatTraceMetadataTests(unittest.TestCase):
    def test_none_result_returns_empty_dict(self):
        self.assertEqual(_chat_trace_metadata(None), {})

    def test_non_dict_returns_empty_dict(self):
        self.assertEqual(_chat_trace_metadata("string"), {})

    def test_valid_result_extracts_fields(self):
        result = {
            "provider": "ollama",
            "temperature": 0.3,
            "temperature_ignored": False,
            "prompt_eval_count": 50,
            "eval_count": 25,
            "prompt_eval_duration": 1_000_000_000,
            "eval_duration": 500_000_000,
            "total_duration": 2_000_000_000,
            "load_duration": 10_000_000,
            "retrieval_status": "EVIDENCE_FOUND",
            "chunk_ids": [1, 2, 3],
        }
        meta = _chat_trace_metadata(result)
        self.assertEqual(meta["provider"], "ollama")
        self.assertEqual(meta["tokens_input"], 50)
        self.assertEqual(meta["tokens_output"], 25)
        self.assertEqual(meta["tokens_total"], 75)
        self.assertEqual(meta["chunk_ids"], [1, 2, 3])
        self.assertIsNotNone(meta["prompt_tokens_per_second"])
        self.assertIsNotNone(meta["output_tokens_per_second"])

    def test_non_int_fields_set_to_none(self):
        result = {
            "prompt_eval_count": "bad",
            "eval_count": "bad",
            "prompt_eval_duration": "bad",
            "eval_duration": None,
            "total_duration": None,
            "load_duration": None,
            "chunk_ids": "not a list",
        }
        meta = _chat_trace_metadata(result)
        self.assertIsNone(meta["tokens_input"])
        self.assertIsNone(meta["tokens_output"])
        self.assertIsNone(meta["tokens_total"])
        self.assertEqual(meta["chunk_ids"], [])

    def test_invalid_chunk_ids_reset_to_empty(self):
        result = {"chunk_ids": [1, "bad", 3]}
        meta = _chat_trace_metadata(result)
        self.assertEqual(meta["chunk_ids"], [])


class ValidateLlmMarkdownOutputTests(unittest.TestCase):
    def test_valid_output(self):
        result = _validate_llm_markdown_output("# Hello\nWorld")
        self.assertEqual(result, "# Hello\nWorld")

    def test_strips_whitespace(self):
        result = _validate_llm_markdown_output("  hello  ")
        self.assertEqual(result, "hello")

    def test_normalizes_crlf(self):
        result = _validate_llm_markdown_output("a\r\nb")
        self.assertEqual(result, "a\nb")

    def test_non_string_raises_error(self):
        with self.assertRaises(LLMOutputValidationError) as ctx:
            _validate_llm_markdown_output(123)
        self.assertEqual(ctx.exception.code, "llm_output_not_text")

    def test_null_byte_raises_error(self):
        with self.assertRaises(LLMOutputValidationError) as ctx:
            _validate_llm_markdown_output("hello\x00world")
        self.assertEqual(ctx.exception.code, "llm_output_contains_null_byte")

    def test_empty_after_strip_raises_error(self):
        with self.assertRaises(LLMOutputValidationError) as ctx:
            _validate_llm_markdown_output("   ")
        self.assertEqual(ctx.exception.code, "llm_output_empty")

    def test_too_large_raises_error(self):
        from unittest.mock import patch
        with patch("app.services.bot_service.settings") as mock_settings:
            mock_settings.llm_max_output_chars = 10
            with self.assertRaises(LLMOutputValidationError) as ctx:
                _validate_llm_markdown_output("x" * 20)
            self.assertEqual(ctx.exception.code, "llm_output_too_large")


class ParseDocCommandTests(unittest.TestCase):
    def test_valid_command(self):
        parsed = parse_doc_command("/doc test.md\ncontent here", user_id=1, chat_id=2)
        self.assertEqual(parsed.filename, "test.md")
        self.assertEqual(parsed.content, "content here")
        self.assertEqual(parsed.user_id, 1)
        self.assertEqual(parsed.chat_id, 2)

    def test_no_user_id_raises_error(self):
        with self.assertRaises(DocCommandParseError) as ctx:
            parse_doc_command("/doc test.md\ncontent", user_id=None, chat_id=2)
        self.assertEqual(ctx.exception.code, "user_id_required")

    def test_no_chat_id_raises_error(self):
        with self.assertRaises(DocCommandParseError) as ctx:
            parse_doc_command("/doc test.md\ncontent", user_id=1, chat_id=None)
        self.assertEqual(ctx.exception.code, "chat_id_required")

    def test_no_newline_raises_error(self):
        with self.assertRaises(DocCommandParseError) as ctx:
            parse_doc_command("/doc test.md content", user_id=1, chat_id=2)
        self.assertEqual(ctx.exception.code, "invalid_doc_usage")

    def test_empty_body_raises_error(self):
        with self.assertRaises(DocCommandParseError) as ctx:
            parse_doc_command("/doc", user_id=1, chat_id=2)
        self.assertEqual(ctx.exception.code, "invalid_doc_usage")


class ParseDocAiCommandTests(unittest.TestCase):
    def test_valid_command(self):
        parsed = parse_doc_ai_command("/doc_ai test.md Write a summary", user_id=1, chat_id=2)
        self.assertEqual(parsed.filename, "test.md")
        self.assertEqual(parsed.prompt, "Write a summary")

    def test_no_user_id_raises_error(self):
        with self.assertRaises(DocCommandParseError) as ctx:
            parse_doc_ai_command("/doc_ai test.md prompt", user_id=None, chat_id=2)
        self.assertEqual(ctx.exception.code, "user_id_required")

    def test_no_chat_id_raises_error(self):
        with self.assertRaises(DocCommandParseError) as ctx:
            parse_doc_ai_command("/doc_ai test.md prompt", user_id=1, chat_id=None)
        self.assertEqual(ctx.exception.code, "chat_id_required")

    def test_missing_prompt_raises_error(self):
        with self.assertRaises(DocCommandParseError) as ctx:
            parse_doc_ai_command("/doc_ai test.md", user_id=1, chat_id=2)
        self.assertEqual(ctx.exception.code, "invalid_doc_ai_usage")

    def test_empty_body_raises_error(self):
        with self.assertRaises(DocCommandParseError) as ctx:
            parse_doc_ai_command("/doc_ai", user_id=1, chat_id=2)
        self.assertEqual(ctx.exception.code, "invalid_doc_ai_usage")


if __name__ == "__main__":
    unittest.main()
