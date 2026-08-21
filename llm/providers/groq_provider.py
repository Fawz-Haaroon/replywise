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


class GroqProvider:
    provider_name = "groq"

    def __init__(self, config: AppConfig) -> None:
        if config.groq_api_key is None:
            raise ValueError("Groq provider cannot start without GROQ_API_KEY.")
        self._api_key = config.groq_api_key
        self._model = config.groq_model
        self._timeout_seconds = config.request_timeout_seconds

    def analyze_context(self, email_context: EmailContext) -> ContextAnalysis:
        response = self._chat(build_context_analysis_prompt(email_context), "context analysis")
        return parse_context_analysis(response)

    def generate_reply(
        self,
        email_context: EmailContext,
        analysis: ContextAnalysis,
    ) -> str:
        return self._chat(build_generation_prompt(email_context, analysis), "draft generation")

    def check_grounding(
        self,
        candidate_sentence: str,
        email_context: EmailContext,
    ) -> GroundingDecision:
        response = self._chat(build_grounding_prompt(candidate_sentence, email_context), "grounding check")
        return parse_grounding_decision(response)

    def _chat(self, prompt: str, operation_name: str) -> str:
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": "Follow the user's output format exactly. Do not add commentary.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        payload_response = post_json(
            "https://api.groq.com/openai/v1/chat/completions",
            payload,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            timeout_seconds=self._timeout_seconds,
            operation_name=f"Groq {operation_name}",
        )
        choices = payload_response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError(
                f"Groq {operation_name} failed: response contained no choices. "
                f"Received {payload_response!r}."
            )
        message = choices[0].get("message") if isinstance(choices[0], dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str):
            raise RuntimeError(
                f"Groq {operation_name} failed: response did not contain message.content. "
                f"Received {payload_response!r}."
            )
        return content.strip()