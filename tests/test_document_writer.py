import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app.services import document_writer


class DocumentWriterTests(unittest.TestCase):
    def test_normalize_document_name_neutralizes_path_traversal(self):
        normalized = document_writer._normalize_document_name(filename="../secret.md")

        self.assertEqual(normalized, document_writer.DEFAULT_DOCUMENT_BASENAME)

    def test_normalize_document_name_neutralizes_absolute_path(self):
        normalized = document_writer._normalize_document_name(filename="/tmp/secret.md")

        self.assertEqual(normalized, document_writer.DEFAULT_DOCUMENT_BASENAME)

    def test_write_document_keeps_output_inside_documents_dir_for_dangerous_name(self):
        with TemporaryDirectory() as tmpdir:
            documents_dir = Path(tmpdir) / "documents"
            with patch.object(document_writer, "DOCUMENTS_DIR", documents_dir):
                result = document_writer.write_document(
                    content="Contenido estable.",
                    trace_id="12345678-1234-5678-1234-567812345678",
                    filename="../escape.md",
                )

                self.assertEqual(result["status"], "ok")
                output_path = Path(result["document_path"])
                self.assertEqual(output_path.parent, documents_dir)
                self.assertTrue(output_path.exists())
                self.assertIn(document_writer.DEFAULT_DOCUMENT_BASENAME, result["document_filename"])
                self.assertNotIn("..", result["document_filename"])
                self.assertNotIn("/", result["document_filename"])


if __name__ == "__main__":
    unittest.main()
