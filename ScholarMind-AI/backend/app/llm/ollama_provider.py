"""Ollama (local, free) provider. Detects whether the server and the configured model are present."""
import httpx
from .base import LLMProvider, LLMUnavailable


class OllamaProvider(LLMProvider):
    name = "ollama"

    def __init__(self, url, model, timeout):
        self.url, self.model, self.timeout = url.rstrip("/"), model, timeout

    def status(self):
        try:
            tags = httpx.get(f"{self.url}/api/tags", timeout=3).json().get("models", [])
        except Exception:
            return {"available": False, "provider": self.name, "model": self.model,
                    "detail": f"Ollama is not reachable at {self.url}. Install it from https://ollama.com and start it."}
        names = {m.get("name", "") for m in tags}
        installed = self.model in names or (":" not in self.model and f"{self.model}:latest" in names)
        if not installed:
            return {"available": False, "provider": self.name, "model": self.model,
                    "detail": f"Model not installed. Run: ollama pull {self.model}"}
        return {"available": True, "provider": self.name, "model": self.model, "detail": "ready"}

    def generate(self, system, prompt):
        st = self.status()
        if not st["available"]:
            raise LLMUnavailable(st["detail"])
        try:
            r = httpx.post(f"{self.url}/api/chat", timeout=self.timeout, json={
                "model": self.model, "stream": False, "options": {"temperature": 0.2},
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]})
            r.raise_for_status()
            return r.json()["message"]["content"].strip()
        except httpx.TimeoutException as exc:
            raise LLMUnavailable(f"LLM timed out after {self.timeout:.0f}s; try a smaller model.") from exc
        except Exception as exc:
            raise LLMUnavailable(f"LLM request failed: {exc}") from exc
