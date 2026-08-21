from config import AppConfig
from llm.prompts import (
    build_context_analysis_prompt,
    build_generation_prompt,
    build_grounding_prompt,
)
from llm.providers.http_support import post_json
from llm.providers.response_parsing import (
    parse_context_analysis,
    parse_grounding_decision,
)
from domain_types import ContextAnalysis, EmailContext, GroundingDecision


class GeminiProvider:
    provider_name = "gemini"

    def __init__(self, config: AppConfig) -> None:
        if config.gemini_api_key is None:
            raise ValueError("Gemini provider cannot start without GEMINI_API_KEY.")
        self._api_key = config.gemini_api_key
        self._model = config.gemini_model
        self._timeout_seconds = config.request_timeout_seconds

    def analyze_context(self, email_context: EmailContext) -> ContextAnalysis:
        response = self._generate(build_context_analysis_prompt(email_context), "context analysis")
        return parse_context_analysis(response)

    def generate_reply(
        self,
        email_context: EmailContext,
        analysis: ContextAnalysis,
    ) -> str:
        return self._generate(build_generation_prompt(email_context, analysis), "draft generation")

    def check_grounding(
        self,
        candidate_sentence: str,
        email_context: EmailContext,
    ) -> GroundingDecision:
        response = self._generate(build_grounding_prompt(candidate_sentence, email_context), "grounding check")
        return parse_grounding_decision(response)

    def _generate(self, prompt: str, operation_name: str) -> str:
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1},
        }
        payload_response = post_json(
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:generateContent",
            payload,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self._api_key,
            },
            timeout_seconds=self._timeout_seconds,
            operation_name=f"Gemini {operation_name}",
        )
        candidates = payload_response.get("candidates")
        if not isinstance(candidates, list) or not candidates:
            raise RuntimeError(
                f"Gemini {operation_name} failed: response contained no candidates. "
                f"Received {payload_response!r}."
            )
        content = candidates[0].get("content") if isinstance(candidates[0], dict) else None
        parts = content.get("parts") if isinstance(content, dict) else None
        text = parts[0].get("text") if isinstance(parts, list) and parts else None
        if not isinstance(text, str):
            raise RuntimeError(
                f"Gemini {operation_name} failed: response did not contain candidate text. "
                f"Received {payload_response!r}."
            )
        return text.strip()