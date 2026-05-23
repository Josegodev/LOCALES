import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_API_CLIENT_JS = REPO_ROOT / "frontend" / "api-client.js"


class FrontendApiClientStaticTests(unittest.TestCase):
    def test_build_url_accepts_absolute_url_before_requiring_base_url(self):
        source = FRONTEND_API_CLIENT_JS.read_text(encoding="utf-8")

        absolute_url_check = 'if (/^https?:\\/\\//i.test(path)) {'
        base_url_resolution = "const resolvedBaseUrl = resolveConfiguredBaseUrl(baseUrl);"

        self.assertIn(absolute_url_check, source)
        self.assertIn(base_url_resolution, source)
        self.assertLess(source.index(absolute_url_check), source.index(base_url_resolution))


if __name__ == "__main__":
    unittest.main()
