from domain.intake import create_email_context
from domain_types import Tone
from llm.providers.offline_provider import OfflinePreviewProvider


def test_offline_grounding_rejects_invented_name_date_and_amount():
    provider = OfflinePreviewProvider()
    context = create_email_context(
        "Please send the report to the finance team on Friday.",
        Tone.PROFESSIONAL,
        "Agree to send the report.",
    )
    decision = provider.check_grounding(
        "I will send the report to Nina on Monday for $500.",
        context,
    )
    assert decision.is_grounded is False


def test_offline_grounding_accepts_details_present_in_source():
    provider = OfflinePreviewProvider()
    context = create_email_context(
        "Please send the report to the finance team on Friday.",
        Tone.PROFESSIONAL,
        "Agree to send the report.",
    )
    decision = provider.check_grounding(
        "I will send the report to the finance team on Friday.",
        context,
    )
    assert decision.is_grounded is True