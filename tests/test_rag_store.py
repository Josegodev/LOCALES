import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

from app import rag_store


class SearchChunksTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._db_path = Path(self._tmpdir.name) / "document_chunks.sqlite"
        conn = sqlite3.connect(self._db_path)
        conn.execute("CREATE TABLE chunks (id INTEGER PRIMARY KEY, source TEXT, text TEXT)")
        conn.execute("INSERT INTO chunks (id, source, text) VALUES (1, 'doc1.md', 'este es un contenido de ejemplo sobre kubernetes')")
        conn.execute("INSERT INTO chunks (id, source, text) VALUES (2, 'doc2.md', 'configuración de docker compose para producción')")
        conn.execute("INSERT INTO chunks (id, source, text) VALUES (3, 'doc3.md', 'guía de kubernetes para deploy en producción')")
        conn.commit()
        conn.close()

    def tearDown(self):
        self._tmpdir.cleanup()

    def _search(self, query, limit=3):
        with patch.object(rag_store, "DB_PATH", self._db_path):
            return rag_store.search_chunks(query, limit=limit)

    def test_returns_matching_chunks(self):
        results = self._search("kubernetes producción")
        self.assertGreaterEqual(len(results), 1)
        texts = [r["text"] for r in results]
        self.assertTrue(any("kubernetes" in t for t in texts))

    def test_empty_query_returns_empty(self):
        results = self._search("a b")
        self.assertEqual(results, [])

    def test_no_matching_terms_returns_empty(self):
        results = self._search("zzzznonexistent")
        self.assertEqual(results, [])

    def test_results_sorted_by_score_descending(self):
        results = self._search("kubernetes producción")
        if len(results) >= 2:
            self.assertGreaterEqual(results[0]["score"], results[1]["score"])

    def test_limit_respected(self):
        results = self._search("kubernetes producción docker", limit=1)
        self.assertLessEqual(len(results), 1)

    def test_deduplication_by_id(self):
        results = self._search("kubernetes kubernetes")
        ids = [r["id"] for r in results]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
