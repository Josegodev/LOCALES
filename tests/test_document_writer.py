import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

from app.document_writer import (
    DocumentWriteError,
    create_document,
)

REQUEST_ID = "12345678123456781234567812345678"


class CreateDocumentTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._safe_root = Path(self._tmpdir.name) / "TELEGRAM_DOCS"
        self._safe_root.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self._tmpdir.cleanup()

    def _create(self, filename, content="hello", overwrite=False):
        with patch("app.document_writer.SAFE_ROOT", self._safe_root):
            with patch("app.document_writer.BASE_DIR", self._safe_root):
                return create_document(filename, content, request_id=REQUEST_ID, overwrite=overwrite)

    def test_creates_file_successfully(self):
        result = self._create("test.md")
        self.assertEqual(result["status"], "created")
        self.assertEqual(result["filename"], "test.md")
        self.assertEqual(result["chars"], 5)
        self.assertIn("created_at", result)
        self.assertTrue((self._safe_root / "test.md").exists())

    def test_empty_filename_raises_error(self):
        with self.assertRaises(DocumentWriteError) as ctx:
            self._create("")
        self.assertEqual(ctx.exception.code, "filename_required")

    def test_none_filename_raises_error(self):
        with self.assertRaises(DocumentWriteError) as ctx:
            self._create(None)
        self.assertEqual(ctx.exception.code, "filename_required")

    def test_whitespace_filename_raises_error(self):
        with self.assertRaises(DocumentWriteError) as ctx:
            self._create("   ")
        self.assertEqual(ctx.exception.code, "filename_required")

    def test_absolute_path_rejected(self):
        with self.assertRaises(DocumentWriteError) as ctx:
            self._create("/etc/passwd.md")
        self.assertEqual(ctx.exception.code, "absolute_path_not_allowed")

    def test_parent_directory_traversal_rejected(self):
        with self.assertRaises(DocumentWriteError) as ctx:
            self._create("../evil.md")
        self.assertEqual(ctx.exception.code, "parent_directory_not_allowed")

    def test_path_separator_rejected(self):
        with self.assertRaises(DocumentWriteError) as ctx:
            self._create("sub/file.md")
        self.assertEqual(ctx.exception.code, "path_not_allowed")

    def test_backslash_separator_rejected(self):
        with self.assertRaises(DocumentWriteError) as ctx:
            self._create("sub\\file.md")
        self.assertEqual(ctx.exception.code, "path_not_allowed")

    def test_non_md_extension_rejected(self):
        with self.assertRaises(DocumentWriteError) as ctx:
            self._create("test.txt")
        self.assertEqual(ctx.exception.code, "extension_not_allowed")

    def test_empty_content_rejected(self):
        with self.assertRaises(DocumentWriteError) as ctx:
            self._create("test.md", content="   ")
        self.assertEqual(ctx.exception.code, "content_required")

    def test_non_string_content_rejected(self):
        with self.assertRaises(DocumentWriteError) as ctx:
            self._create("test.md", content=123)
        self.assertEqual(ctx.exception.code, "content_invalid")

    def test_content_too_large_rejected(self):
        with self.assertRaises(DocumentWriteError) as ctx:
            self._create("test.md", content="x" * 100_001)
        self.assertEqual(ctx.exception.code, "content_too_large")

    def test_duplicate_file_without_overwrite_rejected(self):
        self._create("dup.md")
        with self.assertRaises(DocumentWriteError) as ctx:
            self._create("dup.md")
        self.assertEqual(ctx.exception.code, "file_exists")

    def test_request_id_in_result(self):
        result = self._create("output.md")
        self.assertEqual(result["request_id"], REQUEST_ID)


if __name__ == "__main__":
    unittest.main()
