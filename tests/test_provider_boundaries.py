from dataclasses import dataclass

import pytest
import requests

from config import AppConfig
from domain.intake import create_email_context
from domain_types import Tone
from llm.providers.gemini_provider import GeminiProvider
from llm.providers.http_support import post_json
from llm.providers.ollama_provider import OllamaProvider
from llm.providers.response_parsing import parse_context_analysis


@dataclass
class FakeResponse:
    status_code: int
    payload: object
    text: str = ""

    def json(self):
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


def _ollama_config() -> AppConfig:
    return AppConfig(
        llm_provider="ollama",
        ollama_base_url="http://127.0.0.1:11434",
        ollama_model="llama3.2:3b",
        groq_api_key=None,
        groq_model="llama-3.1-8b-instant",
        gemini_api_key=None,
        gemini_model="gemini-2.0-flash",
        request_timeout_seconds=7,
    )


def _email_context():
    return create_email_context(
        "Can we meet Friday?",
        Tone.PROFESSIONAL,
        "Keep it short.",
    )


def test_ollama_adapter_sends_expected_chat_request(monkeypatch):
    calls = []

    def fake_post(url, *, json, headers, timeout):
        calls.append((url, json, headers, timeout))
        return FakeResponse(
            200,
            {
                "message": {
                    "content": '{"intent":"meeting","key_entities":["Friday"],'
                    '"detected_requests":["meet Friday"]}'
                }
            },
        )

    monkeypatch.setattr(requests, "post", fake_post)
    analysis = OllamaProvider(_ollama_config()).analyze_context(_email_context())

    assert analysis.intent == "meeting"
    assert calls[0][0] == "http://127.0.0.1:11434/api/chat"
    assert calls[0][1]["model"] == "llama3.2:3b"
    assert calls[0][1]["stream"] is False
    assert calls[0][1]["format"] == "json"
    assert calls[0][3] == 7


def test_ollama_adapter_rejects_missing_message_content(monkeypatch):
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: FakeResponse(200, {"message": {}}),
    )

    with pytest.raises(RuntimeError, match="message.content"):
        OllamaProvider(_ollama_config()).generate_reply(
            _email_context(),
            parse_context_analysis(
                '{"intent":"meeting","key_entities":[],"detected_requests":[]}'
            ),
        )


def test_provider_http_errors_identify_operation_and_endpoint(monkeypatch):
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            requests.Timeout("simulated timeout")
        ),
    )

    with pytest.raises(RuntimeError, match="Ollama context analysis.*provider endpoint"):
        OllamaProvider(_ollama_config()).analyze_context(_email_context())


def test_provider_rejects_non_json_response(monkeypatch):
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: FakeResponse(
            200,
            ValueError("not json"),
            text="<html>bad gateway</html>",
        ),
    )

    with pytest.raises(RuntimeError, match="non-JSON response"):
        OllamaProvider(_ollama_config()).analyze_context(_email_context())


def test_gemini_key_is_sent_as_a_header_not_in_the_endpoint(monkeypatch):
    calls = []

    def fake_post(url, *, json, headers, timeout):
        calls.append((url, headers))
        return FakeResponse(
            200,
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": '{"intent":"meeting","key_entities":[],"detected_requests":[]}'
                                }
                            ]
                        }
                    }
                ]
            },
        )

    config = AppConfig(
        llm_provider="gemini",
        ollama_base_url="http://127.0.0.1:11434",
        ollama_model="llama3.2:3b",
        groq_api_key=None,
        groq_model="llama-3.1-8b-instant",
        gemini_api_key="test-secret",
        gemini_model="gemini-2.0-flash",
        request_timeout_seconds=7,
    )
    monkeypatch.setattr(requests, "post", fake_post)

    GeminiProvider(config).analyze_context(_email_context())

    assert "test-secret" not in calls[0][0]
    assert calls[0][1]["x-goog-api-key"] == "test-secret"


def test_provider_errors_redact_header_secrets(monkeypatch):
    secret = "test-secret"

    def fake_post(*args, **kwargs):
        return FakeResponse(
            401,
            {"error": "unauthorized"},
            text=f"invalid key {secret}",
        )

    monkeypatch.setattr(requests, "post", fake_post)

    with pytest.raises(RuntimeError) as error:
        post_json(
            "https://example.test/v1/generate?key=also-secret",
            {"prompt": "hello"},
            {"Authorization": f"Bearer {secret}"},
            3,
            "test request",
        )

    message = str(error.value)
    assert secret not in message
    assert "also-secret" not in message
    assert "provider returned HTTP 401" in message


def test_provider_errors_do_not_expose_user_derived_response_content(monkeypatch):
    user_content = "customer-email@example.com and confidential project detail"
    monkeypatch.setattr(
        requests,
        "post",
        lambda *args, **kwargs: FakeResponse(
            502,
            {"error": "bad gateway"},
            text=user_content,
        ),
    )

    with pytest.raises(RuntimeError) as error:
        post_json(
            "https://example.test/v1/generate",
            {"prompt": user_content},
            {},
            3,
            "test request",
        )

    assert user_content not in str(error.value)