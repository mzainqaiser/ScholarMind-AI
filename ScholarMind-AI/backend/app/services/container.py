"""Service container: one place that wires settings, DB, embedder and vector store together."""
import logging
from ..config import load_settings
from ..database import Database
from ..embeddings.embedding_service import get_embedder
from ..vectorstore.chroma_service import VectorStore

log = logging.getLogger("scholarmind")


class Services:
    def __init__(self):
        self.settings = load_settings()
        s = self.settings
        s.upload_dir.mkdir(parents=True, exist_ok=True)
        s.chroma_dir.mkdir(parents=True, exist_ok=True)
        self.db = Database(s.db_path)
        self.embedder = get_embedder(s.embedding_provider, s.embedding_model)
        self.store = VectorStore(s.chroma_dir, self.embedder.name)
