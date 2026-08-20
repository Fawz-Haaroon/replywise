from collections.abc import Mapping
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests


def post_json(
    url: str,
    payload: Mapping[str, Any],
    headers: Mapping[str, str],
    timeout_seconds: float,
    operation_name: str,
) -> dict[str, Any]:
    try:
        response = requests.post(
            url,
            json=dict(payload),
            headers=dict(headers),
            timeout=timeout_seconds,
        )
    except requests.RequestException as error:
        raise RuntimeError(
            f"{operation_name} failed before a response arrived: "
            f"{_redact_sensitive_text(str(error), url, headers)}. "
            f"Check network access and the provider endpoint '{_safe_endpoint(url)}'."
        ) from error

    if response.status_code >= 400:
        raise RuntimeError(
            f"{operation_name} failed: provider returned HTTP {response.status_code} "
            f"at endpoint '{_safe_endpoint(url)}'. "
            "Check model access, quota, and credentials."
        )
    try:
        payload = response.json()
    except ValueError as error:
        raise RuntimeError(
            f"{operation_name} failed: provider returned non-JSON response "
            f"at endpoint '{_safe_endpoint(url)}'."
        ) from error
    if not isinstance(payload, dict):
        raise RuntimeError(
            f"{operation_name} failed: provider returned {type(payload).__name__}, expected JSON object."
        )
    return payload


def _safe_endpoint(url: str) -> str:
    parts = urlsplit(url)
    if not parts.query:
        return url
    redacted_query = urlencode(
        [(key, "<redacted>") for key, _value in parse_qsl(parts.query, keep_blank_values=True)]
    )
    return urlunsplit((parts.scheme, parts.netloc, parts.path, redacted_query, parts.fragment))


def _redact_sensitive_text(
    text: str,
    url: str,
    headers: Mapping[str, str] | None = None,
) -> str:
    safe_url = _safe_endpoint(url)
    redacted = text.replace(url, safe_url)
    for header_value in (headers or {}).values():
        if header_value:
            redacted = redacted.replace(header_value, "<redacted>")
            for token in header_value.split():
                if len(token) >= 8:
                    redacted = redacted.replace(token, "<redacted>")
    return redacted