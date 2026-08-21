from domain.context_analysis import build_rule_based_context_analysis, merge_context_analyses
from llm.client import LLMProvider
from responsible_ai.assumption_scan import detect_invented_details
from responsible_ai.commitment_scan import GroundingChecker, detect_unsupported_commitments
from responsible_ai.pii_scan import scan_for_sensitive_information
from responsible_ai.risk_score import calculate_prototype_risk_level
from domain_types import ContextAnalysis, DraftResult, EmailContext, RiskLevel, Warning


def create_draft_result(
    email_context: EmailContext,
    provider: LLMProvider,
) -> DraftResult:
    rule_analysis = build_rule_based_context_analysis(email_context)
    model_analysis = provider.analyze_context(email_context)
    analysis = merge_context_analyses(rule_analysis, model_analysis)
    draft_text = _require_draft_text(provider.generate_reply(email_context, analysis))

    warnings = _collect_warnings(draft_text, email_context, provider)
    return DraftResult(
        draft_text=draft_text,
        analysis=analysis,
        warnings=tuple(warnings),
        risk_level=calculate_prototype_risk_level(warnings),
    )


def review_existing_draft(
    draft_text: str,
    email_context: EmailContext,
    analysis: ContextAnalysis,
    provider: LLMProvider,
) -> DraftResult:
    normalized_draft = _require_draft_text(draft_text)
    warnings = _collect_warnings(normalized_draft, email_context, provider)
    return DraftResult(
        draft_text=normalized_draft,
        analysis=analysis,
        warnings=tuple(warnings),
        risk_level=calculate_prototype_risk_level(warnings),
    )


def _require_draft_text(draft_text: str) -> str:
    normalized_draft = draft_text.strip()
    if not normalized_draft:
        raise RuntimeError(
            "Draft generation failed: the selected provider returned an empty response. "
            "Check the provider model and request logs before trying again."
        )
    return normalized_draft


def _collect_warnings(
    draft_text: str,
    email_context: EmailContext,
    provider: LLMProvider,
) -> list[Warning]:
    warnings: list[Warning] = []
    warnings.extend(scan_for_sensitive_information(draft_text))
    warnings.extend(
        detect_unsupported_commitments(
            draft_text,
            email_context,
            grounding_checker=_as_grounding_checker(provider),
        )
    )
    warnings.extend(detect_invented_details(draft_text, email_context))
    return warnings


def _as_grounding_checker(provider: LLMProvider) -> GroundingChecker:
    return provider