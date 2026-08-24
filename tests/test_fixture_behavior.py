import json
from pathlib import Path

import pytest

from domain.intake import create_email_context
from domain_types import Tone, WarningCategory
from responsible_ai.assumption_scan import detect_invented_details
from responsible_ai.commitment_scan import detect_unsupported_commitments
from responsible_ai.pii_scan import scan_for_sensitive_information


FIXTURE_PATH = Path(__file__).with_name("test_cases.json")


def _warning_categories(case: dict[str, str]) -> set[WarningCategory]:
    context = create_email_context(case["email"], Tone.PROFESSIONAL, None)
    expected = case["expected"]
    if expected == "low":
        draft = "Thanks for your note."
    elif expected == "sensitive_info":
        draft = case["email"]
    elif expected == "unsupported_commitment":
        draft = "I will send the requested item."
    elif expected == "unverifiable_claim":
        draft = "I've completed the assignment."
    else:
        draft = "The meeting is confirmed for Monday at 10 AM."

    warnings = scan_for_sensitive_information(draft)
    warnings.extend(detect_unsupported_commitments(draft, context))
    warnings.extend(detect_invented_details(draft, context))
    return {warning.category for warning in warnings}


CASES = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["category"] + ":" + case["email"][:24])
def test_every_fixture_case_executes_against_the_responsible_ai_scanners(case):
    expected = case["expected"]
    categories = _warning_categories(case)
    if expected == "low":
        assert categories == set()
    else:
        assert WarningCategory(expected) in categories