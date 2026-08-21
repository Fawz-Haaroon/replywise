import re
from typing import Protocol

from domain_types import ContextAnalysis, EmailContext


class ContextAnalyzer(Protocol):
    def analyze_context(self, email_context: EmailContext) -> ContextAnalysis:
        ...


REQUEST_PATTERNS = (
    r"\bplease\s+(?P<request>[^.!?\n]+)",
    r"\bcan you\s+(?P<request>[^.!?\n]+)",
    r"\bcould you\s+(?P<request>[^.!?\n]+)",
    r"\bwould you\s+(?P<request>[^.!?\n]+)",
    r"\bplease\s+let me know\s+(?P<request>[^.!?\n]+)",
)
TEMPORAL_PATTERN = re.compile(
    r"\b(?:today|tomorrow|yesterday|monday|tuesday|wednesday|thursday|friday|"
    r"saturday|sunday|january|february|march|april|may|june|july|august|"
    r"september|october|november|december)\b"
    r"|\b\d{1,2}(?::\d{2})?\s?(?:a\.m\.|p\.m\.|am|pm)\b",
    re.IGNORECASE,
)


def build_rule_based_context_analysis(email_context: EmailContext) -> ContextAnalysis:
    email_text = email_context.original_email
    requests = _extract_requests(email_text)
    entities = _extract_key_entities(email_text)
    intent = _describe_intent(requests, email_text)
    return ContextAnalysis(
        intent=intent,
        key_entities=tuple(entities),
        detected_requests=tuple(requests),
    )


def merge_context_analyses(
    rule_analysis: ContextAnalysis,
    model_analysis: ContextAnalysis,
) -> ContextAnalysis:
    merged_entities = _preserve_order(rule_analysis.key_entities + model_analysis.key_entities)
    merged_requests = _preserve_order(
        rule_analysis.detected_requests + model_analysis.detected_requests
    )
    return ContextAnalysis(
        intent=model_analysis.intent or rule_analysis.intent,
        key_entities=tuple(merged_entities),
        detected_requests=tuple(merged_requests),
    )


def _extract_requests(email_text: str) -> list[str]:
    requests: list[str] = []
    for pattern in REQUEST_PATTERNS:
        for match in re.finditer(pattern, email_text, flags=re.IGNORECASE):
            request_text = _clean_phrase(match.group("request"))
            if request_text:
                requests.append(request_text)

    for sentence in _split_sentences(email_text):
        if "?" in sentence and sentence not in requests:
            requests.append(_clean_phrase(sentence))
    return _preserve_order(requests)


def _extract_key_entities(email_text: str) -> list[str]:
    temporal_entities = [match.group(0).strip() for match in TEMPORAL_PATTERN.finditer(email_text)]
    request_entities: list[str] = []
    for request in _extract_requests(email_text):
        request_entities.extend(_select_content_words(request))
    return _preserve_order(temporal_entities + request_entities)


def _describe_intent(requests: list[str], email_text: str) -> str:
    lowered_email = email_text.lower()
    if any(word in lowered_email for word in ("meet", "meeting", "call", "review")):
        if requests:
            return "Meeting or review coordination"
        return "Meeting context"
    if any(word in lowered_email for word in ("send", "share", "report", "document", "attachment")):
        return "Document or information request"
    if any(word in lowered_email for word in ("confirm", "confirmation", "agree")):
        return "Confirmation request"
    if requests:
        return "Action request"
    return "General correspondence"


def _split_sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+|\n+", text) if sentence.strip()]


def _clean_phrase(phrase: str) -> str:
    return re.sub(r"\s+", " ", phrase).strip(" .,:;")


def _select_content_words(phrase: str) -> list[str]:
    stop_words = {
        "a",
        "an",
        "and",
        "before",
        "can",
        "could",
        "for",
        "me",
        "please",
        "the",
        "to",
        "would",
        "you",
    }
    return [
        word
        for word in re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]*", phrase)
        if word.lower() not in stop_words and len(word) > 2
    ][:6]


def _preserve_order(values: tuple[str, ...] | list[str]) -> list[str]:
    seen: set[str] = set()
    ordered_values: list[str] = []
    for value in values:
        normalized_value = value.lower()
        if normalized_value in seen:
            continue
        seen.add(normalized_value)
        ordered_values.append(value)
    return ordered_values