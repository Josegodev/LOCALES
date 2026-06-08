import os
import unittest

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")

from app.main import (
    _extract_anchor_terms,
    _extract_chunk_response_data,
    _no_evidence_answer,
    _should_force_no_evidence,
)


class NoEvidenceAnswerTests(unittest.TestCase):
    def test_contains_marker(self):
        answer = _no_evidence_answer()
        self.assertIn("NO_EVIDENCE_FOR_ANSWER", answer)


class ExtractAnchorTermsTests(unittest.TestCase):
    def test_extracts_terms_with_digit(self):
        terms = _extract_anchor_terms("configure rds-proxy-12345 now")
        self.assertIn("rds-proxy-12345", terms)

    def test_extracts_terms_with_underscore(self):
        terms = _extract_anchor_terms("run my_custom_script for deploy")
        self.assertIn("my_custom_script", terms)

    def test_extracts_terms_with_hyphen(self):
        terms = _extract_anchor_terms("use docker-compose for setup")
        self.assertIn("docker-compose", terms)

    def test_ignores_short_terms(self):
        terms = _extract_anchor_terms("a b cd efgh abc-d")
        self.assertEqual(terms, [])

    def test_empty_query(self):
        terms = _extract_anchor_terms("")
        self.assertEqual(terms, [])


class ShouldForceNoEvidenceTests(unittest.TestCase):
    def test_no_anchor_terms_returns_false(self):
        self.assertFalse(_should_force_no_evidence("hello world", []))

    def test_anchor_in_chunks_returns_false(self):
        chunks = [{"text": "This covers docker-compose in production"}]
        self.assertFalse(_should_force_no_evidence("docker-compose setup", chunks))

    def test_anchor_not_in_chunks_returns_true(self):
        chunks = [{"text": "This is about kubernetes"}]
        self.assertTrue(_should_force_no_evidence("docker-compose setup", chunks))

    def test_non_dict_chunks_skipped(self):
        chunks = ["not a dict", 42]
        self.assertTrue(_should_force_no_evidence("docker-compose config", chunks))

    def test_empty_chunks_with_anchors_returns_true(self):
        self.assertTrue(_should_force_no_evidence("rds-proxy-12345", []))


class ExtractChunkResponseDataTests(unittest.TestCase):
    def test_extracts_texts_and_ids(self):
        chunks = [
            {"text": "chunk one", "id": 1},
            {"text": "chunk two", "id": 2},
        ]
        texts, ids = _extract_chunk_response_data(chunks)
        self.assertEqual(texts, ["chunk one", "chunk two"])
        self.assertEqual(ids, [1, 2])

    def test_string_id_converted_to_int(self):
        chunks = [{"text": "chunk", "id": "42"}]
        texts, ids = _extract_chunk_response_data(chunks)
        self.assertEqual(ids, [42])

    def test_non_dict_skipped(self):
        chunks = [{"text": "valid", "id": 1}, "not a dict", 42]
        texts, ids = _extract_chunk_response_data(chunks)
        self.assertEqual(len(texts), 1)
        self.assertEqual(len(ids), 1)

    def test_empty_text_skipped(self):
        chunks = [{"text": "", "id": 1}, {"text": "  ", "id": 2}]
        texts, ids = _extract_chunk_response_data(chunks)
        self.assertEqual(texts, [])

    def test_non_numeric_string_id_skipped(self):
        chunks = [{"text": "valid", "id": "not-a-number"}]
        _, ids = _extract_chunk_response_data(chunks)
        self.assertEqual(ids, [])

    def test_empty_list(self):
        texts, ids = _extract_chunk_response_data([])
        self.assertEqual(texts, [])
        self.assertEqual(ids, [])


if __name__ == "__main__":
    unittest.main()
