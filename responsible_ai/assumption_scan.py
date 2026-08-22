import re

from domain_types import EmailContext, Warning, WarningCategory


TEMPORAL_DETAIL_PATTERN = re.compile(
    r"\b(?:today|tomorrow|yesterday|monday|tuesday|wednesday|thursday|friday|"
    r"saturday|sunday|january|february|march|april|may|june|july|august|"
    r"september|october|november|december)\b"
    r"|\b\d{1,2}(?::\d{2})?\s?(?:a\.m\.|p\.m\.|am|pm)\b"
    r"|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    re.IGNORECASE,
)
COMPLETION_CLAIM_PATTERN = re.compile(
    r"(?P<sentence>[^.!?\n]*(?:I've|I have|I completed|I finished|I sent|"
    r"I prepared)[^.!?\n]*[.!?]?)",
    re.IGNORECASE,
)
SOURCE_COMPLETION_PATTERN = re.compile(
    r"\b(?:i have|i've|i already)\s+"
    r"(?:completed|finished|sent|prepared|delivered)\b",
    re.IGNORECASE,
)


def detect_invented_details(
    draft_text: str,
    email_context: EmailContext,
) -> list[Warning]:
    source_text = f"{email_context.original_email} {email_context.instruction or ''}"
    source_temporal_details = {
        _normalize_detail(match.group(0))
        for match in TEMPORAL_DETAIL_PATTERN.finditer(source_text)
    }
    warnings: list[Warning] = []
    for match in TEMPORAL_DETAIL_PATTERN.finditer(draft_text):
        detail = match.group(0)
        if _normalize_detail(detail) in source_temporal_details:
            continue
        warnings.append(
            Warning(
                category=WarningCategory.INVENTED_DETAIL,
                triggering_phrase=detail,
                explanation=(
                    f"The draft introduces '{detail}', but that date or time does not "
                    "appear in the original email or instruction."
                ),
            )
        )

    for match in COMPLETION_CLAIM_PATTERN.finditer(draft_text):
        sentence = re.sub(r"\s+", " ", match.group("sentence")).strip()
        if not _source_confirms_completion(source_text):
            warnings.append(
                Warning(
                    category=WarningCategory.UNVERIFIABLE_CLAIM,
                    triggering_phrase=sentence,
                    explanation=(
                        "The draft claims an action is complete, but the source and "
                        "instruction do not confirm that it happened."
                    ),
                )
            )
    return _deduplicate_warnings(warnings)


def _source_confirms_completion(source_text: str) -> bool:
    return bool(SOURCE_COMPLETION_PATTERN.search(source_text))


def _normalize_detail(detail: str) -> str:
    return re.sub(r"\s+", " ", detail.lower().replace(".", "")).strip()


def _deduplicate_warnings(warnings: list[Warning]) -> list[Warning]:
    seen: set[tuple[WarningCategory, str]] = set()
    unique_warnings: list[Warning] = []
    for warning in warnings:
        identity = (warning.category, warning.triggering_phrase.lower())
        if identity in seen:
            continue
        seen.add(identity)
        unique_warnings.append(warning)
    return unique_warnings