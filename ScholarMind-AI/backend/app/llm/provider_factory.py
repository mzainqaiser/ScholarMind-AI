from .base import LLMUnavailable
from .ollama_provider import OllamaProvider

_override = None


def set_llm_override(provider):
    """Tests inject a mock provider here. Never used in normal operation."""
    global _override
    _override = provider


def get_llm(settings):
    if _override is not None:
        return _override
    if settings.llm_provider == "ollama":
        return OllamaProvider(settings.ollama_url, settings.ollama_model, settings.llm_timeout_s)
    raise LLMUnavailable(f"Unknown LLM_PROVIDER '{settings.llm_provider}'. Supported: ollama.")
