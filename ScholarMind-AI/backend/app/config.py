"""Central configuration. Every value can be overridden with an environment variable (see .env.example)."""
import os
import re
from dataclasses import dataclass
from pathlib import Path


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    max_upload_mb: int
    chunk_size: int
    chunk_overlap: int
    top_k: int
    min_score: float
    context_char_budget: int
    embedding_provider: str      # "auto" | "sentence-transformers" | "hashing"
    embedding_model: str
    llm_provider: str            # "ollama"
    ollama_url: str
    ollama_model: str
    llm_timeout_s: float
    agent_max_steps: int
    cors_origins: list

    @property
    def upload_dir(self) -> Path: return self.data_dir / "uploads"
    @property
    def chroma_dir(self) -> Path: return self.data_dir / "chroma"
    @property
    def db_path(self) -> Path: return self.data_dir / "scholarmind.db"


def _load_dotenv(path: Path) -> None:
    """Minimal .env reader (no extra dependency). Real environment variables always win over the file."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = re.split(r"\s+#", value.strip(), maxsplit=1)[0].strip().strip("\"'")   # drop trailing "  # comment"
        os.environ.setdefault(key.strip(), value)


def load_settings() -> Settings:
    """Read settings at call time so tests can point DATA_DIR at a temp folder."""
    root = Path(__file__).resolve().parents[2]
    _load_dotenv(root / ".env")
    return Settings(
        data_dir=Path(_env("SCHOLARMIND_DATA_DIR", str(root / "storage" / "data"))),
        max_upload_mb=int(_env("MAX_UPLOAD_MB", "20")),
        chunk_size=int(_env("CHUNK_SIZE", "800")),
        chunk_overlap=int(_env("CHUNK_OVERLAP", "120")),
        top_k=int(_env("TOP_K", "5")),
        min_score=float(_env("MIN_SCORE", "0.12")),
        context_char_budget=int(_env("CONTEXT_CHAR_BUDGET", "6000")),
        embedding_provider=_env("EMBEDDING_PROVIDER", "auto"),
        embedding_model=_env("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"),
        llm_provider=_env("LLM_PROVIDER", "ollama"),
        ollama_url=_env("OLLAMA_URL", "http://localhost:11434"),
        ollama_model=_env("OLLAMA_MODEL", "qwen2.5:3b-instruct"),
        llm_timeout_s=float(_env("LLM_TIMEOUT_S", "120")),
        agent_max_steps=int(_env("AGENT_MAX_STEPS", "12")),
        cors_origins=_env("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","),
    )
