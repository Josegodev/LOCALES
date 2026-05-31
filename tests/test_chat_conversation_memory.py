import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class ChatConversationMemoryTests(unittest.TestCase):
    CONVERSATION_ID = "12345678-1234-5678-1234-567812345670"

    def test_chat_reuses_recent_messages_from_same_conversation(self):
        captured_messages: list[str] = []

        def ask_chat_side_effect(*args, **kwargs):
            captured_messages.append(kwargs["message"])
            if len(captured_messages) == 1:
                answer = "Primera respuesta."
            else:
                answer = "Segunda respuesta."
            return {
                "status": "ok",
                "provider": "ollama",
                "model": "granite4.1:8b",
                "temperature": 0.2,
                "use_rag": False,
                "answer": answer,
            }

        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "CHAT_RUNS"
            client = TestClient(app)
            with patch("app.auth.settings.chat_auth_mode", "local_open"):
                with patch("app.main.settings.chat_runs_path", str(runs_dir)):
                    with patch("app.observability.chat_runs.settings.chat_runs_path", str(runs_dir)):
                        with patch("app.main.resolve_provider_model", return_value=("ollama", "granite4.1:8b")):
                            with patch("app.main.ask_chat", side_effect=ask_chat_side_effect):
                                first_response = client.post(
                                    "/chat",
                                    json={
                                        "message": "Hola 1",
                                        "provider": "ollama",
                                        "model": "granite4.1:8b",
                                        "use_rag": False,
                                        "conversation_id": self.CONVERSATION_ID,
                                        "conversation_window": 4,
                                    },
                                )
                                second_response = client.post(
                                    "/chat",
                                    json={
                                        "message": "Hola 2",
                                        "provider": "ollama",
                                        "model": "granite4.1:8b",
                                        "use_rag": False,
                                        "conversation_id": self.CONVERSATION_ID,
                                        "conversation_window": 2,
                                    },
                                )

            self.assertEqual(first_response.status_code, 200)
            self.assertEqual(second_response.status_code, 200)
            self.assertEqual(len(captured_messages), 2)
            self.assertEqual(captured_messages[0], "Hola 1")
            self.assertIn("1. Usuario: Hola 1", captured_messages[1])
            self.assertIn("2. Asistente: Primera respuesta.", captured_messages[1])
            self.assertIn("Mensaje actual:\nHola 2", captured_messages[1])

            second_payload = second_response.json()
            self.assertEqual(second_payload["conversation_id"], self.CONVERSATION_ID)
            self.assertEqual(second_payload["conversation_window"], 2)
            self.assertEqual(second_payload["conversation_messages_used"], 2)

            run_files = sorted(runs_dir.glob("*.json"))
            self.assertEqual(len(run_files), 2)
            persisted_payload = json.loads(run_files[-1].read_text(encoding="utf-8"))
            self.assertEqual(persisted_payload["conversation_id"], self.CONVERSATION_ID)
            self.assertEqual(persisted_payload["conversation_window"], 2)
            self.assertEqual(persisted_payload["conversation_messages_used"], 2)


if __name__ == "__main__":
    unittest.main()
