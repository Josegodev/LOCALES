import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.observability import telegram_trace as telegram_trace_module
from app.services import bot_service


TRACE_ID = "12345678123456781234567812345678"


class TelegramTracePersistenceTests(unittest.TestCase):
    def _run_message_and_read_trace(
        self,
        *,
        text: str,
        ask_chat_fn,
        doc_handler=None,
        doc_ai_handler=None,
    ) -> dict:
        sent_messages: list[tuple[int, str]] = []

        def fake_send(chat_id: int, message_text: str) -> None:
            sent_messages.append((chat_id, message_text))

        kwargs = {
            "send_message_fn": fake_send,
            "ask_chat_fn": ask_chat_fn,
            "trace_id_factory": lambda: TRACE_ID,
        }
        if doc_handler is not None:
            kwargs["doc_handler"] = doc_handler
        if doc_ai_handler is not None:
            kwargs["doc_ai_handler"] = doc_ai_handler

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(telegram_trace_module, "TELEGRAM_RUNS_DIR", Path(tmpdir) / "telegram_runs"):
                with patch.object(bot_service.settings, "telegram_trace_include_text", False):
                    bot_service.handle_message(
                        {
                            "chat": {"id": 456},
                            "from": {"id": 123},
                            "text": text,
                        },
                        **kwargs,
                    )

            files = list((Path(tmpdir) / "telegram_runs").glob("telegram_chat_*.jsonl"))
            payload = json.loads(files[0].read_text(encoding="utf-8").strip())

        self.assertEqual(len(files), 1)
        self.assertEqual(len(sent_messages), 1)
        return payload

    def test_handle_message_persists_jsonl_trace_without_text_by_default(self):
        sent_messages: list[tuple[int, str]] = []

        def fake_send(chat_id: int, text: str) -> None:
            sent_messages.append((chat_id, text))

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(telegram_trace_module, "TELEGRAM_RUNS_DIR", Path(tmpdir) / "telegram_runs"):
                with patch.object(bot_service.settings, "telegram_trace_include_text", False):
                    bot_service.handle_message(
                        {
                            "chat": {"id": 456},
                            "from": {"id": 123},
                            "text": "hola",
                        },
                        send_message_fn=fake_send,
                        ask_chat_fn=lambda *args, **kwargs: {
                            "answer": "respuesta",
                            "provider": "ollama",
                            "model": "granite4.1:8b",
                            "temperature": 0.2,
                            "status": "ok",
                            "latency_ms": 12,
                        },
                        trace_id_factory=lambda: TRACE_ID,
                    )

            output_path = Path(tmpdir) / "telegram_runs"
            files = list(output_path.glob("telegram_chat_*.jsonl"))
            payload = json.loads(files[0].read_text(encoding="utf-8").strip())

        self.assertEqual(len(sent_messages), 1)
        self.assertEqual(len(files), 1)
        self.assertEqual(payload["trace_id"], TRACE_ID)
        self.assertEqual(payload["request_id"], TRACE_ID)
        self.assertEqual(payload["chat_id"], 456)
        self.assertEqual(payload["user_id"], 123)
        self.assertEqual(payload["command"], "chat")
        self.assertEqual(payload["text_chars"], 4)
        self.assertEqual(payload["response_chars"], len("respuesta"))
        self.assertEqual(payload["provider"], "ollama")
        self.assertEqual(payload["model"], "granite4.1:8b")
        self.assertEqual(payload["temperature"], 0.2)
        self.assertEqual(payload["status"], "ok")
        self.assertIsNone(payload["error_code"])
        self.assertIn("created_at", payload)
        self.assertNotIn("text", payload)

    def test_handle_message_persists_chat_token_metrics(self):
        payload = self._run_message_and_read_trace(
            text="hola",
            ask_chat_fn=lambda *args, **kwargs: {
                "answer": "respuesta",
                "provider": "ollama",
                "model": "granite4.1:8b",
                "temperature": 0.2,
                "status": "ok",
                "latency_ms": 12,
                "prompt_eval_count": 1404,
                "eval_count": 77,
                "prompt_eval_duration": 263654367,
                "eval_duration": 1082391194,
                "total_duration": 1406679321,
                "load_duration": 34551123,
                "retrieval_status": "EVIDENCE_FOUND",
                "chunk_ids": [346, 206, 262],
            },
        )

        self.assertEqual(payload["provider"], "ollama")
        self.assertEqual(payload["temperature"], 0.2)
        self.assertEqual(payload["tokens_input"], 1404)
        self.assertEqual(payload["tokens_output"], 77)
        self.assertEqual(payload["tokens_total"], 1481)
        self.assertEqual(payload["prompt_eval_count"], 1404)
        self.assertEqual(payload["eval_count"], 77)
        self.assertEqual(payload["prompt_eval_duration_ns"], 263654367)
        self.assertEqual(payload["eval_duration_ns"], 1082391194)
        self.assertEqual(payload["total_duration_ns"], 1406679321)
        self.assertEqual(payload["load_duration_ns"], 34551123)
        self.assertAlmostEqual(payload["prompt_tokens_per_second"], 5325.153593985417)
        self.assertAlmostEqual(payload["output_tokens_per_second"], 71.1387901406005)
        self.assertEqual(payload["retrieval_status"], "EVIDENCE_FOUND")
        self.assertEqual(payload["chunk_ids"], [346, 206, 262])

    def test_handle_message_persists_non_llm_command_without_token_metrics(self):
        payload = self._run_message_and_read_trace(
            text="/doc ejemplo.md\ncontenido",
            ask_chat_fn=lambda *args, **kwargs: self.fail("chat backend should not be called"),
            doc_handler=lambda *args, **kwargs: "Documento creado: ejemplo.md (9 caracteres)",
        )

        self.assertEqual(payload["command"], "doc")
        self.assertIsNone(payload["model"])
        self.assertNotIn("tokens_input", payload)
        self.assertNotIn("tokens_output", payload)
        self.assertNotIn("tokens_total", payload)

    def test_handle_message_is_compatible_when_backend_omits_token_metrics(self):
        payload = self._run_message_and_read_trace(
            text="hola",
            ask_chat_fn=lambda *args, **kwargs: {
                "answer": "respuesta",
                "provider": "ollama",
                "model": "granite4.1:8b",
                "temperature": 0.2,
                "status": "ok",
                "latency_ms": 12,
            },
        )

        self.assertEqual(payload["provider"], "ollama")
        self.assertEqual(payload["temperature"], 0.2)
        self.assertIsNone(payload["tokens_input"])
        self.assertIsNone(payload["tokens_output"])
        self.assertIsNone(payload["tokens_total"])
        self.assertIsNone(payload["prompt_eval_duration_ns"])
        self.assertIsNone(payload["eval_duration_ns"])
        self.assertIsNone(payload["prompt_tokens_per_second"])
        self.assertIsNone(payload["output_tokens_per_second"])
        self.assertEqual(payload["chunk_ids"], [])

    def test_handle_message_can_include_text_when_enabled(self):
        sent_messages: list[tuple[int, str]] = []

        def fake_send(chat_id: int, text: str) -> None:
            sent_messages.append((chat_id, text))

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(telegram_trace_module, "TELEGRAM_RUNS_DIR", Path(tmpdir) / "telegram_runs"):
                with patch.object(bot_service.settings, "telegram_trace_include_text", True):
                    bot_service.handle_message(
                        {
                            "chat": {"id": 456},
                            "from": {"id": 123},
                            "text": "hola con texto",
                        },
                        send_message_fn=fake_send,
                        ask_chat_fn=lambda *args, **kwargs: {
                            "answer": "ok",
                            "provider": "ollama",
                            "model": "granite4.1:8b",
                            "temperature": 0.2,
                            "status": "ok",
                            "latency_ms": 7,
                        },
                        trace_id_factory=lambda: TRACE_ID,
                    )

            files = list((Path(tmpdir) / "telegram_runs").glob("telegram_chat_*.jsonl"))
            payload = json.loads(files[0].read_text(encoding="utf-8").strip())

        self.assertEqual(len(files), 1)
        self.assertEqual(payload["text"], "hola con texto")

    def test_trace_persistence_failure_does_not_break_message_processing(self):
        sent_messages: list[tuple[int, str]] = []

        def fake_send(chat_id: int, text: str) -> None:
            sent_messages.append((chat_id, text))

        with patch("app.services.bot_service.append_telegram_trace", side_effect=OSError("disk full")):
            bot_service.handle_message(
                {
                    "chat": {"id": 456},
                    "from": {"id": 123},
                    "text": "hola",
                },
                send_message_fn=fake_send,
                ask_chat_fn=lambda *args, **kwargs: {
                    "answer": "ok",
                    "provider": "ollama",
                    "model": "granite4.1:8b",
                    "temperature": 0.2,
                    "status": "ok",
                    "latency_ms": 4,
                },
                trace_id_factory=lambda: TRACE_ID,
            )

        self.assertEqual(sent_messages, [(456, "ok")])


if __name__ == "__main__":
    unittest.main()
