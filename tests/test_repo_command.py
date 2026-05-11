import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.observability import telegram_trace as telegram_trace_module
from app.services import bot_service, repo_analyzer_service

TRACE_ID = "12345678123456781234567812345678"


class RepoCommandTests(unittest.TestCase):
    def test_repo_without_question_returns_usage(self):
        with patch.object(repo_analyzer_service.settings, "repo_analyzer_enabled", True):
            result = repo_analyzer_service.handle_repo_command(
                "/repo",
                user_id=123,
                trace_id=TRACE_ID,
            )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_code"], "invalid_repo_usage")
        self.assertEqual(result["reply_text"], repo_analyzer_service.REPO_USAGE_TEXT)

    def test_repo_with_question_uses_fixed_settings_and_session(self):
        captured: dict[str, object] = {}

        class FakeSession:
            def __init__(self, repo_path: str, model: str, temperature: float) -> None:
                captured["repo_path"] = repo_path
                captured["model"] = model
                captured["temperature"] = temperature

            def ask(self, question: str) -> dict:
                captured["question"] = question
                return {
                    "status": "ok",
                    "repo_path": captured["repo_path"],
                    "model": captured["model"],
                    "temperature": captured["temperature"],
                    "question": question,
                    "evidence_files": ["app/llm_client.py"],
                    "answer": "Se calcula en app/llm_client.py.",
                    "error": None,
                }

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(repo_analyzer_service.settings, "repo_analyzer_enabled", True):
                with patch.object(repo_analyzer_service.settings, "repo_analyzer_path", tmpdir):
                    with patch.object(repo_analyzer_service.settings, "repo_analyzer_model", "granite4.1:8b"):
                        with patch.object(repo_analyzer_service.settings, "repo_analyzer_temperature", 0.2):
                            result = repo_analyzer_service.handle_repo_command(
                                "/repo Dónde se calculan los tokens?",
                                user_id=123,
                                trace_id=TRACE_ID,
                                session_factory=FakeSession,
                            )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(captured["repo_path"], tmpdir)
        self.assertEqual(captured["model"], "granite4.1:8b")
        self.assertEqual(captured["temperature"], 0.2)
        self.assertEqual(captured["question"], "Dónde se calculan los tokens?")
        self.assertEqual(result["reply_text"], "Se calcula en app/llm_client.py.")

    def test_repo_disabled_returns_controlled_error(self):
        with patch.object(repo_analyzer_service.settings, "repo_analyzer_enabled", False):
            result = repo_analyzer_service.run_repo_analysis_question(
                "Qué hay en el repo?",
                user_id=123,
                trace_id=TRACE_ID,
            )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_code"], "REPO_ANALYZER_DISABLED")
        self.assertEqual(result["reply_text"], "repo_analyzer no está habilitado.")

    def test_repo_invalid_path_returns_invalid_repo_path(self):
        with patch.object(repo_analyzer_service.settings, "repo_analyzer_enabled", True):
            with patch.object(repo_analyzer_service.settings, "repo_analyzer_path", "/tmp/ruta-que-no-existe"):
                result = repo_analyzer_service.run_repo_analysis_question(
                    "Qué hay en el repo?",
                    user_id=123,
                    trace_id=TRACE_ID,
                )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_code"], "INVALID_REPO_PATH")

    def test_repo_ollama_error_is_returned_as_controlled_error(self):
        class FakeSession:
            def __init__(self, repo_path: str, model: str, temperature: float) -> None:
                self.repo_path = repo_path
                self.model = model
                self.temperature = temperature

            def ask(self, question: str) -> dict:
                return {
                    "status": "error",
                    "repo_path": self.repo_path,
                    "model": self.model,
                    "temperature": self.temperature,
                    "question": question,
                    "evidence_files": ["README.md"],
                    "answer": None,
                    "error": {
                        "error_code": "OLLAMA_UNAVAILABLE",
                        "message": "Ollama is unavailable.",
                        "warnings": [],
                    },
                }

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(repo_analyzer_service.settings, "repo_analyzer_enabled", True):
                with patch.object(repo_analyzer_service.settings, "repo_analyzer_path", tmpdir):
                    result = repo_analyzer_service.run_repo_analysis_question(
                        "Qué hay en el repo?",
                        user_id=123,
                        trace_id=TRACE_ID,
                        session_factory=FakeSession,
                    )

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_code"], "OLLAMA_UNAVAILABLE")
        self.assertIn("Ollama is unavailable.", result["reply_text"])

    def test_repo_long_response_is_truncated(self):
        class FakeSession:
            def __init__(self, repo_path: str, model: str, temperature: float) -> None:
                self.repo_path = repo_path
                self.model = model
                self.temperature = temperature

            def ask(self, question: str) -> dict:
                return {
                    "status": "ok",
                    "repo_path": self.repo_path,
                    "model": self.model,
                    "temperature": self.temperature,
                    "question": question,
                    "evidence_files": ["README.md"],
                    "answer": "x" * 5000,
                    "error": None,
                }

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(repo_analyzer_service.settings, "repo_analyzer_enabled", True):
                with patch.object(repo_analyzer_service.settings, "repo_analyzer_path", tmpdir):
                    result = repo_analyzer_service.run_repo_analysis_question(
                        "Resumen largo",
                        user_id=123,
                        trace_id=TRACE_ID,
                        session_factory=FakeSession,
                    )

        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["truncated"])
        self.assertLessEqual(len(result["reply_text"]), repo_analyzer_service.TELEGRAM_SAFE_MESSAGE_CHARS)
        self.assertIn("respuesta truncada", result["reply_text"])

    def test_non_repo_message_keeps_normal_chat_flow(self):
        sent_messages: list[tuple[int, str]] = []
        ask_calls: list[str] = []

        def fake_send(chat_id: int, text: str) -> None:
            sent_messages.append((chat_id, text))

        def fake_ask(message: str, **kwargs) -> dict:
            ask_calls.append(message)
            return {
                "answer": "respuesta normal",
                "provider": "ollama",
                "model": "granite4.1:8b",
                "temperature": 0.2,
                "use_rag": True,
                "status": "ok",
                "latency_ms": 5,
            }

        with patch("app.services.bot_service.write_telegram_conversation_record"):
            bot_service.handle_message(
                {
                    "chat": {"id": 456},
                    "from": {"id": 123},
                    "text": "hola",
                },
                send_message_fn=fake_send,
                ask_chat_fn=fake_ask,
                repo_handler=lambda *args, **kwargs: self.fail("repo_handler should not be called"),
                trace_id_factory=lambda: TRACE_ID,
            )

        self.assertEqual(ask_calls, ["hola"])
        self.assertEqual(sent_messages, [(456, "respuesta normal")])

    def test_repo_trace_includes_repo_metadata(self):
        sent_messages: list[tuple[int, str]] = []

        def fake_send(chat_id: int, text: str) -> None:
            sent_messages.append((chat_id, text))

        repo_result = {
            "status": "ok",
            "trace_id": TRACE_ID,
            "timestamp": "2026-05-10T10:00:00+00:00",
            "source": "telegram",
            "command": "repo",
            "repo_tool": "ask_repo_llm",
            "user_id": 123,
            "repo_path": "/home/jose-gonzalez-oliva/LOCALES",
            "provider": "ollama",
            "model": "granite4.1:8b",
            "temperature": 0.2,
            "question": "Dónde se calculan los tokens?",
            "evidence_files": ["app/llm_client.py"],
            "answer": "Se calcula en app/llm_client.py.",
            "reply_text": "Se calcula en app/llm_client.py.",
            "error": None,
            "error_code": None,
            "error_message": None,
            "warnings": [],
            "latency_ms": 17,
            "truncated": False,
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(telegram_trace_module, "TELEGRAM_RUNS_DIR", Path(tmpdir) / "telegram_runs"):
                with patch.object(telegram_trace_module, "TELEGRAM_EVAL_RUNS_DIR", Path(tmpdir) / "eval_runs"):
                    with patch.object(telegram_trace_module, "TELEGRAM_CONVERSATION_RUNS_DIR", Path(tmpdir) / "conversation_runs"):
                        with patch.object(bot_service.settings, "telegram_trace_include_text", False):
                            bot_service.handle_message(
                                {
                                    "chat": {"id": 456},
                                    "from": {"id": 123},
                                    "text": "/repo Dónde se calculan los tokens?",
                                },
                                send_message_fn=fake_send,
                                ask_chat_fn=lambda *args, **kwargs: self.fail("chat backend should not be called"),
                                repo_handler=lambda *args, **kwargs: repo_result,
                                trace_id_factory=lambda: TRACE_ID,
                            )

            trace_files = list((Path(tmpdir) / "telegram_runs").glob("telegram_chat_*.jsonl"))
            payload = json.loads(trace_files[0].read_text(encoding="utf-8").strip())

        self.assertEqual(sent_messages, [(456, "Se calcula en app/llm_client.py.")])
        self.assertEqual(payload["command"], "repo")
        self.assertEqual(payload["repo_tool"], "ask_repo_llm")
        self.assertEqual(payload["model"], "granite4.1:8b")
        self.assertEqual(payload["temperature"], 0.2)
        self.assertEqual(payload["repo_path"], "/home/jose-gonzalez-oliva/LOCALES")
        self.assertEqual(payload["question"], "Dónde se calculan los tokens?")
        self.assertEqual(payload["evidence_files"], ["app/llm_client.py"])
        self.assertEqual(payload["source_filenames"], ["app/llm_client.py"])
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["latency_ms"], 17)

    def test_repo_read_file_range_uses_configured_repo_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "app" / "config.py"
            config_path.parent.mkdir(parents=True, exist_ok=True)
            config_path.write_text("uno\ndos\ntres\n", encoding="utf-8")

            with patch.object(repo_analyzer_service.settings, "repo_analyzer_enabled", True):
                with patch.object(repo_analyzer_service.settings, "repo_analyzer_path", tmpdir):
                    with patch.object(repo_analyzer_service.settings, "repo_analyzer_model", "granite4.1:8b"):
                        with patch.object(repo_analyzer_service.settings, "repo_analyzer_temperature", 0.2):
                            result = repo_analyzer_service.run_repo_analysis_question(
                                "línea 2 de config.py",
                                user_id=123,
                                trace_id=TRACE_ID,
                            )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["repo_tool"], "read_file_range")
        self.assertEqual(result["repo_path"], tmpdir)
        self.assertEqual(result["resolved_path"], "app/config.py")
        self.assertIn("2: dos", result["reply_text"])


if __name__ == "__main__":
    unittest.main()
