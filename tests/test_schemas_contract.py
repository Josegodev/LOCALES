import unittest

from pydantic import ValidationError

from app.schemas import ChatRequest, ChatResponse


class SchemasContractTests(unittest.TestCase):
    def test_chat_request_normalizes_allowed_source_filenames(self):
        request = ChatRequest(
            message="hola",
            provider="ollama",
            model="granite4.1:8b",
            allowed_source_filenames=[" docs/manual.md ", "../privado.pdf", "manual.md"],
        )

        self.assertEqual(request.allowed_source_filenames, ["manual.md", "privado.pdf"])

    def test_chat_request_rejects_invalid_trace_id(self):
        with self.assertRaises(ValidationError):
            ChatRequest(
                message="hola",
                provider="ollama",
                model="granite4.1:8b",
                trace_id="trace-invalido",
            )

    def test_chat_response_preserves_critical_public_fields(self):
        response = ChatResponse(
            trace_id="12345678-1234-5678-1234-567812345678",
            status="ok",
            provider="ollama",
            model="granite4.1:8b",
            answer="ok",
            latency_ms=9,
            retrieval_status="EVIDENCE_FOUND",
            answer_mode="documentary_answer",
            warnings=["warning-text", {"code": "RAG_FALLBACK"}],
        )

        self.assertEqual(response.status, "ok")
        self.assertEqual(response.trace_id, "12345678-1234-5678-1234-567812345678")
        self.assertEqual(response.retrieval_status, "EVIDENCE_FOUND")
        self.assertEqual(response.answer_mode, "documentary_answer")
        self.assertEqual(response.latency_ms, 9)
        self.assertEqual(response.warnings, ["warning-text", {"code": "RAG_FALLBACK"}])


if __name__ == "__main__":
    unittest.main()
