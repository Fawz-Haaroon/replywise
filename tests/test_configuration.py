import pytest

from config import ConfigurationError, load_config


def _clear_provider_environment(monkeypatch) -> None:
    for name in (
        "LLM_PROVIDER",
        "OLLAMA_BASE_URL",
        "OLLAMA_MODEL",
        "GROQ_API_KEY",
        "GROQ_MODEL",
        "GEMINI_API_KEY",
        "GEMINI_MODEL",
        "LLM_REQUEST_TIMEOUT_SECONDS",
    ):
        monkeypatch.delenv(name, raising=False)


def test_offline_configuration_does_not_require_network_or_cloud_credentials(monkeypatch):
    _clear_provider_environment(monkeypatch)
    config = load_config()

    assert config.llm_provider == "offline"
    assert config.ollama_model == "llama3.2:3b"
    assert config.request_timeout_seconds == 60


def test_ollama_configuration_does_not_require_cloud_credentials(monkeypatch):
    _clear_provider_environment(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", "ollama")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2:3b")

    config = load_config()

    assert config.llm_provider == "ollama"
    assert config.groq_api_key is None
    assert config.gemini_api_key is None


@pytest.mark.parametrize("provider", ["invalid", "openai", ""])
def test_invalid_provider_is_rejected(monkeypatch, provider):
    _clear_provider_environment(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", provider)

    with pytest.raises(ConfigurationError, match="LLM_PROVIDER is invalid"):
        load_config()


@pytest.mark.parametrize(
    ("provider", "variable"),
    [("groq", "GROQ_API_KEY"), ("gemini", "GEMINI_API_KEY")],
)
def test_selected_cloud_provider_requires_only_its_own_key(monkeypatch, provider, variable):
    _clear_provider_environment(monkeypatch)
    monkeypatch.setenv("LLM_PROVIDER", provider)

    with pytest.raises(ConfigurationError, match=variable):
        load_config()


def test_timeout_must_be_positive(monkeypatch):
    _clear_provider_environment(monkeypatch)
    monkeypatch.setenv("LLM_REQUEST_TIMEOUT_SECONDS", "0")

    with pytest.raises(ConfigurationError, match="positive number"):
        load_config()