from __future__ import annotations

import sys
from pathlib import Path
from time import perf_counter

from pydantic import BaseModel, ConfigDict
from openai import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    NotFoundError,
    OpenAI,
    OpenAIError,
    RateLimitError,
)

# Allows `python scripts/probe_openai_models.py` to import top-level packages.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import settings

MODEL_CANDIDATES: tuple[str, ...] = (
    "gpt-5.5",
    "gpt-5.5-pro",
    "gpt-5.4",
    "gpt-5.4-mini",
    "gpt-5.4-nano",
    "gpt-5",
    "gpt-5-mini",
    "gpt-5-nano",
    "gpt-4.1",
    "gpt-4.1-mini",
    "gpt-4o",
    "gpt-4o-mini",
)
PROBE_PROMPT = "Responde solo: OK"
PROBE_TIMEOUT_SECONDS = 30.0
PROBE_MAX_OUTPUT_TOKENS = 16


class ProbeResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model: str
    status: str
    error_type: str | None = None
    latency_ms: int | None = None


def _require_api_key() -> str | None:
    return settings.openai_api_key


def _build_client(api_key: str) -> OpenAI:
    return OpenAI(
        api_key=api_key,
        timeout=PROBE_TIMEOUT_SECONDS,
        max_retries=0,
    )


def _error_type_from_exception(exc: Exception) -> str:
    if isinstance(exc, APITimeoutError):
        return "timeout"
    if isinstance(exc, APIConnectionError):
        return "connection_error"
    if isinstance(exc, AuthenticationError):
        return "authentication_error"
    if isinstance(exc, NotFoundError):
        return "model_not_found"
    if isinstance(exc, RateLimitError):
        return "rate_limited"

    if isinstance(exc, APIStatusError):
        status_code = getattr(exc, "status_code", None)
        if status_code == 401:
            return "authentication_error"
        if status_code == 404:
            return "model_not_found"
        if status_code == 429:
            return "rate_limited"

    if isinstance(exc, (APIError, OpenAIError)):
        return "generic_openai_error"

    return "generic_openai_error"


def _probe_model(client: OpenAI, model: str) -> tuple[ProbeResult, str | None]:
    started_at = perf_counter()

    try:
        response = client.responses.create(
            model=model,
            input=PROBE_PROMPT,
            max_output_tokens=PROBE_MAX_OUTPUT_TOKENS,
        )
        response_text = " ".join((response.output_text or "").split())
        latency_ms = int((perf_counter() - started_at) * 1000)

        if not response_text:
            return (
                ProbeResult(
                    model=model,
                    status="fail",
                    error_type="generic_openai_error",
                    latency_ms=latency_ms,
                ),
                None,
            )

        return (
            ProbeResult(
                model=model,
                status="ok",
                error_type=None,
                latency_ms=latency_ms,
            ),
            response_text,
        )
    except Exception as exc:
        latency_ms = int((perf_counter() - started_at) * 1000)
        return (
            ProbeResult(
                model=model,
                status="fail",
                error_type=_error_type_from_exception(exc),
                latency_ms=latency_ms,
            ),
            None,
        )


def main() -> int:
    api_key = _require_api_key()
    if not api_key:
        print("[FAIL] error_type=missing_api_key")
        print("BEST_AVAILABLE_MODEL=")
        return 1

    client = _build_client(api_key)

    for model in MODEL_CANDIDATES:
        print(f"[PROBE] model={model}")
        result, response_text = _probe_model(client, model)

        if result.status == "ok":
            print(f"[OK] model={result.model}")
            print(f"response={response_text}")
            print(f"BEST_AVAILABLE_MODEL={result.model}")
            return 0

        print(f"[FAIL] error_type={result.error_type}")

    print("BEST_AVAILABLE_MODEL=")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
