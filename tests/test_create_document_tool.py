import asyncio
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from app.schemas import CreateDocumentRequest
from app.services import document_writer
from app.tools.create_document import create_document_tool


class CreateDocumentToolTests(unittest.TestCase):
    def test_create_document_tool_reports_overwrite_not_requested(self):
        request = CreateDocumentRequest(
            request_id="12345678-1234-5678-1234-567812345678",
            filename="prueba.md",
            content="# Titulo\n\nContenido inicial.",
            overwrite=False,
            user_id=7,
            chat_id=9,
        )

        with TemporaryDirectory() as tmpdir:
            documents_dir = Path(tmpdir) / "documents"
            with patch.object(document_writer, "DOCUMENTS_DIR", documents_dir):
                result = asyncio.run(create_document_tool(request=request))
                self.assertTrue(Path(result["document_path"]).exists())

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["tool_called"], "create_document")
        self.assertEqual(result["content_source"], "request")
        self.assertEqual(result["filename"], "prueba.md")
        self.assertEqual(result["format"], ".md")
        self.assertFalse(result["overwrite_requested"])
        self.assertFalse(result["overwrite_applied"])
        self.assertEqual(result["overwrite_reason"], "unique_trace_filename_policy")
        self.assertTrue(result["document_filename"].endswith(".md"))
        self.assertEqual(Path(result["document_path"]).parent, documents_dir)

    def test_create_document_tool_reports_overwrite_requested_but_not_applied(self):
        request = CreateDocumentRequest(
            request_id="87654321-4321-8765-4321-876543218765",
            filename="manual.md",
            content="## Manual\n\nPaso 1.",
            overwrite=True,
            user_id=11,
            chat_id=13,
        )

        with TemporaryDirectory() as tmpdir:
            documents_dir = Path(tmpdir) / "documents"
            with patch.object(document_writer, "DOCUMENTS_DIR", documents_dir):
                result = asyncio.run(create_document_tool(request=request))

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["tool_called"], "create_document")
        self.assertEqual(result["content_source"], "request")
        self.assertEqual(result["filename"], "manual.md")
        self.assertTrue(result["overwrite_requested"])
        self.assertFalse(result["overwrite_applied"])
        self.assertEqual(result["overwrite_reason"], "unique_trace_filename_policy")
        self.assertTrue(result["document_filename"].endswith(".md"))

    def test_create_document_tool_keeps_unique_markdown_filenames_when_overwrite_changes(self):
        first_request = CreateDocumentRequest(
            request_id="11111111-1111-4111-8111-111111111111",
            filename="manual.md",
            content="## Manual\n\nPrimera version.",
            overwrite=False,
            user_id=3,
            chat_id=4,
        )
        second_request = CreateDocumentRequest(
            request_id="22222222-2222-4222-8222-222222222222",
            filename="manual.md",
            content="## Manual\n\nSegunda version.",
            overwrite=True,
            user_id=3,
            chat_id=4,
        )

        with TemporaryDirectory() as tmpdir:
            documents_dir = Path(tmpdir) / "documents"
            with patch.object(document_writer, "DOCUMENTS_DIR", documents_dir):
                first_result = asyncio.run(create_document_tool(request=first_request))
                second_result = asyncio.run(create_document_tool(request=second_request))

        self.assertEqual(first_result["status"], "ok")
        self.assertEqual(second_result["status"], "ok")
        self.assertNotEqual(first_result["document_filename"], second_result["document_filename"])
        self.assertTrue(first_result["document_filename"].endswith(".md"))
        self.assertTrue(second_result["document_filename"].endswith(".md"))

    def test_create_document_tool_returns_missing_instruction_when_content_is_missing(self):
        request = {
            "request_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
            "filename": "faltante.md",
            "overwrite": False,
            "user_id": 1,
            "chat_id": 2,
        }

        result = asyncio.run(create_document_tool(request=request))

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error_type"], "missing_instruction")
        self.assertEqual(result["tool_called"], "create_document")


if __name__ == "__main__":
    unittest.main()
