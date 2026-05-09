import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from DB.chunks import document_context


class DocumentContextTests(unittest.TestCase):
    def test_search_chunks_filters_by_allowed_source_filenames(self):
        with TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "documents.sqlite"
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
                        "EVOLUTION_MAP.md",
                        "/docs/EVOLUTION_MAP.md",
                        "sha-evolution",
                        "AgentRuntime como orquestador de producción",
                        "2026-05-09T00:00:00Z",
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO documents (filename, source_path, sha256, raw_markdown, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        "UNRELATED_NOTES.md",
                        "/docs/UNRELATED_NOTES.md",
                        "sha-unrelated",
                        "AgentRuntime texto contaminante",
                        "2026-05-09T00:00:00Z",
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
                        "El AgentRuntime funciona como orquestador de producción.",
                        60,
                        "2026-05-09T00:00:00Z",
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
                        "El AgentRuntime aparece aquí pero en un dominio ajeno.",
                        56,
                        "2026-05-09T00:00:00Z",
                    ),
                )
                conn.commit()
            finally:
                conn.close()

            with patch.object(document_context, "DB_PATH", db_path):
                results = document_context.search_chunks(
                    query="AgentRuntime orquestador producción",
                    limit=5,
                    allowed_source_filenames=["EVOLUTION_MAP.md"],
                )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["filename"], "EVOLUTION_MAP.md")


if __name__ == "__main__":
    unittest.main()
