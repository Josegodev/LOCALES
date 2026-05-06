"""Model boundary for the experimental lab.

This adapter never executes actions. It only returns raw text that must be
validated by llm_lab.validator before the API sends a response.
"""

from __future__ import annotations

import json
import os
import socket
from dataclasses import dataclass
from typing import Any
from urllib import error, request

DEFAULT_TIMEOUT_SECONDS = 10
MOCK_ENDPOINT = "mock:in-process"
OLLAMA_DEFAULT_ENDPOINT = "http://127.0.0.1:11434/api/generate"
LMSTUDIO_DEFAULT_ENDPOINT = "http://127.0.0.1:1234/v1/chat/completions"


@dataclass(frozen=True)
class AdapterConfig:
    provider: str
    endpoint: str
    model_id: str


@dataclass(frozen=True)
class AdapterResult:
    provider: str
    endpoint: str
    model_id: str
    raw_output: str


class ModelAdapter:
    """Boundary between the lab and a mock or local model provider."""

    proposal_models = {"mock:proposal", "mock:invalid_json", "mock:invalid_schema", "mock:adapter_error"}
    answer_models = {"mock:answer", "mock:invalid_json", "mock:invalid_schema", "mock:adapter_error"}

    def __init__(self, timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS) -> None:
        self.timeout_seconds = timeout_seconds

    def generate_proposal(
        self,
        *,
        prompt: str,
        model_id: str | None,
        task: str,
        context: dict[str, Any],
    ) -> AdapterResult:
        config = self._resolve_config(kind="proposal", requested_model_id=model_id)
        try:
            raw_output = self._generate_proposal(config=config, prompt=prompt, task=task, context=context)
        except Exception as exc:
            raw_output = _adapter_error(exc)
        return AdapterResult(
            provider=config.provider,
            endpoint=config.endpoint,
            model_id=config.model_id,
            raw_output=raw_output,
        )

    def generate_answer(
        self,
        *,
        prompt: str,
        model_id: str | None,
        question: str,
        context: dict[str, Any],
    ) -> AdapterResult:
        config = self._resolve_config(kind="answer", requested_model_id=model_id)
        try:
            raw_output = self._generate_answer(config=config, prompt=prompt, question=question, context=context)
        except Exception as exc:
            raw_output = _adapter_error(exc)
        return AdapterResult(
            provider=config.provider,
            endpoint=config.endpoint,
            model_id=config.model_id,
            raw_output=raw_output,
        )

    def _generate_proposal(
        self,
        *,
        config: AdapterConfig,
        prompt: str,
        task: str,
        context: dict[str, Any],
    ) -> str:
        if config.provider != "mock":
            return self._call_local_provider(config=config, prompt=prompt)

        model_id = config.model_id
        if model_id not in self.proposal_models:
            raise ValueError(f"unsupported proposal model_id: {model_id}")
        if model_id == "mock:adapter_error":
            raise RuntimeError("simulated model adapter failure")
        if model_id == "mock:invalid_json":
            return "{not valid json"
        if model_id == "mock:invalid_schema":
            return json.dumps(
                {
                    "suggested_action": "draft_proposal",
                    "arguments": {},
                    "confidence": 2.0,
                    "meta": {
                        "needs_clarification": False,
                        "justification": "invalid confidence for validation test",
                    },
                },
                sort_keys=True,
            )

        proposed_action = "none" if _looks_like_execution(task) else "draft_proposal"
        needs_clarification = proposed_action == "none"
        return json.dumps(
            {
                "suggested_action": proposed_action,
                "arguments": {
                    "task": task,
                    "context_keys": sorted(context.keys()),
                    "proposal_only": True,
                },
                "confidence": 0.42,
                "meta": {
                    "needs_clarification": needs_clarification,
                    "justification": "mock adapter generated a proposal only; no action was executed",
                },
            },
            sort_keys=True,
        )

    def _generate_answer(
        self,
        *,
        config: AdapterConfig,
        prompt: str,
        question: str,
        context: dict[str, Any],
    ) -> str:
        if config.provider != "mock":
            return self._call_local_provider(config=config, prompt=prompt)

        model_id = config.model_id
        if model_id not in self.answer_models:
            raise ValueError(f"unsupported answer model_id: {model_id}")
        if model_id == "mock:adapter_error":
            raise RuntimeError("simulated model adapter failure")
        if model_id == "mock:invalid_json":
            return "not-json"
        if model_id == "mock:invalid_schema":
            return json.dumps(
                {
                    "answer": 123,
                    "confidence": 0.5,
                    "meta": {
                        "needs_clarification": False,
                        "justification": "invalid answer type for validation test",
                    },
                },
                sort_keys=True,
            )

        return json.dumps(
            {
                "answer": f"Mock answer for: {question}",
                "confidence": 0.4,
                "meta": {
                    "needs_clarification": False,
                    "justification": "mock adapter generated text only; no action was executed",
                },
            },
            sort_keys=True,
        )

    def _resolve_config(self, *, kind: str, requested_model_id: str | None) -> AdapterConfig:
        if requested_model_id and requested_model_id.startswith("mock:"):
            return AdapterConfig(
                provider="mock",
                endpoint=MOCK_ENDPOINT,
                model_id=requested_model_id,
            )

        provider = os.getenv("LLM_LAB_PROVIDER", "mock").strip().lower() or "mock"
        if provider in {"lm-studio", "lm_studio"}:
            provider = "lmstudio"

        if provider == "mock":
            default_model_id = "mock:proposal" if kind == "proposal" else "mock:answer"
            return AdapterConfig(
                provider="mock",
                endpoint=MOCK_ENDPOINT,
                model_id=requested_model_id or default_model_id,
            )

        if provider == "ollama":
            return AdapterConfig(
                provider=provider,
                endpoint=os.getenv("LLM_LAB_ENDPOINT", OLLAMA_DEFAULT_ENDPOINT).strip() or OLLAMA_DEFAULT_ENDPOINT,
                model_id=os.getenv("LLM_LAB_MODEL", requested_model_id or "").strip(),
            )

        if provider == "lmstudio":
            return AdapterConfig(
                provider=provider,
                endpoint=os.getenv("LLM_LAB_ENDPOINT", LMSTUDIO_DEFAULT_ENDPOINT).strip() or LMSTUDIO_DEFAULT_ENDPOINT,
                model_id=os.getenv("LLM_LAB_MODEL", requested_model_id or "").strip(),
            )

        return AdapterConfig(
            provider=provider,
            endpoint=os.getenv("LLM_LAB_ENDPOINT", "").strip(),
            model_id=os.getenv("LLM_LAB_MODEL", requested_model_id or "").strip(),
        )

    def _call_local_provider(self, *, config: AdapterConfig, prompt: str) -> str:
        if not config.model_id:
            raise ValueError(f"LLM_LAB_MODEL is required when provider={config.provider}")

        if config.provider == "ollama":
            return self._call_ollama(config=config, prompt=prompt)
        if config.provider == "lmstudio":
            return self._call_lmstudio(config=config, prompt=prompt)

        raise ValueError(f"unsupported provider: {config.provider}")

    def _call_ollama(self, *, config: AdapterConfig, prompt: str) -> str:
        response = self._post_json(
            endpoint=config.endpoint,
            payload={
                "model": config.model_id,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0},
            },
        )
        raw_output = response.get("response")
        if not isinstance(raw_output, str):
            raise ValueError("ollama response missing string field: response")
        return raw_output

    def _call_lmstudio(self, *, config: AdapterConfig, prompt: str) -> str:
        response = self._post_json(
            endpoint=config.endpoint,
            payload={
                "model": config.model_id,
                "messages": [
                    {"role": "system", "content": "Return JSON only. Never execute actions."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0,
                "stream": False,
                "response_format": {"type": "json_object"},
            },
        )
        try:
            raw_output = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("lmstudio response missing choices[0].message.content") from exc
        if not isinstance(raw_output, str):
            raise ValueError("lmstudio message content must be a string")
        return raw_output

    def _post_json(self, *, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not endpoint:
            raise ValueError("LLM_LAB_ENDPOINT must be set for this provider")

        http_request = request.Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"content-type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=self.timeout_seconds) as response:
                body = response.read().decode("utf-8")
        except error.HTTPError as exc:
            raise ConnectionError(f"provider HTTP error: {exc.code}") from exc
        except (TimeoutError, socket.timeout) as exc:
            raise TimeoutError(f"provider timeout after {self.timeout_seconds} seconds") from exc
        except error.URLError as exc:
            if isinstance(exc.reason, (TimeoutError, socket.timeout)):
                raise TimeoutError(f"provider timeout after {self.timeout_seconds} seconds") from exc
            raise ConnectionError(f"provider request failed: {exc.reason}") from exc

        try:
            parsed = json.loads(body)
        except json.JSONDecodeError as exc:
            raise ValueError("provider response was not valid JSON") from exc
        if not isinstance(parsed, dict):
            raise ValueError("provider response JSON must be an object")
        return parsed


def _looks_like_execution(text: str) -> bool:
    lowered = text.lower()
    execution_terms = ("run ", "execute ", "delete ", "write ", "modify ", "deploy ")
    return any(term in lowered for term in execution_terms)


def _adapter_error(exc: Exception) -> str:
    return json.dumps(
        {
            "adapter_error": str(exc),
            "error_type": type(exc).__name__,
        },
        sort_keys=True,
    )
