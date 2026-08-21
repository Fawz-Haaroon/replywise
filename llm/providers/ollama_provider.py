import json

from config import AppConfig
from domain_types import ContextAnalysis, EmailContext, GroundingDecision
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


class OllamaProvider:
    provider_name = "ollama"

    def __init__(self, config: AppConfig) -> None:
        self._base_url = config.ollama_base_url.rstrip("/")
        self._model = config.ollama_model
        self._timeout_seconds = config.request_timeout_seconds

    def analyze_context(self, email_context: EmailContext) -> ContextAnalysis:
        response = self._chat(
            build_context_analysis_prompt(email_context),
            "context analysis",
            response_format="json",
        )

        # Small local models can sometimes produce valid JSON with an
        # incorrect field shape. For example:
        #
        #   "key_entities": {"name": "Rahul"}
        #
        # instead of:
        #
        #   "key_entities": ["Rahul"]
        #
        # Normalize only these known schema fields at the provider boundary.
        # The strict response parser remains responsible for final validation.
        response = self._normalize_context_analysis(response)

        return parse_context_analysis(response)

    def generate_reply(
        self,
        email_context: EmailContext,
        analysis: ContextAnalysis,
    ) -> str:
        return self._chat(
            build_generation_prompt(email_context, analysis),
            "draft generation",
        )

    def check_grounding(
        self,
        candidate_sentence: str,
        email_context: EmailContext,
    ) -> GroundingDecision:
        response = self._chat(
            build_grounding_prompt(candidate_sentence, email_context),
            "grounding check",
            response_format="json",
        )

        return parse_grounding_decision(response)

    def _normalize_context_analysis(self, response: str) -> str:
        """
        Normalize common structured-output mistakes from small local models.

        Ollama guarantees valid JSON when `format="json"` is used, but it does
        not guarantee that every field has the exact shape expected by the
        application.

        For example, a local model may return:

            {
                "intent": "reschedule a meeting",
                "key_entities": {"name": "Rahul"},
                "detected_requests": ["Move the meeting"]
            }

        when ReplyWise expects:

            {
                "intent": "reschedule a meeting",
                "key_entities": ["Rahul"],
                "detected_requests": ["Move the meeting"]
            }

        Only obvious list-shape mistakes are repaired here. The final
        response parser remains responsible for schema validation.
        """
        try:
            payload = json.loads(response)
        except json.JSONDecodeError:
            # Let the existing parser produce the normal, useful error.
            return response

        if not isinstance(payload, dict):
            return response

        for field_name in ("key_entities", "detected_requests"):
            if field_name not in payload:
                continue

            value = payload[field_name]

            if isinstance(value, dict):
                payload[field_name] = self._dict_to_string_list(value)

            elif isinstance(value, str):
                payload[field_name] = [value]

            elif isinstance(value, list):
                normalized_items: list[str] = []

                for item in value:
                    normalized_item = self._normalize_list_item(item)

                    if normalized_item is not None:
                        normalized_items.append(normalized_item)

                payload[field_name] = normalized_items

        return json.dumps(payload)

    @staticmethod
    def _dict_to_string_list(value: dict) -> list[str]:
        """
        Convert a dictionary accidentally used where list[str] was expected.

        Prefer common semantic keys such as `name`, `value`, `text`,
        `description`, `label`, and `item`.
        """
        preferred_keys = (
            "name",
            "value",
            "text",
            "description",
            "label",
            "item",
        )

        for key in preferred_keys:
            candidate = value.get(key)

            if isinstance(candidate, str) and candidate.strip():
                return [candidate.strip()]

        strings: list[str] = []

        for item in value.values():
            if isinstance(item, str) and item.strip():
                strings.append(item.strip())

        return strings

    @staticmethod
    def _normalize_list_item(item: object) -> str | None:
        """
        Normalize an individual list item into a string when possible.

        Handles outputs such as:

            [{"name": "Rahul"}, "Friday"]

        becoming:

            ["Rahul", "Friday"]
        """
        if isinstance(item, str):
            value = item.strip()
            return value if value else None

        if isinstance(item, dict):
            values = OllamaProvider._dict_to_string_list(item)
            return values[0] if values else None

        return None

    def _chat(
        self,
        prompt: str,
        operation_name: str,
        response_format: str | None = None,
    ) -> str:
        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,
            },
        }

        if response_format is not None:
            payload["format"] = response_format

        payload_response = post_json(
            f"{self._base_url}/api/chat",
            payload,
            headers={"Content-Type": "application/json"},
            timeout_seconds=self._timeout_seconds,
            operation_name=f"Ollama {operation_name}",
        )

        message = payload_response.get("message")

        if (
            not isinstance(message, dict)
            or not isinstance(message.get("content"), str)
        ):
            raise RuntimeError(
                f"Ollama {operation_name} failed: "
                f"response did not contain message.content. "
                f"Received {payload_response!r}."
            )

        return message["content"].strip()
