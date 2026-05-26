import unittest

from app.chat.fallback import (
    ANSWER_MODE_DOCUMENTARY,
    ANSWER_MODE_SAFE_REFUSAL,
    build_safe_refusal_chat_response,
    fallback_used_from_state,
    fallback_reason_from_state,
    finalize_rag_answer,
)
from app.chat.retrieval import NO_EVIDENCE_MARKER


class ChatFallbackTests(unittest.TestCase):
    def _context(self) -> dict:
        return {
            "query_original": "hola",
            "query_normalized": "hola",
            "query_terms": ["hola"],
            "quoted_terms": [],
            "source_intent": "mixed",
            "selected_corpus": "mixed",
            "active_document_id": None,
            "active_document_title": None,
            "active_context_used": False,
            "active_context_reason": None,
            "query_expansion_used": False,
            "query_expansion_reason": None,
            "expanded_query_terms": [],
            "candidate_filenames": ["doc.md"],
            "selected_filenames": ["doc.md"],
            "scores": [1],
            "warnings": [],
            "chunks": [{"id": 1}],
            "chunk_ids": [1],
            "document_ids": [2],
            "source_filenames": ["doc.md"],
        }

    def test_finalize_rag_answer_documentary_answer(self):
        answer, answer_mode = finalize_rag_answer(
            retrieval_status="EVIDENCE_FOUND",
            raw_answer="NO_EVIDENCE_FOR_ANSWER\nRespuesta documental.",
        )

        self.assertEqual(answer, "Respuesta documental.")
        self.assertEqual(answer_mode, ANSWER_MODE_DOCUMENTARY)

    def test_finalize_rag_answer_no_evidence_marker(self):
        answer, answer_mode = finalize_rag_answer(
            retrieval_status=NO_EVIDENCE_MARKER,
            raw_answer="cualquier cosa",
        )

        self.assertIn(NO_EVIDENCE_MARKER, answer)
        self.assertEqual(answer_mode, ANSWER_MODE_SAFE_REFUSAL)

    def test_safe_refusal_response_preserves_trace_id(self):
        context = self._context()

        response = build_safe_refusal_chat_response(
            trace_id="12345678123456781234567812345678",
            context=context,
            provider="ollama",
            model="granite4.1:8b",
            temperature=0.2,
            temperature_ignored=False,
            use_rag=True,
            latency_ms=12,
        )

        self.assertEqual(response.trace_id, "12345678123456781234567812345678")
        self.assertEqual(response.retrieval_status, NO_EVIDENCE_MARKER)
        self.assertEqual(response.answer_mode, ANSWER_MODE_SAFE_REFUSAL)
        self.assertEqual(response.chunk_ids, [])
        self.assertEqual(response.document_ids, [])
        self.assertEqual(response.source_filenames, [])

    def test_fallback_reason_no_evidence(self):
        reason = fallback_reason_from_state(
            retrieval_status=NO_EVIDENCE_MARKER,
            answer_mode="standard_answer",
            evidence_used=False,
        )

        self.assertEqual(reason, "no_evidence")

    def test_retrieval_status_no_evidence_sets_fallback_used_true(self):
        self.assertTrue(
            fallback_used_from_state(
                retrieval_status=NO_EVIDENCE_MARKER,
                answer_mode="standard_answer",
                evidence_used=False,
            )
        )


if __name__ == "__main__":
    unittest.main()
