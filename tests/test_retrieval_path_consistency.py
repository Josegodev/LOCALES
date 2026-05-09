import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from DB.chunks import document_context
from DB.chunks import search_docs
from app import rag_store


def _create_documents_sqlite(db_path: Path) -> None:
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

        documents = [
            ("EVOLUTION_MAP.md", "/docs/EVOLUTION_MAP.md", "sha-evolution"),
            ("ARCHITECTURE.md", "/docs/ARCHITECTURE.md", "sha-architecture"),
            (
                "CONTRACT_POLICY_TOOLREGISTRY.md",
                "/docs/CONTRACT_POLICY_TOOLREGISTRY.md",
                "sha-contract",
            ),
            ("MEMORIA 27.12.2021.pdf", "/docs/MEMORIA 27.12.2021.pdf", "sha-memoria"),
        ]
        for filename, source_path, sha256 in documents:
            conn.execute(
                """
                INSERT INTO documents (filename, source_path, sha256, raw_markdown, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    filename,
                    source_path,
                    sha256,
                    f"Contenido para {filename}",
                    "2026-05-09T00:00:00Z",
                ),
            )

        chunks = [
            (
                1,
                0,
                "El AgentRuntime figura como orquestador de producción en el mapa evolutivo.",
            ),
            (
                2,
                0,
                "La arquitectura describe el orquestador y su relación con policy.",
            ),
            (
                3,
                0,
                "El contrato de policy y tool registry cierra el comportamiento del orquestador.",
            ),
            (
                4,
                0,
                "La memoria antigua también menciona orquestador y AgentRuntime fuera del dominio NUCLEO.",
            ),
        ]
        for document_id, chunk_index, text in chunks:
            conn.execute(
                """
                INSERT INTO chunks (document_id, chunk_index, text, char_count, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    chunk_index,
                    text,
                    len(text),
                    "2026-05-09T00:00:00Z",
                ),
            )

        conn.commit()
    finally:
        conn.close()


class RetrievalPathConsistencyTests(unittest.TestCase):
    def test_search_docs_filters_by_allowed_source_filenames(self):
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "documents.sqlite"
            _create_documents_sqlite(db_path)

            with patch.object(document_context, "DB_PATH", db_path):
                results = search_docs.search_chunks(
                    query="¿Qué función tiene el orquestador?",
                    limit=10,
                    allowed_source_filenames=["/tmp/EVOLUTION_MAP.md", "ARCHITECTURE.md"],
                )

        self.assertEqual(
            sorted({item["filename"] for item in results}),
            ["ARCHITECTURE.md", "EVOLUTION_MAP.md"],
        )
        self.assertNotIn("MEMORIA 27.12.2021.pdf", [item["filename"] for item in results])

    def test_rag_store_filters_by_allowed_source_filenames_and_preserves_source_alias(self):
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "documents.sqlite"
            _create_documents_sqlite(db_path)

            with patch.object(document_context, "DB_PATH", db_path):
                results = rag_store.search_chunks(
                    query="¿Qué función tiene el orquestador?",
                    limit=10,
                    allowed_source_filenames=["CONTRACT_POLICY_TOOLREGISTRY.md"],
                )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["filename"], "CONTRACT_POLICY_TOOLREGISTRY.md")
        self.assertEqual(results[0]["source"], "CONTRACT_POLICY_TOOLREGISTRY.md")

    def test_search_without_allowlist_keeps_legacy_behavior(self):
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "documents.sqlite"
            _create_documents_sqlite(db_path)

            with patch.object(document_context, "DB_PATH", db_path):
                results = search_docs.search_chunks(
                    query="¿Qué función tiene el orquestador?",
                    limit=10,
                )

        self.assertIn("MEMORIA 27.12.2021.pdf", [item["filename"] for item in results])

    def test_build_document_prompt_returns_no_evidence_when_allowlist_has_no_matches(self):
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "documents.sqlite"
            _create_documents_sqlite(db_path)

            with patch.object(document_context, "DB_PATH", db_path):
                context = document_context.build_document_prompt(
                    query="¿Qué función tiene el orquestador?",
                    limit=10,
                    allowed_source_filenames=["README.md"],
                )

        self.assertEqual(context["status"], "NO_EVIDENCE")
        self.assertEqual(context["chunks"], [])

    def test_regression_orchestrator_query_never_returns_memoria_when_allowlisted(self):
        allowed_source_filenames = [
            "EVOLUTION_MAP.md",
            "ARCHITECTURE.md",
            "CONTRACT_POLICY_TOOLREGISTRY.md",
        ]

        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "documents.sqlite"
            _create_documents_sqlite(db_path)

            with patch.object(document_context, "DB_PATH", db_path):
                results = document_context.search_chunks(
                    query="¿Qué función tiene el orquestador?",
                    limit=10,
                    allowed_source_filenames=allowed_source_filenames,
                )

        source_filenames = [item["filename"] for item in results]
        self.assertNotIn("MEMORIA 27.12.2021.pdf", source_filenames)
        self.assertTrue(source_filenames)
        self.assertTrue(set(source_filenames).issubset(set(allowed_source_filenames)))


if __name__ == "__main__":
    unittest.main()
