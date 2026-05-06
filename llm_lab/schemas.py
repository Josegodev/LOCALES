"""Shared JSON contracts for the isolated LLM lab.

The lab intentionally uses plain dictionaries instead of runtime-specific
objects. That keeps this package replaceable and independent from NUCLEO.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

JSONDict = dict[str, Any]


FALLBACK_PROPOSAL: JSONDict = {
    "suggested_action": "none",
    "arguments": {},
    "confidence": 0.0,
    "meta": {
        "needs_clarification": True,
        "justification": "fallback: validation_failed",
        "fallback_reason": "validation_failed",
    },
}


FALLBACK_ANSWER: JSONDict = {
    "answer": "",
    "confidence": 0.0,
    "meta": {
        "needs_clarification": True,
        "justification": "fallback: validation_failed",
        "fallback_reason": "validation_failed",
    },
}


@dataclass(frozen=True)
class ValidationResult:
    """Result of converting raw model output into a safe JSON object."""

    validated_output: JSONDict
    fallback_used: bool
    fallback_reason: str | None = None


def proposal_fallback(reason: str = "validation_failed") -> JSONDict:
    fallback = copy.deepcopy(FALLBACK_PROPOSAL)
    fallback["meta"]["fallback_reason"] = reason
    fallback["meta"]["justification"] = f"fallback: {reason}"
    return fallback


def answer_fallback(reason: str = "validation_failed") -> JSONDict:
    fallback = copy.deepcopy(FALLBACK_ANSWER)
    fallback["meta"]["fallback_reason"] = reason
    fallback["meta"]["justification"] = f"fallback: {reason}"
    return fallback

