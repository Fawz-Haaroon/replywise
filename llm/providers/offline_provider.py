import re

from domain.context_analysis import build_rule_based_context_analysis
from domain_types import ContextAnalysis, EmailContext, GroundingDecision


class OfflinePreviewProvider:
    provider_name = "offline"

    def analyze_context(self, email_context: EmailContext) -> ContextAnalysis:
        return build_rule_based_context_analysis(email_context)

    def generate_reply(
        self,
        email_context: EmailContext,
        analysis: ContextAnalysis,
    ) -> str:
        greeting = _extract_sender_name(email_context.original_email) or "there"
        closing = "Best"
        if email_context.tone.value == "friendly":
            closing = "Thanks"
        if email_context.instruction and "short" in email_context.instruction.lower():
            return f"Hi {greeting},\n\nThanks for your note. I’ll review this and follow up.\n\n{closing},"
        return (
            f"Hi {greeting},\n\n"
            "Thanks for your note. I’ll review this and follow up.\n\n"
            f"{closing},"
        )

    def check_grounding(
        self,
        candidate_sentence: str,
        email_context: EmailContext,
    ) -> GroundingDecision:
        source = f"{email_context.original_email} {email_context.instruction or ''}".lower()
        stop_words = {
            "will", "works", "for", "with", "that", "have", "the", "and",
            "this", "your", "you", "from", "into", "after", "before",
            "please", "can", "could", "would", "i", "am", "to", "ll", "i'll",
            "i've", "send", "share", "provide", "prepare", "finish", "complete",
            "deliver", "confirm", "schedule", "review", "follow", "up",
        }
        candidate_terms = {
            term.lower()
            for term in re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]{2,}", candidate_sentence)
            if term.lower() not in stop_words
        }
        source_terms = {
            term.lower()
            for term in re.findall(r"[A-Za-z0-9][A-Za-z0-9'-]{2,}", source)
        }
        is_grounded = bool(candidate_terms) and candidate_terms <= source_terms
        return GroundingDecision(
            is_grounded=is_grounded,
            reason=(
                "The specific detail appears in the source."
                if is_grounded
                else "The specific detail does not appear in the source."
            ),
        )
def _extract_sender_name(original_email: str) -> str | None:
    match = re.search(r"^(?:hi|hello|dear)\s+([A-Za-z][A-Za-z'-]+)", original_email, re.IGNORECASE)
    return match.group(1) if match else None