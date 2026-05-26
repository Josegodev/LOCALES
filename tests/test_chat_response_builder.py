import unittest

from app.chat.response_builder import build_chat_response


class ChatResponseBuilderTests(unittest.TestCase):
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
            "warnings": ["warning-text", {"code": "STRUCTURED"}],
        }

    def test_response_builder_preserves_public_contract(self):
        response = build_chat_response(
            trace_id="12345678123456781234567812345678",
            response_payload={
                "status": "ok",
                "provider": "ollama",
                "model": "granite4.1:8b",
                "temperature": 0.2,
                "temperature_ignored": False,
                "use_rag": True,
                "answer": "Respuesta documental.",
                "latency_ms": 25,
                "prompt_eval_count": 10,
                "eval_count": 20,
                "total_duration": 100,
                "load_duration": 50,
            },
            context=self._context(),
            retrieval_status="EVIDENCE_FOUND",
            answer_mode="documentary_answer",
            evidence_used=True,
            fallback_used=False,
            chunk_texts=["texto"],
            chunk_ids=[1],
            document_ids=[2],
            source_filenames=["doc.md"],
        )

        self.assertEqual(response.trace_id, "12345678123456781234567812345678")
        self.assertEqual(response.retrieval_status, "EVIDENCE_FOUND")
        self.assertEqual(response.answer_mode, "documentary_answer")
        self.assertTrue(response.evidence_used)
        self.assertFalse(response.fallback_used)
        self.assertEqual(response.warnings, ["warning-text", {"code": "STRUCTURED"}])
        self.assertIsInstance(response.warnings, list)
        self.assertEqual(response.prompt_eval_count, 10)
        self.assertEqual(response.eval_count, 20)
        self.assertEqual(response.total_duration, 100)
        self.assertEqual(response.load_duration, 50)
        self.assertEqual(response.chunk_ids, [1])
        self.assertEqual(response.document_ids, [2])
        self.assertEqual(response.source_filenames, ["doc.md"])


if __name__ == "__main__":
    unittest.main()
