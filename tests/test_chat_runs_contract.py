import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.observability.chat_runs import list_chat_runs, save_chat_run


class ChatRunsContractTests(unittest.TestCase):
    def test_save_and_list_chat_runs_preserve_basic_fields_and_types(self):
        payload = {
            "trace_id": "12345678-1234-5678-1234-567812345678",
            "created_at": "2026-05-16T12:00:00+00:00",
            "source": "chat",
            "input": "hola",
            "response": "ok",
            "provider": "ollama",
            "requested_model": "granite",
            "model": "granite4.1:8b",
            "temperature": "0.2",
            "max_tokens": "128",
            "top_p": "0.9",
            "status": "ok",
            "retrieval_status": "EVIDENCE_FOUND",
            "chunk_ids": ["1", 2],
            "document_ids": ["3", 4],
            "source_filenames": ["doc.md"],
            "warnings": ["warning-text"],
            "latency_ms": 14,
            "answer_mode": "documentary_answer",
            "fallback_used": False,
        }

        with TemporaryDirectory() as tmpdir:
            runs_dir = Path(tmpdir) / "CHAT_RUNS"
            save_chat_run(payload, path=runs_dir)
            records = list_chat_runs(path=runs_dir)

        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record.trace_id, "12345678-1234-5678-1234-567812345678")
        self.assertEqual(record.status, "ok")
        self.assertEqual(record.input, "hola")
        self.assertEqual(record.response, "ok")
        self.assertEqual(record.provider, "ollama")
        self.assertEqual(record.requested_model, "granite")
        self.assertEqual(record.model, "granite4.1:8b")
        self.assertEqual(record.temperature, 0.2)
        self.assertEqual(record.max_tokens, 128)
        self.assertEqual(record.top_p, 0.9)
        self.assertEqual(record.chunk_ids, [1, 2])
        self.assertEqual(record.document_ids, [3, 4])
        self.assertEqual(record.source_filenames, ["doc.md"])
        self.assertEqual(record.warnings, ["warning-text"])
        self.assertEqual(record.answer_mode, "documentary_answer")
        self.assertFalse(record.fallback_used)
        self.assertIsInstance(record.latency_ms, int)


if __name__ == "__main__":
    unittest.main()
