from domain.intake import create_email_context
from responsible_ai.commitment_scan import detect_unsupported_commitments
from domain_types import Tone, WarningCategory


def test_flags_request_converted_to_unconfirmed_promise():
    context = create_email_context(
        "Could you send me the report before the meeting?",
        Tone.PROFESSIONAL,
        None,
    )
    warnings = detect_unsupported_commitments(
        "I'll send the report before the meeting.",
        context,
    )
    assert len(warnings) == 1
    assert warnings[0].category == WarningCategory.UNSUPPORTED_COMMITMENT


def test_does_not_flag_explicit_user_instruction_to_send():
    context = create_email_context(
        "Could you send me the report before the meeting?",
        Tone.PROFESSIONAL,
        "Agree to send the report before the meeting.",
    )
    warnings = detect_unsupported_commitments(
        "I'll send the report before the meeting.",
        context,
    )
    assert warnings == []


def test_flags_false_completion_claim():
    context = create_email_context("Have you completed the assignment?", Tone.PROFESSIONAL, None)
    warnings = detect_unsupported_commitments("I've completed the assignment.", context)
    assert any(warning.category == WarningCategory.UNSUPPORTED_COMMITMENT for warning in warnings)


def test_keeps_grounded_meeting_confirmation():
    context = create_email_context(
        "Can we move tomorrow's review to Friday at 3 PM?",
        Tone.PROFESSIONAL,
        "Confirm Friday at 3 PM works.",
    )
    warnings = detect_unsupported_commitments("Friday at 3 PM works for me.", context)
    assert warnings == []


def test_flags_invented_recipient_even_when_action_words_overlap():
    context = create_email_context("Please send the report to the finance team.", Tone.PROFESSIONAL, "Agree to send the report.")
    warnings = detect_unsupported_commitments(
        "I will send the report to Nina at Acme.",
        context,
    )
    assert any(warning.category == WarningCategory.UNSUPPORTED_COMMITMENT for warning in warnings)


def test_provider_grounding_checks_are_bounded():
    class CountingChecker:
        calls = 0

        def check_grounding(self, candidate_sentence, email_context):
            self.calls += 1
            from domain_types import GroundingDecision
            return GroundingDecision(False, "provider did not confirm the detail")

    checker = CountingChecker()
    context = create_email_context("Please review the report.", Tone.PROFESSIONAL, "Agree to review the report.")
    draft = " ".join(f"I will review the report for item {index}." for index in range(6))
    warnings = detect_unsupported_commitments(draft, context, checker)
    assert len(warnings) == 6
    assert checker.calls <= 3