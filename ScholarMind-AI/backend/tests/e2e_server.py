"""TEST-ONLY launcher: runs the real backend with the scripted MOCK LLM so the full stack can be exercised
without Ollama. Never used in normal operation (see scripts/start_backend.ps1 for the real launcher)."""
import os
import uvicorn
from backend.app.llm.provider_factory import set_llm_override
from backend.tests.test_agent import ScriptedLLM

os.environ["EMBEDDING_PROVIDER"] = "hashing"
set_llm_override(ScriptedLLM())
if __name__ == "__main__":
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, log_level="warning")
