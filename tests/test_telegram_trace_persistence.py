import json
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.observability import telegram_trace as telegram_trace_module
from app.services import bot_service

SUMMARIZER_PATH = Path("/home/jose-gonzalez-oliva/LOCALES/evals/runs/summarize_telegram_runs.py")
summarizer_spec = importlib.util.spec_from_file_location("summarize_telegram_runs", SUMMARIZER_PATH)
summarize_telegram_runs = importlib.util.module_from_spec(summarizer_spec)
assert summarizer_spec is not None and summarizer_spec.loader is not None
summarizer_spec.loader.exec_module(summarize_telegram_runs)


TRACE_ID = "12345678123456781234567812345678"


class TelegramTracePersistenceTests(unittest.TestCase):
    def _run_message_and_read_traces(
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
                with patch.object(telegram_trace_module, "TELEGRAM_EVAL_RUNS_DIR", Path(tmpdir) / "eval_runs"):
                    with patch.object(bot_service.settings, "telegram_trace_include_text", False):
                        bot_service.handle_message(
                            {
                                "chat": {"id": 456},
                                "from": {"id": 123},
                                "text": text,
                            },
                            **kwargs,
                        )

            jsonl_files = list((Path(tmpdir) / "telegram_runs").glob("telegram_chat_*.jsonl"))
            eval_files = list((Path(tmpdir) / "eval_runs").glob("chat_eval_*.json"))
            jsonl_payload = json.loads(jsonl_files[0].read_text(encoding="utf-8").strip())
            eval_payload = json.loads(eval_files[0].read_text(encoding="utf-8"))

        self.assertEqual(len(jsonl_files), 1)
        self.assertEqual(len(eval_files), 1)
        self.assertEqual(len(sent_messages), 1)
        return {
            "jsonl_payload": jsonl_payload,
            "jsonl_path": jsonl_files[0],
            "eval_payload": eval_payload,
            "eval_path": eval_files[0],
        }

    def test_handle_message_persists_jsonl_trace_without_text_by_default(self):
        sent_messages: list[tuple[int, str]] = []

        def fake_send(chat_id: int, text: str) -> None:
            sent_messages.append((chat_id, text))

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(telegram_trace_module, "TELEGRAM_RUNS_DIR", Path(tmpdir) / "telegram_runs"):
                with patch.object(telegram_trace_module, "TELEGRAM_EVAL_RUNS_DIR", Path(tmpdir) / "eval_runs"):
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
                                "use_rag": True,
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
        self.assertEqual(payload["source"], "telegram")
        self.assertEqual(payload["input"], "hola")
        self.assertEqual(payload["response"], "respuesta")
        self.assertEqual(payload["answer_length"], len("respuesta"))
        self.assertEqual(payload["command"], "chat")
        self.assertEqual(payload["text_chars"], 4)
        self.assertEqual(payload["response_chars"], len("respuesta"))
        self.assertEqual(payload["provider"], "ollama")
        self.assertEqual(payload["model"], "granite4.1:8b")
        self.assertEqual(payload["temperature"], 0.2)
        self.assertEqual(payload["prompt_version"], "telegram_rag_v1")
        self.assertIsNone(payload["top_k"])
        self.assertEqual(payload["source_filenames"], [])
        self.assertTrue(payload["use_rag"])
        self.assertEqual(payload["status"], "ok")
        self.assertIsNone(payload["error_code"])
        self.assertIsNone(payload["error_message"])
        self.assertIn("created_at", payload)
        self.assertNotIn("text", payload)

    def test_handle_message_persists_chat_token_metrics(self):
        traces = self._run_message_and_read_traces(
            text="hola",
            ask_chat_fn=lambda *args, **kwargs: {
                "answer": "respuesta",
                "provider": "ollama",
                "model": "granite4.1:8b",
                "temperature": 0.2,
                "use_rag": True,
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
                "top_k": 3,
                "source_filenames": ["ARCHITECTURE.md"],
            },
        )
        payload = traces["jsonl_payload"]
        eval_payload = traces["eval_payload"]

        self.assertEqual(payload["provider"], "ollama")
        self.assertEqual(payload["temperature"], 0.2)
        self.assertTrue(payload["use_rag"])
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
        self.assertEqual(payload["prompt_version"], "telegram_rag_v1")
        self.assertEqual(payload["top_k"], 3)
        self.assertEqual(payload["source_filenames"], ["ARCHITECTURE.md"])
        self.assertEqual(payload["answer_length"], len("respuesta"))
        self.assertEqual(
            payload["ollama"],
            {
                "load_duration_ns": 34551123,
                "prompt_eval_duration_ns": 263654367,
                "eval_duration_ns": 1082391194,
                "total_duration_ns": 1406679321,
                "prompt_eval_count": 1404,
                "eval_count": 77,
            },
        )
        for key, value in payload.items():
            self.assertIn(key, eval_payload)
            self.assertEqual(eval_payload[key], value)
        self.assertEqual(eval_payload["source"], "telegram")
        self.assertEqual(eval_payload["trace_id"], TRACE_ID)
        self.assertEqual(eval_payload["model"], "granite4.1:8b")
        self.assertEqual(eval_payload["temperature"], 0.2)
        self.assertIsNone(eval_payload["generation_config"])
        self.assertEqual(eval_payload["input"], "hola")
        self.assertEqual(eval_payload["response"], "respuesta")
        self.assertEqual(eval_payload["status"], "ok")
        self.assertEqual(eval_payload["retrieval_status"], "EVIDENCE_FOUND")
        self.assertEqual(eval_payload["chunk_ids"], [346, 206, 262])
        self.assertEqual(eval_payload["prompt_eval_count"], 1404)
        self.assertEqual(eval_payload["eval_count"], 77)
        self.assertEqual(eval_payload["prompt_eval_duration"], 263654367)
        self.assertEqual(eval_payload["eval_duration"], 1082391194)
        self.assertEqual(eval_payload["total_duration"], 1406679321)
        self.assertEqual(eval_payload["load_duration"], 34551123)
        self.assertEqual(eval_payload["tokens_input"], 1404)
        self.assertEqual(eval_payload["tokens_output"], 77)
        self.assertEqual(eval_payload["tokens_total"], 1481)
        self.assertAlmostEqual(eval_payload["output_tokens_per_second"], 71.1387901406005)
        self.assertEqual(eval_payload["warnings"], [])
        self.assertIsNone(eval_payload["error_code"])
        self.assertIsNone(eval_payload["error_message"])
        self.assertIn("granite4.1_8b", traces["eval_path"].name)

    def test_handle_message_persists_non_llm_command_without_token_metrics(self):
        traces = self._run_message_and_read_traces(
            text="/doc ejemplo.md\ncontenido",
            ask_chat_fn=lambda *args, **kwargs: self.fail("chat backend should not be called"),
            doc_handler=lambda *args, **kwargs: "Documento creado: ejemplo.md (9 caracteres)",
        )
        payload = traces["jsonl_payload"]
        eval_payload = traces["eval_payload"]

        self.assertEqual(payload["command"], "doc")
        self.assertIsNone(payload["model"])
        self.assertNotIn("tokens_input", payload)
        self.assertNotIn("tokens_output", payload)
        self.assertNotIn("tokens_total", payload)
        self.assertEqual(eval_payload["model"], None)
        self.assertNotIn("prompt_eval_count", eval_payload)
        self.assertNotIn("eval_count", eval_payload)
        self.assertEqual(eval_payload["warnings"], [])
        self.assertIsNone(eval_payload["temperature"])
        self.assertIsNone(eval_payload["generation_config"])
        self.assertIn("unknown_model", traces["eval_path"].name)

    def test_handle_message_is_compatible_when_backend_omits_token_metrics(self):
        traces = self._run_message_and_read_traces(
            text="hola",
            ask_chat_fn=lambda *args, **kwargs: {
                "answer": "respuesta",
                "provider": "ollama",
                "model": "granite4.1:8b",
                "temperature": 0.2,
                "use_rag": True,
                "status": "ok",
                "latency_ms": 12,
            },
        )
        payload = traces["jsonl_payload"]
        eval_payload = traces["eval_payload"]

        self.assertEqual(payload["provider"], "ollama")
        self.assertEqual(payload["temperature"], 0.2)
        self.assertTrue(payload["use_rag"])
        self.assertIsNone(payload["tokens_input"])
        self.assertIsNone(payload["tokens_output"])
        self.assertIsNone(payload["tokens_total"])
        self.assertIsNone(payload["prompt_eval_duration_ns"])
        self.assertIsNone(payload["eval_duration_ns"])
        self.assertIsNone(payload["prompt_tokens_per_second"])
        self.assertIsNone(payload["output_tokens_per_second"])
        self.assertEqual(payload["chunk_ids"], [])
        self.assertEqual(payload["prompt_version"], "telegram_rag_v1")
        self.assertIsNone(payload["top_k"])
        self.assertEqual(payload["source_filenames"], [])
        self.assertEqual(payload["answer_length"], len("respuesta"))
        self.assertNotIn("ollama", payload)
        for key, value in payload.items():
            self.assertIn(key, eval_payload)
            self.assertEqual(eval_payload[key], value)
        self.assertEqual(eval_payload["chunk_ids"], [])
        self.assertIsNone(eval_payload["retrieval_status"])
        self.assertEqual(eval_payload["temperature"], 0.2)
        self.assertIsNone(eval_payload["generation_config"])

    def test_handle_message_can_include_text_when_enabled(self):
        sent_messages: list[tuple[int, str]] = []

        def fake_send(chat_id: int, text: str) -> None:
            sent_messages.append((chat_id, text))

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(telegram_trace_module, "TELEGRAM_RUNS_DIR", Path(tmpdir) / "telegram_runs"):
                with patch.object(telegram_trace_module, "TELEGRAM_EVAL_RUNS_DIR", Path(tmpdir) / "eval_runs"):
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
                                "use_rag": True,
                                "status": "ok",
                                "latency_ms": 7,
                            },
                            trace_id_factory=lambda: TRACE_ID,
                        )

            files = list((Path(tmpdir) / "telegram_runs").glob("telegram_chat_*.jsonl"))
            payload = json.loads(files[0].read_text(encoding="utf-8").strip())

        self.assertEqual(len(files), 1)
        self.assertEqual(payload["text"], "hola con texto")
        self.assertEqual(payload["input"], "hola con texto")
        self.assertEqual(payload["response"], "ok")

    def test_trace_persistence_failure_does_not_break_message_processing(self):
        sent_messages: list[tuple[int, str]] = []

        def fake_send(chat_id: int, text: str) -> None:
            sent_messages.append((chat_id, text))

        with patch("app.services.bot_service.append_telegram_trace", side_effect=OSError("disk full")):
            with patch("app.services.bot_service.write_telegram_eval_run"):
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
                        "use_rag": True,
                        "status": "ok",
                        "latency_ms": 4,
                    },
                    trace_id_factory=lambda: TRACE_ID,
                )

        self.assertEqual(sent_messages, [(456, "ok")])

    def test_backend_failure_still_persists_eval_run(self):
        sent_messages: list[tuple[int, str]] = []

        def fake_send(chat_id: int, text: str) -> None:
            sent_messages.append((chat_id, text))

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(telegram_trace_module, "TELEGRAM_RUNS_DIR", Path(tmpdir) / "telegram_runs"):
                with patch.object(telegram_trace_module, "TELEGRAM_EVAL_RUNS_DIR", Path(tmpdir) / "eval_runs"):
                    bot_service.handle_message(
                        {
                            "chat": {"id": 456},
                            "from": {"id": 123},
                            "text": "hola",
                        },
                        send_message_fn=fake_send,
                        ask_chat_fn=lambda *args, **kwargs: (_ for _ in ()).throw(
                            bot_service.backend_client.BackendClientError(
                                code="backend_timeout",
                                message="backend_chat_error",
                                status_code=504,
                            )
                        ),
                        trace_id_factory=lambda: TRACE_ID,
                    )

            eval_files = list((Path(tmpdir) / "eval_runs").glob("chat_eval_*.json"))
            eval_payload = json.loads(eval_files[0].read_text(encoding="utf-8"))

        self.assertEqual(len(eval_files), 1)
        self.assertEqual(sent_messages, [(456, f"No se pudo procesar el mensaje. (request_id={TRACE_ID})")])
        self.assertEqual(eval_payload["status"], "error")
        self.assertEqual(eval_payload["error_code"], "backend_timeout")
        self.assertEqual(eval_payload["error_message"], "backend_chat_error")
        self.assertEqual(eval_payload["response"], f"No se pudo procesar el mensaje. (request_id={TRACE_ID})")

    def test_backend_failure_still_persists_valid_jsonl_trace(self):
        sent_messages: list[tuple[int, str]] = []

        def fake_send(chat_id: int, text: str) -> None:
            sent_messages.append((chat_id, text))

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(telegram_trace_module, "TELEGRAM_RUNS_DIR", Path(tmpdir) / "telegram_runs"):
                with patch.object(telegram_trace_module, "TELEGRAM_EVAL_RUNS_DIR", Path(tmpdir) / "eval_runs"):
                    bot_service.handle_message(
                        {
                            "chat": {"id": 456},
                            "from": {"id": 123},
                            "text": "hola",
                        },
                        send_message_fn=fake_send,
                        ask_chat_fn=lambda *args, **kwargs: (_ for _ in ()).throw(
                            bot_service.backend_client.BackendClientError(
                                code="backend_timeout",
                                message="backend_chat_error",
                                status_code=504,
                            )
                        ),
                        trace_id_factory=lambda: TRACE_ID,
                    )

            jsonl_files = list((Path(tmpdir) / "telegram_runs").glob("telegram_chat_*.jsonl"))
            payload = json.loads(jsonl_files[0].read_text(encoding="utf-8").strip())

        self.assertEqual(len(jsonl_files), 1)
        self.assertEqual(payload["trace_id"], TRACE_ID)
        self.assertEqual(payload["model"], None)
        self.assertEqual(payload["temperature"], None)
        self.assertEqual(payload["retrieval_status"], None)
        self.assertEqual(payload["chunk_ids"], [])
        self.assertEqual(payload["prompt_version"], "telegram_rag_v1")
        self.assertIsNone(payload["top_k"])
        self.assertEqual(payload["answer_length"], len(f"No se pudo procesar el mensaje. (request_id={TRACE_ID})"))
        self.assertEqual(payload["status"], "error")
        self.assertEqual(payload["error_code"], "backend_timeout")
        self.assertEqual(payload["error_message"], "backend_chat_error")
        self.assertEqual(payload["response"], f"No se pudo procesar el mensaje. (request_id={TRACE_ID})")
        self.assertEqual(payload["source_filenames"], [])
        self.assertNotIn("ollama", payload)

    def test_build_eval_record_from_trace_preserves_all_fields(self):
        trace_record = {
            "chunk_ids": [206, 277, 285],
            "created_at": "2026-05-09T10:25:38.552187+00:00",
            "error_code": None,
            "error_message": None,
            "eval_count": 146,
            "eval_duration_ns": 1875091495,
            "generation_config": None,
            "input": "¿que hace el planner?",
            "latency_ms": 4566,
            "load_duration_ns": 2013858549,
            "model": "llama3.1:8b",
            "output_tokens_per_second": 77.86286716638325,
            "prompt_eval_count": 1419,
            "prompt_eval_duration_ns": 423309996,
            "response": "respuesta",
            "retrieval_status": "EVIDENCE_FOUND",
            "source": "telegram",
            "status": "ok",
            "temperature": 1.0,
            "tokens_input": 1419,
            "tokens_output": 146,
            "tokens_total": 1565,
            "total_duration_ns": 4365564453,
            "trace_id": "e19f17a490a64a15845d6481de884b94",
            "warnings": [],
        }

        eval_record = telegram_trace_module.build_eval_record_from_trace(trace_record)

        for key, value in trace_record.items():
            self.assertIn(key, eval_record)
            self.assertEqual(eval_record[key], value)
        self.assertEqual(eval_record["prompt_eval_duration"], 423309996)
        self.assertEqual(eval_record["eval_duration"], 1875091495)
        self.assertEqual(eval_record["load_duration"], 2013858549)
        self.assertEqual(eval_record["total_duration"], 4365564453)

    def test_safe_model_name_replaces_invalid_chars_and_limits_length(self):
        self.assertEqual(telegram_trace_module.safe_model_name(None), "unknown_model")
        self.assertEqual(telegram_trace_module.safe_model_name(" granite4.1:8b "), "granite4.1_8b")
        self.assertEqual(
            telegram_trace_module.safe_model_name("a" * 120),
            "a" * 80,
        )

    def test_handle_message_persists_generation_config_when_backend_returns_it(self):
        traces = self._run_message_and_read_traces(
            text="hola",
            ask_chat_fn=lambda *args, **kwargs: {
                "answer": "respuesta",
                "provider": "ollama",
                "model": "granite4.1:8b",
                "temperature": 0.3,
                "generation_config": {
                    "temperature": 0.3,
                    "num_predict": 256,
                    "top_k": 20,
                },
                "use_rag": True,
                "status": "ok",
                "latency_ms": 12,
            },
        )

        eval_payload = traces["eval_payload"]
        self.assertEqual(eval_payload["temperature"], 0.3)
        self.assertEqual(
            eval_payload["generation_config"],
            {
                "temperature": 0.3,
                "num_predict": 256,
                "top_k": 20,
            },
        )

    def test_write_telegram_eval_run_prints_written_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("builtins.print") as print_mock:
                path = telegram_trace_module.write_telegram_eval_run(
                    trace_id=TRACE_ID,
                    model="granite4.1:8b",
                    input_text="hola",
                    response_text="respuesta",
                    status="ok",
                    latency_ms=9,
                    error_code=None,
                    error_message=None,
                    metadata={
                        "temperature": 0.4,
                        "generation_config": {"temperature": 0.4, "num_predict": 128},
                    },
                    base_dir=Path(tmpdir) / "eval_runs",
                )
                self.assertTrue(path.exists())
                payload = json.loads(path.read_text(encoding="utf-8"))

        print_mock.assert_called_once()
        self.assertIn("[telegram_eval] wrote eval run:", print_mock.call_args.args[0])
        self.assertEqual(payload["temperature"], 0.4)
        self.assertEqual(payload["generation_config"], {"temperature": 0.4, "num_predict": 128})

    def test_summarize_groups_by_model_and_temperature_with_legacy_runs(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir)
            (runs_dir / "chat_eval_1.json").write_text(
                json.dumps(
                    {
                        "source": "telegram",
                        "model": "granite4.1:8b",
                        "temperature": 0.2,
                        "latency_ms": 10,
                        "output_tokens_per_second": 20.0,
                        "tokens_total": 100,
                        "retrieval_status": "EVIDENCE_FOUND",
                        "error_code": None,
                    }
                ),
                encoding="utf-8",
            )
            (runs_dir / "chat_eval_2.json").write_text(
                json.dumps(
                    {
                        "source": "telegram",
                        "model": "granite4.1:8b",
                        "latency_ms": 30,
                        "output_tokens_per_second": 10.0,
                        "tokens_total": 80,
                        "retrieval_status": "NO_EVIDENCE",
                        "error_code": "backend_timeout",
                    }
                ),
                encoding="utf-8",
            )
            (runs_dir / "chat_eval_3.json").write_text(
                json.dumps(
                    {
                        "model": "granite4.1:8b",
                        "results": [],
                    }
                ),
                encoding="utf-8",
            )

            with patch.object(summarize_telegram_runs, "RUNS_DIR", runs_dir):
                runs = summarize_telegram_runs.load_runs()
                grouped = summarize_telegram_runs.group_by_model_and_temperature(runs)
                warm_summary = summarize_telegram_runs.summarize_model(
                    "granite4.1:8b",
                    0.2,
                    grouped[("granite4.1:8b", 0.2)],
                )
                legacy_summary = summarize_telegram_runs.summarize_model(
                    "granite4.1:8b",
                    None,
                    grouped[("granite4.1:8b", None)],
                )

        self.assertEqual(len(runs), 2)
        self.assertIn(("granite4.1:8b", 0.2), grouped)
        self.assertIn(("granite4.1:8b", None), grouped)
        self.assertEqual(warm_summary["runs"], 1)
        self.assertEqual(warm_summary["avg_latency_ms"], 10)
        self.assertEqual(warm_summary["evidence_found_rate"], 1.0)
        self.assertEqual(legacy_summary["temperature"], None)
        self.assertEqual(legacy_summary["errors"], 1)


if __name__ == "__main__":
    unittest.main()
