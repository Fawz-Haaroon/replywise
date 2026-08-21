import json
from typing import Any

from domain_types import ContextAnalysis, GroundingDecision


def parse_context_analysis(response_text: str) -> ContextAnalysis:
    payload = _parse_json_object(response_text, "context analysis")
    intent = _require_string(payload, "intent", "context analysis")
    key_entities = _require_string_list(payload, "key_entities", "context analysis")
    detected_requests = _require_string_list(payload, "detected_requests", "context analysis")
    return ContextAnalysis(
        intent=intent,
        key_entities=tuple(key_entities),
        detected_requests=tuple(detected_requests),
    )


def parse_grounding_decision(response_text: str) -> GroundingDecision:
    payload = _parse_json_object(response_text, "grounding check")
    grounded = payload.get("grounded")
    reason = payload.get("reason")
    if not isinstance(grounded, bool):
        raise RuntimeError(
            "LLM grounding check failed: expected boolean field 'grounded', "
            f"received {grounded!r}."
        )
    if not isinstance(reason, str) or not reason.strip():
        raise RuntimeError(
            "LLM grounding check failed: expected non-empty string field 'reason', "
            f"received {reason!r}."
        )
    return GroundingDecision(is_grounded=grounded, reason=reason.strip())


def _parse_json_object(response_text: str, operation_name: str) -> dict[str, Any]:
    candidate = response_text.strip()
    if candidate.startswith("```"):
        candidate = candidate.removeprefix("```json").removesuffix("```").strip()
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"LLM {operation_name} failed: expected strict JSON but received "
            f"{response_text[:200]!r}."
        ) from error
    if not isinstance(payload, dict):
        raise RuntimeError(
            f"LLM {operation_name} failed: expected a JSON object, received "
            f"{type(payload).__name__}."
        )
    return payload


def _require_string(payload: dict[str, Any], key: str, operation_name: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise RuntimeError(
            f"LLM {operation_name} failed: field '{key}' must be a string, received {value!r}."
        )
    return value.strip()


def _require_string_list(
    payload: dict[str, Any],
    key: str,
    operation_name: str,
) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise RuntimeError(
            f"LLM {operation_name} failed: field '{key}' must be a list of strings, "
            f"received {value!r}."
        )
    return [item.strip() for item in value if item.strip()]