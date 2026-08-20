from typing import Protocol

from domain_types import ContextAnalysis, EmailContext, GroundingDecision


class LLMProvider(Protocol):
    provider_name: str

    def analyze_context(self, email_context: EmailContext) -> ContextAnalysis:
        ...

    def generate_reply(
        self,
        email_context: EmailContext,
        analysis: ContextAnalysis,
    ) -> str:
        ...

    def check_grounding(
        self,
        candidate_sentence: str,
        email_context: EmailContext,
    ) -> GroundingDecision:
        ...