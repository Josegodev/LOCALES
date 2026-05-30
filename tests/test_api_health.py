import unittest

from fastapi.testclient import TestClient

from app.main import app


class ApiHealthTests(unittest.TestCase):
    def test_health_returns_ok_contract(self):
        response = TestClient(app).get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})


if __name__ == "__main__":
    unittest.main()
