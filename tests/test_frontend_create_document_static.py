import unittest
from pathlib import Path


class FrontendCreateDocumentStaticTests(unittest.TestCase):
    REPO_ROOT = Path(__file__).resolve().parents[1]

    def test_frontend_exposes_create_document_button_and_command_prefix(self):
        frontend_html = (self.REPO_ROOT / "frontend" / "index.html").read_text(encoding="utf-8")
        frontend_js = (self.REPO_ROOT / "frontend" / "app.js").read_text(encoding="utf-8")

        self.assertIn('id="createDocumentButton"', frontend_html)
        self.assertIn('const CREATE_DOCUMENT_PREFIX = "/creardoc"', frontend_js)
        self.assertIn("elements.useRagInput.checked = false;", frontend_js)


if __name__ == "__main__":
    unittest.main()
