import re

from domain_types import Warning, WarningCategory


EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
SSN_PATTERN = re.compile(r"(?<!\d)\d{3}[- ]\d{2}[- ]\d{4}(?!\d)")
PAN_PATTERN = re.compile(r"\b[A-Z]{5}\d{4}[A-Z]\b", re.IGNORECASE)
AADHAAR_PATTERN = re.compile(r"(?<!\d)\d{4}(?:[\s-]?\d{4}){2}(?!\d)")
INDIAN_PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)"
)
ACCOUNT_PATTERN = re.compile(
    r"\b(?:account|card|iban|routing)\b\D{0,20}((?:\d[\s-]?){9,18}\d)\b",
    re.IGNORECASE,
)
OTP_PATTERN = re.compile(
    r"\b(?:password|passcode|otp|pin)\b\D{0,12}([A-Z0-9]{4,12})\b",
    re.IGNORECASE,
)
ADDRESS_PATTERN = re.compile(
    r"\b\d{1,5}\s+[A-Za-z][A-Za-z0-9 .'-]{1,30}\s+"
    r"(?:road|rd|street|st|avenue|ave|lane|ln)\b",
    re.IGNORECASE,
)


def scan_for_sensitive_information(draft_text: str) -> list[Warning]:
    warnings: list[Warning] = []
    warnings.extend(_warnings_for_pattern(draft_text, EMAIL_PATTERN, "Email address"))
    warnings.extend(_warnings_for_pattern(draft_text, SSN_PATTERN, "Social Security number"))
    warnings.extend(_warnings_for_pattern(draft_text, INDIAN_PHONE_PATTERN, "Phone number"))
    warnings.extend(_warnings_for_pattern(draft_text, PAN_PATTERN, "Government ID"))
    warnings.extend(_warnings_for_pattern(draft_text, AADHAAR_PATTERN, "Government ID"))
    warnings.extend(_warnings_for_pattern(draft_text, ACCOUNT_PATTERN, "Financial identifier"))
    warnings.extend(_warnings_for_pattern(draft_text, OTP_PATTERN, "Password or one-time code"))
    warnings.extend(_warnings_for_pattern(draft_text, ADDRESS_PATTERN, "Physical address"))
    return _deduplicate_warnings(warnings)


def _warnings_for_pattern(
    draft_text: str,
    pattern: re.Pattern[str],
    category_name: str,
) -> list[Warning]:
    return [
        Warning(
            category=WarningCategory.SENSITIVE_INFO,
            triggering_phrase=match.group(0),
            explanation=(
                f"{category_name} appears in the draft. Confirm that repeating it is "
                "necessary before using this response."
            ),
        )
        for match in pattern.finditer(draft_text)
    ]


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