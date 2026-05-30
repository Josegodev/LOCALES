import unittest
from unittest.mock import Mock, patch

import requests
from fastapi.testclient import TestClient

from app.main import app
from app.rag_client import NO_EVIDENCE_MARKER, query_remote_rag


class RagNoEvidenceContractTests(unittest.TestCase):
    def test_remote_rag_timeout_returns_no_fake_evidence(self):
        with patch("app.rag_client.requests.post", side_effect=requests.Timeout):
            result = query_remote_rag("que es self rag?", top_k=3, trace_id="trace-1")

        self.assertEqual(result["status"], NO_EVIDENCE_MARKER)
        self.assertEqual(result["retrieval_status"], NO_EVIDENCE_MARKER)
        self.assertEqual(result["chunks"], [])
        self.assertEqual(result["chunk_ids"], [])
        self.assertEqual(result["document_ids"], [])
        self.assertEqual(result["source_filenames"], [])
        self.assertFalse(result["evidence_used"])
        self.assertTrue(result["fallback_used"])

    def test_chat_safe_refusal_clears_fake_evidence_from_no_evidence_context(self):
        client = TestClient(app)
        fake_context = {
            "status": "NO_EVIDENCE",
            "retrieval_status": "NO_EVIDENCE",
            "prompt": "No hay evidencia suficiente.",
            "chunks": [{"id": 99, "document_id": 7, "filename": "fake.md", "text": "inventado"}],
            "chunk_ids": [99],
            "document_ids": [7],
            "source_filenames": ["fake.md"],
            "selected_filenames": ["fake.md"],
            "candidate_filenames": ["fake.md"],
            "scores": [1],
            "ranking_scores": [1],
            "warnings": [],
            "query_original": "que es self rag?",
            "query_normalized": "que es self rag",
            "query_terms": ["self", "rag"],
            "quoted_terms": [],
            "source_intent": "mixed",
            "selected_corpus": "mixed",
            "active_context_used": False,
            "active_context_reason": None,
            "query_expansion_used": False,
            "query_expansion_reason": None,
            "expanded_query_terms": [],
        }

        with patch("app.auth.settings.chat_auth_mode", "local_open"):
            with patch("app.main.settings.use_remote_rag", False):
                with patch("app.main.build_document_prompt", return_value=fake_context):
                    with patch("app.main.ask_chat", new=Mock()) as ask_chat_mock:
                        response = client.post(
                            "/chat",
                            json={
                                "message": "que es self rag?",
                                "provider": "ollama",
                                "model": "granite4.1:8b",
                                "trace_id": "12345678-1234-5678-1234-567812345678",
                            },
                        )

        self.assertEqual(response.status_code, 200)
        ask_chat_mock.assert_not_called()
        payload = response.json()
        self.assertEqual(payload["retrieval_status"], NO_EVIDENCE_MARKER)
        self.assertEqual(payload["answer_mode"], "safe_refusal")
        self.assertEqual(payload["chunks"], [])
        self.assertEqual(payload["chunk_ids"], [])
        self.assertEqual(payload["document_ids"], [])
        self.assertEqual(payload["source_filenames"], [])
        self.assertEqual(payload["selected_filenames"], [])
        self.assertFalse(payload["evidence_used"])
        self.assertTrue(payload["fallback_used"])


if __name__ == "__main__":
    unittest.main()
