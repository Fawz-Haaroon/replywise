from domain.drafting import create_draft_result
from domain.intake import create_email_context
from llm.providers.offline_provider import OfflinePreviewProvider
from domain_types import RiskLevel, Tone


def test_offline_provider_runs_a_conservative_full_review_pipeline():
    context = create_email_context(
        "Hi Alex, can we move tomorrow's project review to Friday at 3 PM? "
        "Also, please send me the updated report before the meeting? Thanks, Rahul",
        Tone.PROFESSIONAL,
        "Keep it concise and confirm Friday at 3 PM works.",
    )
    result = create_draft_result(context, OfflinePreviewProvider())
    assert result.ai_disclosed is True
    assert result.warnings == ()
    assert result.risk_level == RiskLevel.LOW