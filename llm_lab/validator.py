"""Validation for raw model outputs.

Every model response enters the system as untrusted text. The validator is the
only place that turns that text into a safe JSON contract.
"""

from __future__ import annotations

import json
from typing import Any

from .schemas import JSONDict, ValidationResult, answer_fallback, proposal_fallback


def validate_proposal_output(raw_output: str) -> ValidationResult:
    data = _parse_json_object(raw_output)
    if data is None or not _is_valid_proposal(data):
        return ValidationResult(
            validated_output=proposal_fallback("validation_failed"),
            fallback_used=True,
            fallback_reason="validation_failed",
        )

    return ValidationResult(validated_output=data, fallback_used=False)


def validate_answer_output(raw_output: str) -> ValidationResult:
    data = _parse_json_object(raw_output)
    if data is None or not _is_valid_answer(data):
        return ValidationResult(
            validated_output=answer_fallback("validation_failed"),
            fallback_used=True,
            fallback_reason="validation_failed",
        )

    return ValidationResult(validated_output=data, fallback_used=False)


def _parse_json_object(raw_output: str) -> JSONDict | None:
    try:
        data = json.loads(raw_output)
    except (TypeError, json.JSONDecodeError):
        return None

    if not isinstance(data, dict):
        return None
    return data


def _is_valid_proposal(data: dict[str, Any]) -> bool:
    if not isinstance(data.get("suggested_action"), str):
        return False
    if not isinstance(data.get("arguments"), dict):
        return False
    if not _is_confidence(data.get("confidence")):
        return False
    return _is_valid_meta(data.get("meta"))


def _is_valid_answer(data: dict[str, Any]) -> bool:
    if not isinstance(data.get("answer"), str):
        return False
    if not _is_confidence(data.get("confidence")):
        return False
    return _is_valid_meta(data.get("meta"))


def _is_valid_meta(meta: Any) -> bool:
    if not isinstance(meta, dict):
        return False
    if not isinstance(meta.get("needs_clarification"), bool):
        return False
    if not isinstance(meta.get("justification"), str):
        return False
    fallback_reason = meta.get("fallback_reason")
    if fallback_reason is not None and not isinstance(fallback_reason, str):
        return False
    return True


def _is_confidence(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return 0.0 <= float(value) <= 1.0

