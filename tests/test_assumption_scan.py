from domain.intake import create_email_context
from responsible_ai.assumption_scan import detect_invented_details
from domain_types import Tone, WarningCategory


def test_flags_time_not_present_in_source():
    context = create_email_context("Let's meet Friday.", Tone.PROFESSIONAL, None)
    warnings = detect_invented_details("Friday at 3 PM works for me.", context)
    assert any(warning.category == WarningCategory.INVENTED_DETAIL for warning in warnings)


def test_keeps_source_time_when_present():
    context = create_email_context(
        "Let's meet Friday at 3 PM.",
        Tone.PROFESSIONAL,
        None,
    )
    warnings = detect_invented_details("Friday at 3 PM works for me.", context)
    assert warnings == []


def test_flags_unverifiable_completion_claim():
    context = create_email_context("Have you completed the assignment?", Tone.PROFESSIONAL, None)
    warnings = detect_invented_details("I've completed it yesterday.", context)
    assert any(warning.category == WarningCategory.UNVERIFIABLE_CLAIM for warning in warnings)


def test_does_not_flag_plain_reply_without_temporal_detail():
    context = create_email_context("Thanks for the update.", Tone.PROFESSIONAL, None)
    warnings = detect_invented_details("Thanks for the update.", context)
    assert warnings == []


def test_does_not_treat_i_have_alone_as_completion_evidence():
    context = create_email_context("I have noted the discussion.", Tone.PROFESSIONAL, None)
    warnings = detect_invented_details("I've completed the review.", context)
    assert any(warning.category == WarningCategory.UNVERIFIABLE_CLAIM for warning in warnings)