import os
from pathlib import Path

import pytest

from config import load_config
from domain.intake import create_email_context
from domain_types import Tone
from llm.providers.ollama_provider import OllamaProvider


@pytest.mark.skipif(
    os.getenv("REPLYWISE_OLLAMA_INTEGRATION") != "1",
    reason="Set REPLYWISE_OLLAMA_INTEGRATION=1 to run the local Ollama check.",
)
def test_configured_local_ollama_generates_structured_context():
    project_root = Path(__file__).resolve().parents[1]
    config = load_config(project_root / ".env")
    if config.llm_provider != "ollama":
        pytest.skip("LLM_PROVIDER is not ollama.")
    analysis = OllamaProvider(config).analyze_context(
        create_email_context("Can we meet Friday?", Tone.PROFESSIONAL, None)
    )
    assert analysis.intent