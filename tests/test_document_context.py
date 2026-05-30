import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from DB.chunks import document_context


def _create_legacy_documents_sqlite(db_path: Path) -> None:
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
            (
                "Attention is all yout need.pdf",
                "/tmp/pdf/Attention is all yout need.pdf",
                "sha-pdf",
                "The paper introduces the Transformer architecture based entirely on attention.",
            ),
            (
                "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks - Patrick Lewis et al..pdf",
                "/tmp/pdf/Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks - Patrick Lewis et al..pdf",
                "sha-rag-pdf",
                "RAG improves knowledge-intensive generation by conditioning the model on retrieved passages from a dense index.",
            ),
            (
                "EVOLUTION_MAP.md",
                "/home/jose-gonzalez-oliva/NUCLEO/docs_esp/EVOLUTION_MAP.md",
                "sha-evolution",
                "NUCLEO AgentRuntime acts as the orchestrator of execution.",
            ),
            (
                "orchestrator.md",
                "/home/jose-gonzalez-oliva/NUCLEO/docs_esp/modules/orchestrator.md",
                "sha-orchestrator",
                "El orquestador coordina planner, policy y runtime de NUCLEO.",
            ),
            (
                "internal_transformers.md",
                "/home/jose-gonzalez-oliva/NUCLEO/docs_esp/internal_transformers.md",
                "sha-internal-transformers",
                "Nota interna que menciona transformers pero no es documentación oficial.",
            ),
            (
                "session_20260501_frontend_unificado.md",
                "/home/jose-gonzalez-oliva/NUCLEO/sessions/session_20260501_frontend_unificado.md",
                "sha-session",
                "La sesion interna habla del rendimiento del frontend unificado, no del paper de RAG.",
            ),
        ]

        for filename, source_path, sha256, raw_markdown in documents:
            conn.execute(
                """
                INSERT INTO documents (filename, source_path, sha256, raw_markdown, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    filename,
                    source_path,
                    sha256,
                    raw_markdown,
                    "2026-05-09T00:00:00Z",
                ),
            )

        chunks = [
            (
                1,
                0,
                "The paper introduces the Transformer architecture based entirely on attention.",
            ),
            (
                2,
                0,
                "RAG improves knowledge-intensive generation by conditioning the model on retrieved passages from a dense index.",
            ),
            (
                3,
                0,
                "NUCLEO AgentRuntime acts as the orchestrator of execution.",
            ),
            (
                4,
                0,
                "El orquestador coordina planner, policy y runtime de NUCLEO.",
            ),
            (
                5,
                0,
                "Documento interno que menciona transformers en un contexto no oficial.",
            ),
            (
                6,
                0,
                "La sesion interna habla del rendimiento del frontend unificado, no del paper de RAG.",
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


class DocumentContextTests(unittest.TestCase):
    def test_safe_migration_adds_document_metadata_and_classifies_existing_rows(self):
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "documents.sqlite"
            _create_legacy_documents_sqlite(db_path)

            with patch.object(document_context, "DB_PATH", db_path):
                document_context.search_chunks(query='que dice el paper sobre "transformers"?', limit=5)

            conn = sqlite3.connect(db_path)
            try:
                columns = {
                    row[1]
                    for row in conn.execute("PRAGMA table_info(documents)").fetchall()
                }
                rows = conn.execute(
                    """
                    SELECT filename, corpus, source_type, priority
                    FROM documents
                    ORDER BY id
                    """
                ).fetchall()
            finally:
                conn.close()

        self.assertIn("corpus", columns)
        self.assertIn("source_type", columns)
        self.assertIn("priority", columns)
        rows_by_filename = {row[0]: row[1:] for row in rows}
        self.assertEqual(
            rows_by_filename["Attention is all yout need.pdf"],
            ("documentos_oficiales", "pdf", 100),
        )
        self.assertEqual(
            rows_by_filename["EVOLUTION_MAP.md"],
            ("nucleo", "markdown", 50),
        )

    def test_official_docs_query_prefers_pdf_corpus_for_spanish_paper_query(self):
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "documents.sqlite"
            _create_legacy_documents_sqlite(db_path)

            with patch.object(document_context, "DB_PATH", db_path):
                context = document_context.build_document_prompt(
                    query='que dice el paper sobre "transformers"?',
                    limit=5,
                )

        self.assertEqual(context["status"], "EVIDENCE_FOUND")
        self.assertEqual(context["source_intent"], "official_docs")
        self.assertEqual(context["selected_corpus"], "documentos_oficiales")
        self.assertEqual(context["selected_filenames"][0], "Attention is all yout need.pdf")

    def test_official_docs_query_prefers_pdf_corpus_for_english_paper_query(self):
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "documents.sqlite"
            _create_legacy_documents_sqlite(db_path)

            with patch.object(document_context, "DB_PATH", db_path):
                context = document_context.build_document_prompt(
                    query="what the paper say about transformers?",
                    limit=5,
                )

        self.assertEqual(context["status"], "EVIDENCE_FOUND")
        self.assertEqual(context["source_intent"], "official_docs")
        self.assertEqual(context["selected_filenames"][0], "Attention is all yout need.pdf")
        self.assertIn("Attention is all yout need.pdf", context["candidate_filenames"])

    def test_nucleo_query_prefers_internal_docs(self):
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "documents.sqlite"
            _create_legacy_documents_sqlite(db_path)

            with patch.object(document_context, "DB_PATH", db_path):
                context = document_context.build_document_prompt(
                    query="qué hace el orquestador de NUCLEO?",
                    limit=5,
                )

        self.assertEqual(context["status"], "EVIDENCE_FOUND")
        self.assertEqual(context["source_intent"], "nucleo")
        self.assertEqual(context["selected_corpus"], "nucleo")
        self.assertIn(context["selected_filenames"][0], {"EVOLUTION_MAP.md", "orchestrator.md"})
        self.assertNotEqual(context["selected_filenames"][0], "Attention is all yout need.pdf")

    def test_search_chunks_filters_by_allowed_source_filenames(self):
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "documents.sqlite"
            _create_legacy_documents_sqlite(db_path)

            with patch.object(document_context, "DB_PATH", db_path):
                results = document_context.search_chunks(
                    query="AgentRuntime orquestador producción",
                    limit=5,
                    allowed_source_filenames=["EVOLUTION_MAP.md"],
                )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["filename"], "EVOLUTION_MAP.md")

    def test_active_document_context_can_keep_pdf_for_referential_follow_up_query(self):
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "documents.sqlite"
            _create_legacy_documents_sqlite(db_path)

            with patch.object(document_context, "DB_PATH", db_path):
                context = document_context.build_document_prompt(
                    query="que dice esa arquitectura?",
                    limit=3,
                    active_document_id=1,
                    active_document_title="Attention is all yout need.pdf",
                    allow_active_document_fallback=True,
                    active_context_reason="referential_query",
                )

        self.assertEqual(context["status"], "EVIDENCE_FOUND")
        self.assertTrue(context["active_context_used"])
        self.assertEqual(context["active_context_reason"], "referential_query")
        self.assertEqual(context["active_document_id"], 1)
        self.assertEqual(context["selected_filenames"], ["Attention is all yout need.pdf"])
        self.assertEqual(context["selected_corpus"], "documentos_oficiales")

    def test_rag_follow_up_with_active_pdf_avoids_session_markdown_contamination(self):
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "documents.sqlite"
            _create_legacy_documents_sqlite(db_path)

            with patch.object(document_context, "DB_PATH", db_path):
                context = document_context.build_document_prompt(
                    query="como se mejora ese rendimiento con RAG?",
                    limit=3,
                    active_document_id=2,
                    active_document_title=(
                        "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks - "
                        "Patrick Lewis et al..pdf"
                    ),
                    allow_active_document_fallback=True,
                    active_context_reason="referential_query",
                    active_corpus="documentos_oficiales",
                    last_source_intent="official_docs",
                )

        self.assertEqual(context["status"], "EVIDENCE_FOUND")
        self.assertEqual(context["source_intent"], "official_docs")
        self.assertEqual(context["selected_corpus"], "documentos_oficiales")
        self.assertTrue(context["active_context_used"])
        self.assertEqual(
            context["selected_filenames"],
            ["Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks - Patrick Lewis et al..pdf"],
        )
        self.assertNotIn("session_20260501_frontend_unificado.md", context["selected_filenames"])

    def test_rag_query_without_active_document_prefers_pdf_corpus_over_internal_session(self):
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "documents.sqlite"
            _create_legacy_documents_sqlite(db_path)

            with patch.object(document_context, "DB_PATH", db_path):
                context = document_context.build_document_prompt(
                    query="como mejora RAG el rendimiento?",
                    limit=3,
                )

        self.assertEqual(context["status"], "EVIDENCE_FOUND")
        self.assertEqual(context["source_intent"], "official_docs")
        self.assertEqual(context["selected_corpus"], "documentos_oficiales")
        self.assertIn(
            "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks - Patrick Lewis et al..pdf",
            context["selected_filenames"],
        )
        self.assertNotIn("session_20260501_frontend_unificado.md", context["selected_filenames"])

    def test_documento_con_titulo_expresa_intent_de_documentos_oficiales(self):
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "documents.sqlite"
            _create_legacy_documents_sqlite(db_path)

            with patch.object(document_context, "DB_PATH", db_path):
                context = document_context.build_document_prompt(
                    query='qué dice el documento "Attention is all yout need"?',
                    limit=3,
                )

        self.assertEqual(context["source_intent"], "official_docs")
        self.assertEqual(context["selected_corpus"], "documentos_oficiales")
        self.assertEqual(context["selected_filenames"][0], "Attention is all yout need.pdf")

    def test_spanish_attention_query_uses_domain_dictionary_expansion(self):
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "documents.sqlite"
            _create_legacy_documents_sqlite(db_path)

            with patch.object(document_context, "DB_PATH", db_path):
                context = document_context.build_document_prompt(
                    query="¿que es un mecanismo de atencion?",
                    limit=3,
                )

        self.assertTrue(context["query_expansion_used"])
        self.assertEqual(context["query_expansion_reason"], "domain_dictionary")
        self.assertTrue(
            any(
                term in context["expanded_query_terms"]
                for term in ("attention", "self-attention", "attention mechanism")
            )
        )


if __name__ == "__main__":
    unittest.main()
