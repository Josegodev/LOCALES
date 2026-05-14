import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import requests
from fastapi.testclient import TestClient

from app import rag_client
from app.config import settings
from app.main import app as chat_app
from rag_service.main import app as rag_app

REQUEST_ID = "12345678123456781234567812345678"
AUTH_HEADERS = {"Authorization": "Bearer test-dev-token"}
settings.jose_dev_token = "test-dev-token"


def _create_documents_db(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                source_path TEXT NOT NULL,
                sha256 TEXT NOT NULL UNIQUE,
                raw_markdown TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                text TEXT NOT NULL,
                char_count INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
            """
        )
        conn.execute(
            """
            INSERT INTO documents (filename, source_path, sha256, raw_markdown, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "Attention is all you need.pdf",
                "/srv/rag/pdf/Attention is all you need.pdf",
                "sha-attention",
                "The Transformer architecture is based on attention mechanisms.",
                "2026-05-11T00:00:00Z",
            ),
        )
        conn.execute(
            """
            INSERT INTO chunks (document_id, chunk_index, text, char_count, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                1,
                0,
                "The Transformer architecture is based on attention mechanisms.",
                61,
                "2026-05-11T00:00:00Z",
            ),
        )
        conn.execute(
            """
            INSERT INTO documents (filename, source_path, sha256, raw_markdown, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "NUCLEO_RUNTIME.md",
                "/srv/rag/docs/NUCLEO_RUNTIME.md",
                "sha-nucleo-runtime",
                "NUCLEO runtime coordinates planner policy and tools.",
                "2026-05-11T00:00:00Z",
            ),
        )
        conn.execute(
            """
            INSERT INTO chunks (document_id, chunk_index, text, char_count, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                2,
                0,
                "NUCLEO runtime coordinates planner policy and tools.",
                51,
                "2026-05-11T00:00:00Z",
            ),
        )
        conn.commit()
    finally:
        conn.close()


class RemoteRagServiceTests(unittest.TestCase):
    def test_chat_uses_local_rag_when_remote_rag_is_disabled(self):
        client = TestClient(chat_app, headers=AUTH_HEADERS)

        with patch("app.main.settings.use_remote_rag", False):
            with patch(
                "app.main.build_document_prompt",
                return_value={
                    "status": "EVIDENCE_FOUND",
                    "prompt": "local context prompt",
                    "chunks": [{"id": 1, "filename": "local.md", "text": "local evidence"}],
                },
            ) as build_document_prompt_mock:
                with patch("app.main.query_remote_rag") as query_remote_rag_mock:
                    with patch(
                        "app.main.ask_chat",
                        return_value={
                            "status": "ok",
                            "provider": "ollama",
                            "model": "granite4.1:8b",
                            "temperature": 0.2,
                            "use_rag": True,
                            "answer": "Respuesta local.",
                        },
                    ):
                        response = client.post(
                            "/chat",
                            json={
                                "message": "hola",
                                "trace_id": REQUEST_ID,
                                "user_id": 123,
                                "chat_id": 456,
                            },
                        )

        self.assertEqual(response.status_code, 200)
        build_document_prompt_mock.assert_called_once()
        query_remote_rag_mock.assert_not_called()

    def test_chat_uses_remote_rag_when_enabled(self):
        client = TestClient(chat_app, headers=AUTH_HEADERS)

        with patch("app.main.settings.use_remote_rag", True):
            with patch("app.main.build_document_prompt") as build_document_prompt_mock:
                with patch(
                    "app.main.query_remote_rag",
                    return_value={
                        "status": "EVIDENCE_FOUND",
                        "retrieval_status": "EVIDENCE_FOUND",
                        "prompt": "remote context prompt",
                        "chunks": [
                            {
                                "id": 7,
                                "document_id": 3,
                                "filename": "remote.pdf",
                                "text": "remote evidence",
                            }
                        ],
                        "warnings": [],
                    },
                ) as query_remote_rag_mock:
                    with patch(
                        "app.main.ask_chat",
                        return_value={
                            "status": "ok",
                            "provider": "ollama",
                            "model": "granite4.1:8b",
                            "temperature": 0.2,
                            "use_rag": True,
                            "answer": "Respuesta remota.",
                        },
                    ) as ask_chat_mock:
                        response = client.post(
                            "/chat",
                            json={
                                "message": "que es un transformer?",
                                "trace_id": REQUEST_ID,
                                "user_id": 123,
                                "chat_id": 456,
                            },
                        )

        self.assertEqual(response.status_code, 200)
        build_document_prompt_mock.assert_not_called()
        query_remote_rag_mock.assert_called_once_with(
            query="que es un transformer?",
            top_k=3,
            trace_id=REQUEST_ID,
            allowed_source_filenames=[],
        )
        ask_chat_mock.assert_called_once()
        self.assertEqual(ask_chat_mock.call_args.kwargs["message"], "remote context prompt")
        self.assertEqual(response.json()["chunk_ids"], [7])

    def test_rag_client_sends_allowed_source_filenames(self):
        captured: dict = {}

        class FakeResponse:
            status_code = 200

            @staticmethod
            def json() -> dict:
                return {
                    "status": "NO_EVIDENCE_FOR_ANSWER",
                    "retrieval_status": "NO_EVIDENCE_FOR_ANSWER",
                    "chunks": [],
                }

            @staticmethod
            def raise_for_status() -> None:
                return None

        def fake_post(url: str, json: dict, timeout: float):
            captured["url"] = url
            captured["json"] = json
            captured["timeout"] = timeout
            return FakeResponse()

        with patch.object(rag_client.requests, "post", side_effect=fake_post):
            rag_client.query_remote_rag(
                query="runtime",
                top_k=5,
                trace_id=REQUEST_ID,
                allowed_source_filenames=["NUCLEO_RUNTIME.md"],
            )

        self.assertEqual(captured["json"]["allowed_source_filenames"], ["NUCLEO_RUNTIME.md"])

    def test_rag_client_timeout_returns_controlled_no_evidence(self):
        with patch.object(rag_client.requests, "post", side_effect=requests.Timeout):
            result = rag_client.query_remote_rag(
                query="que es un transformer?",
                top_k=5,
                trace_id=REQUEST_ID,
            )

        self.assertEqual(result["retrieval_status"], "NO_EVIDENCE_FOR_ANSWER")
        self.assertFalse(result["evidence_used"])
        self.assertTrue(result["fallback_used"])
        self.assertEqual(result["chunks"], [])
        self.assertEqual(result["chunks_found"], 0)
        self.assertEqual(result["warnings"][0]["code"], "RAG_SERVICE_UNAVAILABLE")

    def test_rag_client_5xx_returns_controlled_service_error(self):
        class FakeResponse:
            status_code = 500

            @staticmethod
            def json() -> dict:
                return {"detail": "boom"}

        with patch.object(rag_client.requests, "post", return_value=FakeResponse()):
            result = rag_client.query_remote_rag(
                query="que es un transformer?",
                top_k=5,
                trace_id=REQUEST_ID,
            )

        self.assertEqual(result["retrieval_status"], "NO_EVIDENCE_FOR_ANSWER")
        self.assertEqual(result["warnings"][0]["code"], "RAG_SERVICE_ERROR")

    def test_rag_health_works_with_temp_db(self):
        client = TestClient(rag_app)

        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "documents.sqlite"
            _create_documents_db(db_path)

            with patch("rag_service.main.settings.documents_db_path", str(db_path)):
                response = client.get("/rag/health")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "ok")
        self.assertTrue(body["retrieval_ready"])
        self.assertEqual(body["documents_count"], 2)
        self.assertEqual(body["chunks_count"], 2)

    def test_rag_query_returns_controlled_no_evidence_when_db_invalid(self):
        client = TestClient(rag_app)

        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "documents.sqlite"
            sqlite3.connect(db_path).close()

            with patch("rag_service.main.settings.documents_db_path", str(db_path)):
                response = client.post(
                    "/rag/query",
                    json={
                        "query": "que es un transformer?",
                        "top_k": 5,
                        "trace_id": REQUEST_ID,
                    },
                )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["retrieval_status"], "NO_EVIDENCE_FOR_ANSWER")
        self.assertFalse(body["evidence_used"])
        self.assertTrue(body["fallback_used"])
        self.assertEqual(body["chunks_found"], 0)
        self.assertEqual(body["warnings"][0]["code"], "RAG_DB_SCHEMA_INVALID")

    def test_rag_query_returns_chunks_without_absolute_source_path(self):
        client = TestClient(rag_app)

        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "documents.sqlite"
            _create_documents_db(db_path)

            with patch("rag_service.main.settings.documents_db_path", str(db_path)):
                response = client.post(
                    "/rag/query",
                    json={
                        "query": "que es un transformer attention?",
                        "top_k": 5,
                        "trace_id": REQUEST_ID,
                    },
                )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["retrieval_status"], "EVIDENCE_FOUND")
        self.assertGreater(body["chunks_found"], 0)
        self.assertNotIn("source_path", body["chunks"][0])
        self.assertEqual(body["chunks"][0]["filename"], "Attention is all you need.pdf")

    def test_rag_query_respects_allowed_source_filenames(self):
        client = TestClient(rag_app)

        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "documents.sqlite"
            _create_documents_db(db_path)

            with patch("rag_service.main.settings.documents_db_path", str(db_path)):
                response = client.post(
                    "/rag/query",
                    json={
                        "query": "runtime planner policy",
                        "top_k": 5,
                        "trace_id": REQUEST_ID,
                        "allowed_source_filenames": ["NUCLEO_RUNTIME.md"],
                    },
                )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["retrieval_status"], "EVIDENCE_FOUND")
        self.assertGreater(body["chunks_found"], 0)
        self.assertEqual(
            {chunk["filename"] for chunk in body["chunks"]},
            {"NUCLEO_RUNTIME.md"},
        )

    def test_rag_query_allowed_source_without_matches_returns_no_evidence(self):
        client = TestClient(rag_app)

        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "documents.sqlite"
            _create_documents_db(db_path)

            with patch("rag_service.main.settings.documents_db_path", str(db_path)):
                response = client.post(
                    "/rag/query",
                    json={
                        "query": "runtime planner policy",
                        "top_k": 5,
                        "trace_id": REQUEST_ID,
                        "allowed_source_filenames": ["Attention is all you need.pdf"],
                    },
                )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["retrieval_status"], "NO_EVIDENCE_FOR_ANSWER")
        self.assertEqual(body["chunks_found"], 0)
        self.assertFalse(body["evidence_used"])
        self.assertTrue(body["fallback_used"])
        self.assertEqual(body["chunks"], [])
        self.assertEqual(body["warnings"], [])


if __name__ == "__main__":
    unittest.main()
