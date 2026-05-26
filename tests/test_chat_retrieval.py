import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.chat.retrieval import NO_EVIDENCE_MARKER, retrieve_chat_context
from app.schemas import ChatRequest


class ChatRetrievalTests(unittest.TestCase):
    def _request(self, **overrides) -> ChatRequest:
        payload = {
            "message": "hola",
            "provider": "ollama",
            "model": "granite4.1:8b",
            "use_rag": True,
            "allowed_source_filenames": [],
        }
        payload.update(overrides)
        return ChatRequest(**payload)

    def test_retrieve_chat_context_disabled_rag_keeps_disabled_contract(self):
        request = self._request(use_rag=False)

        result = retrieve_chat_context(
            request=request,
            trace_id="12345678123456781234567812345678",
            use_rag=False,
            settings_obj=SimpleNamespace(use_remote_rag=False),
            build_document_prompt_fn=lambda *args, **kwargs: {},
            query_remote_rag_fn=lambda *args, **kwargs: {},
        )

        self.assertEqual(result.retrieval_status, "DISABLED")
        self.assertEqual(result.context["retrieval_status"], "DISABLED")
        self.assertEqual(result.chunk_ids, [])
        self.assertEqual(result.document_ids, [])
        self.assertEqual(result.source_filenames, [])
        self.assertEqual(result.candidate_filenames, [])
        self.assertFalse(result.evidence_used)
        self.assertFalse(result.fallback_used)
        self.assertEqual(result.fallback_reason, None)

    def test_retrieve_chat_context_local_rag_with_evidence(self):
        request = self._request()
        build_document_prompt_mock = Mock(
            return_value={
                "status": "EVIDENCE_FOUND",
                "prompt": "context prompt",
                "chunks": [
                    {
                        "id": 7,
                        "document_id": 3,
                        "filename": "doc.md",
                        "text": "evidencia local suficiente",
                    }
                ],
                "warnings": [],
                "query_original": "hola",
                "query_normalized": "hola",
                "query_terms": ["hola"],
                "quoted_terms": [],
                "source_intent": "mixed",
                "selected_corpus": "mixed",
                "candidate_filenames": ["doc.md"],
                "selected_filenames": ["doc.md"],
                "scores": [1],
            }
        )
        query_remote_rag_mock = Mock()

        result = retrieve_chat_context(
            request=request,
            trace_id="12345678123456781234567812345678",
            use_rag=True,
            settings_obj=SimpleNamespace(use_remote_rag=False),
            build_document_prompt_fn=build_document_prompt_mock,
            query_remote_rag_fn=query_remote_rag_mock,
        )

        build_document_prompt_mock.assert_called_once()
        query_remote_rag_mock.assert_not_called()
        self.assertEqual(result.retrieval_status, "EVIDENCE_FOUND")
        self.assertTrue(result.evidence_used)
        self.assertFalse(result.fallback_used)
        self.assertEqual(result.chunk_ids, [7])
        self.assertEqual(result.document_ids, [3])
        self.assertEqual(result.source_filenames, ["doc.md"])
        self.assertEqual(result.candidate_filenames, ["doc.md"])

    def test_retrieve_chat_context_local_rag_without_evidence(self):
        request = self._request(message="que es self rag?")

        result = retrieve_chat_context(
            request=request,
            trace_id="12345678123456781234567812345678",
            use_rag=True,
            settings_obj=SimpleNamespace(use_remote_rag=False),
            build_document_prompt_fn=lambda *args, **kwargs: {
                "status": "NO_EVIDENCE",
                "retrieval_status": "NO_EVIDENCE",
                "prompt": "No hay evidencia documental suficiente para responder.",
                "chunks": [],
                "warnings": [],
                "query_original": "que es self rag?",
                "query_normalized": "que es self rag",
                "query_terms": ["self"],
                "quoted_terms": [],
                "source_intent": "mixed",
                "selected_corpus": "mixed",
                "candidate_filenames": [],
                "selected_filenames": [],
                "scores": [],
            },
            query_remote_rag_fn=lambda *args, **kwargs: {},
        )

        self.assertEqual(result.retrieval_status, NO_EVIDENCE_MARKER)
        self.assertFalse(result.evidence_used)
        self.assertTrue(result.fallback_used)
        self.assertEqual(result.fallback_reason, "no_evidence")
        self.assertEqual(result.chunk_ids, [])

    def test_retrieve_chat_context_remote_rag_propagates_allowed_source_filenames(self):
        request = self._request(allowed_source_filenames=["uno.md", "dos.md"])
        query_remote_rag_mock = Mock(
            return_value={
                "status": "EVIDENCE_FOUND",
                "retrieval_status": "EVIDENCE_FOUND",
                "prompt": "remote prompt",
                "chunks": [],
                "warnings": [],
                "candidate_filenames": ["uno.md", "dos.md"],
            }
        )

        retrieve_chat_context(
            request=request,
            trace_id="12345678123456781234567812345678",
            use_rag=True,
            settings_obj=SimpleNamespace(use_remote_rag=True),
            build_document_prompt_fn=lambda *args, **kwargs: {},
            query_remote_rag_fn=query_remote_rag_mock,
        )

        query_remote_rag_mock.assert_called_once_with(
            query="hola",
            top_k=3,
            trace_id="12345678123456781234567812345678",
            allowed_source_filenames=["uno.md", "dos.md"],
        )

    def test_retrieve_chat_context_remote_rag_preserves_structured_warning(self):
        request = self._request()
        warning = {"code": "RAG_SERVICE_UNAVAILABLE", "message": "Remote RAG service is unavailable."}

        result = retrieve_chat_context(
            request=request,
            trace_id="12345678123456781234567812345678",
            use_rag=True,
            settings_obj=SimpleNamespace(use_remote_rag=True),
            build_document_prompt_fn=lambda *args, **kwargs: {},
            query_remote_rag_fn=lambda *args, **kwargs: {
                "status": NO_EVIDENCE_MARKER,
                "retrieval_status": NO_EVIDENCE_MARKER,
                "prompt": "remote no evidence",
                "chunks": [],
                "warnings": [warning],
                "candidate_filenames": [],
                "selected_filenames": [],
            },
        )

        self.assertEqual(result.retrieval_status, NO_EVIDENCE_MARKER)
        self.assertEqual(result.warnings, [warning])
        self.assertEqual(result.context["warnings"], [warning])

    def test_retrieve_chat_context_remote_rag_recoverable_failure_degrades_to_no_evidence(self):
        request = self._request(message="pregunta remota")

        result = retrieve_chat_context(
            request=request,
            trace_id="12345678123456781234567812345678",
            use_rag=True,
            settings_obj=SimpleNamespace(use_remote_rag=True),
            build_document_prompt_fn=lambda *args, **kwargs: {},
            query_remote_rag_fn=lambda *args, **kwargs: {
                "status": NO_EVIDENCE_MARKER,
                "retrieval_status": NO_EVIDENCE_MARKER,
                "prompt": "No hay evidencia documental suficiente para responder.",
                "chunks": [],
                "warnings": [{"code": "RAG_SERVICE_ERROR", "message": "recoverable"}],
                "candidate_filenames": [],
                "selected_filenames": [],
            },
        )

        self.assertEqual(result.retrieval_status, NO_EVIDENCE_MARKER)
        self.assertFalse(result.evidence_used)
        self.assertTrue(result.fallback_used)
        self.assertEqual(result.fallback_reason, "no_evidence")


if __name__ == "__main__":
    unittest.main()
