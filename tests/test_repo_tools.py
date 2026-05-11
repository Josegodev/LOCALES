import tempfile
import unittest
from pathlib import Path

from app.services import repo_tools


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


class RepoToolsTests(unittest.TestCase):
    def test_route_single_line_uses_read_file_range(self):
        route = repo_tools.route_repo_question("línea 14 de config.py")

        self.assertEqual(route["repo_tool"], "read_file_range")
        self.assertEqual(route["requested_file"], "config.py")
        self.assertEqual(route["start_line"], 14)
        self.assertEqual(route["end_line"], 14)

    def test_route_line_range_uses_read_file_range(self):
        route = repo_tools.route_repo_question("líneas 10-20 de app/config.py")

        self.assertEqual(route["repo_tool"], "read_file_range")
        self.assertEqual(route["requested_file"], "app/config.py")
        self.assertEqual(route["start_line"], 10)
        self.assertEqual(route["end_line"], 20)

    def test_route_search_uses_search_text(self):
        route = repo_tools.route_repo_question("busca REPO_ANALYZER_ENABLED")

        self.assertEqual(route["repo_tool"], "search_text")
        self.assertEqual(route["query"], "REPO_ANALYZER_ENABLED")

    def test_route_find_file_uses_find_file(self):
        route = repo_tools.route_repo_question("dónde está config.py")

        self.assertEqual(route["repo_tool"], "find_file")
        self.assertEqual(route["requested_file"], "config.py")

    def test_route_repo_tree_uses_repo_tree(self):
        route = repo_tools.route_repo_question("estructura del repo")

        self.assertEqual(route["repo_tool"], "repo_tree")

    def test_route_open_question_uses_llm_fallback(self):
        route = repo_tools.route_repo_question("Dónde se calculan los tokens?")

        self.assertEqual(route["repo_tool"], "ask_repo_llm")

    def test_read_file_range_does_not_call_llm(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            write_file(
                Path(tmpdir) / "app" / "config.py",
                "\n".join(f"linea {index}" for index in range(1, 31)) + "\n",
            )

            result = repo_tools.run_repo_tool_question(
                tmpdir,
                "línea 14 de config.py",
                "granite4.1:8b",
                0.2,
                ask_repo_llm_fn=lambda *args, **kwargs: self.fail("LLM fallback should not be called"),
            )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["repo_tool"], "read_file_range")
        self.assertEqual(result["resolved_path"], "app/config.py")
        self.assertEqual(result["lines"], ["14: linea 14"])

    def test_find_file_returns_ambiguous_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            write_file(Path(tmpdir) / "app" / "config.py", "a\n")
            write_file(Path(tmpdir) / "tests" / "config.py", "b\n")

            result = repo_tools.find_file(tmpdir, "config.py")

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"]["error_code"], "AMBIGUOUS_FILE_MATCH")

    def test_find_file_returns_not_found(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            write_file(Path(tmpdir) / "app" / "config.py", "a\n")

            result = repo_tools.find_file(tmpdir, "missing.py")

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"]["error_code"], "FILE_NOT_FOUND")

    def test_read_file_range_returns_line_out_of_range(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            write_file(Path(tmpdir) / "app" / "config.py", "uno\ndos\n")

            result = repo_tools.read_file_range(tmpdir, "config.py", 10, 10)

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"]["error_code"], "LINE_OUT_OF_RANGE")


if __name__ == "__main__":
    unittest.main()
