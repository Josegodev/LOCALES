import unittest

import requests

from app.adapters import telegram_api
import scripts.run_telegram as run_telegram


class FakeTelegramResponse:
    def __init__(
        self,
        *,
        status_code: int,
        text: str = "",
        url: str = "https://api.telegram.org/botTOKEN/getUpdates",
        headers: dict | None = None,
        payload: dict | None = None,
    ):
        self.status_code = status_code
        self.text = text
        self.url = url
        self.headers = headers or {}
        self._payload = payload

    def json(self):
        if self._payload is None:
            raise ValueError("json unavailable")
        return self._payload


def build_http_error(response: FakeTelegramResponse) -> requests.exceptions.HTTPError:
    return requests.exceptions.HTTPError("telegram http error", response=response)


class TelegramPollingTests(unittest.TestCase):
    def test_classify_http_error_invalid_token(self):
        response = FakeTelegramResponse(
            status_code=401,
            text='{"ok":false,"description":"Unauthorized"}',
            url="https://api.telegram.org/bot1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcd/sendMessage",
        )

        classified = telegram_api.classify_telegram_http_error(
            build_http_error(response),
            endpoint="getUpdates",
        )

        self.assertEqual(classified["code"], "invalid_token")
        self.assertEqual(classified["status_code"], 401)
        self.assertEqual(classified["endpoint"], "getUpdates")
        self.assertEqual(classified["url"], "https://api.telegram.org/bot<redacted>/sendMessage")

    def test_classify_http_error_polling_conflict(self):
        response = FakeTelegramResponse(
            status_code=409,
            text='{"ok":false,"description":"Conflict: terminated by other getUpdates request"}',
        )

        classified = telegram_api.classify_telegram_http_error(
            build_http_error(response),
            endpoint="getUpdates",
        )

        self.assertEqual(classified["code"], "polling_conflict")
        self.assertEqual(classified["reason"], "terminated_by_other_getUpdates")
        self.assertEqual(
            classified["message"],
            "Ya hay otro proceso usando este bot token. Cierra procesos duplicados.",
        )

    def test_classify_http_error_rate_limited_extracts_retry_after(self):
        response = FakeTelegramResponse(
            status_code=429,
            text='{"ok":false,"error_code":429,"description":"Too Many Requests","parameters":{"retry_after":9}}',
            payload={
                "ok": False,
                "error_code": 429,
                "description": "Too Many Requests",
                "parameters": {"retry_after": 9},
            },
        )

        classified = telegram_api.classify_telegram_http_error(
            build_http_error(response),
            endpoint="getUpdates",
        )

        self.assertEqual(classified["code"], "rate_limited")
        self.assertEqual(classified["retry_after"], 9)

    def test_classify_http_error_server_error(self):
        response = FakeTelegramResponse(
            status_code=502,
            text="Bad Gateway",
        )

        classified = telegram_api.classify_telegram_http_error(
            build_http_error(response),
            endpoint="getUpdates",
        )

        self.assertEqual(classified["code"], "telegram_server_error")
        self.assertEqual(classified["status_code"], 502)

    def test_classify_request_exception_network_error(self):
        classified = telegram_api.classify_telegram_request_error(
            requests.exceptions.ConnectionError("sin red"),
            endpoint="getUpdates",
        )

        self.assertEqual(classified["code"], "network_error")
        self.assertEqual(classified["reason"], "connection_error")

    def test_http_error_body_is_limited_to_500_chars(self):
        response = FakeTelegramResponse(
            status_code=500,
            text="x" * 700,
        )

        classified = telegram_api.classify_telegram_http_error(
            build_http_error(response),
            endpoint="getUpdates",
        )

        self.assertEqual(len(classified["response_body"]), 500)

    def test_polling_backoff_respects_retry_after(self):
        self.assertEqual(
            run_telegram._polling_backoff_seconds(2, retry_after=9),
            9,
        )
        self.assertEqual(
            run_telegram._polling_backoff_seconds(4, retry_after=None),
            8,
        )

    def test_endpoint_is_inferred_from_exception_url(self):
        response = FakeTelegramResponse(
            status_code=429,
            url="https://api.telegram.org/botTOKEN/sendMessage",
        )

        endpoint = run_telegram._telegram_endpoint_from_exception(
            build_http_error(response)
        )

        self.assertEqual(endpoint, "sendMessage")


if __name__ == "__main__":
    unittest.main()
