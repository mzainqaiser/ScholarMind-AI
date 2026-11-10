from abc import ABC, abstractmethod


class LLMUnavailable(Exception):
    """Raised when no LLM provider is configured/reachable. Mapped to HTTP 503 with setup guidance."""


class LLMProvider(ABC):
    name = "base"

    @abstractmethod
    def generate(self, system: str, prompt: str) -> str: ...

    @abstractmethod
    def status(self) -> dict:
        """Return {available: bool, provider, model, detail}."""
