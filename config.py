import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


SUPPORTED_LLM_PROVIDERS = ("offline", "ollama", "groq", "gemini")


class ConfigurationError(RuntimeError):
    """Raised when startup configuration cannot support the selected provider."""


@dataclass(frozen=True)
class AppConfig:
    llm_provider: str
    ollama_base_url: str
    ollama_model: str
    groq_api_key: str | None
    groq_model: str
    gemini_api_key: str | None
    gemini_model: str
    request_timeout_seconds: float


def load_config(environment_path: Path | None = None) -> AppConfig:
    if environment_path is not None:
        load_dotenv(dotenv_path=environment_path)

    provider = os.getenv("LLM_PROVIDER", "offline").strip().lower()
    if provider not in SUPPORTED_LLM_PROVIDERS:
        allowed = ", ".join(SUPPORTED_LLM_PROVIDERS)
        raise ConfigurationError(
            f"Configuration field LLM_PROVIDER is invalid: received '{provider}', "
            f"expected one of {allowed}."
        )

    groq_api_key = _read_optional_secret("GROQ_API_KEY")
    gemini_api_key = _read_optional_secret("GEMINI_API_KEY")
    _require_provider_key(provider, groq_api_key, gemini_api_key)

    timeout_value = os.getenv("LLM_REQUEST_TIMEOUT_SECONDS", "60").strip()
    try:
        timeout_seconds = float(timeout_value)
    except ValueError as error:
        raise ConfigurationError(
            "Configuration field LLM_REQUEST_TIMEOUT_SECONDS is invalid: "
            f"received '{timeout_value}', expected a positive number of seconds."
        ) from error
    if timeout_seconds <= 0:
        raise ConfigurationError(
            "Configuration field LLM_REQUEST_TIMEOUT_SECONDS is invalid: "
            f"received '{timeout_value}', expected a positive number of seconds."
        )

    return AppConfig(
        llm_provider=provider,
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").strip(),
        ollama_model=os.getenv("OLLAMA_MODEL", "llama3.2:3b").strip(),
        groq_api_key=groq_api_key,
        groq_model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip(),
        gemini_api_key=gemini_api_key,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip(),
        request_timeout_seconds=timeout_seconds,
    )


def _read_optional_secret(name: str) -> str | None:
    value = os.getenv(name)
    if value is None:
        return None
    stripped_value = value.strip()
    return stripped_value or None


def _require_provider_key(
    provider: str,
    groq_api_key: str | None,
    gemini_api_key: str | None,
) -> None:
    required_key_by_provider = {
        "groq": ("GROQ_API_KEY", groq_api_key),
        "gemini": ("GEMINI_API_KEY", gemini_api_key),
    }
    required_key = required_key_by_provider.get(provider)
    if required_key is None:
        return

    variable_name, value = required_key
    if value is None:
        raise ConfigurationError(
            f"Configuration field {variable_name} is missing for LLM_PROVIDER={provider}. "
            "Add it to .env or choose LLM_PROVIDER=ollama or offline."
        )