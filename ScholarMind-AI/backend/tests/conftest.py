"""Test fixtures. Embeddings: deterministic HashingEmbedder (offline). LLM: mocks (NOT a real model)."""
import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("SCHOLARMIND_DATA_DIR", tempfile.mkdtemp(prefix="sm_import_"))
os.environ["EMBEDDING_PROVIDER"] = "hashing"

from fastapi.testclient import TestClient  # noqa: E402

from backend.app.llm.base import LLMProvider  # noqa: E402
from backend.app.llm.provider_factory import set_llm_override  # noqa: E402
from backend.app.main import create_app  # noqa: E402

PAGE1 = ("Supervised learning trains a model on labeled examples. Each training example pairs an input with a "
         "known target, and the algorithm learns a mapping from inputs to targets. Classification and regression "
         "are the two main supervised tasks. Overfitting happens when a model memorises noise in the training data.")
PAGE2 = ("Unsupervised learning finds structure in unlabeled data. Clustering groups similar items together, and "
         "dimensionality reduction compresses features while keeping the important variation. K-means is a "
         "popular clustering algorithm that assigns points to the nearest centroid.")
PAGE3 = ("Photosynthesis converts light energy into chemical energy in chloroplasts. Chlorophyll absorbs red and "
         "blue light, and the Calvin cycle fixes carbon dioxide into sugars.")


class MockLLM(LLMProvider):
    """Deterministic stand-in. Returns a cited answer. NOT a real model."""
    name = "mock"

    def __init__(self):
        self.calls = 0

    def generate(self, system, prompt):
        self.calls += 1
        return "According to the excerpts, the answer is supported by the document [S1]."

    def status(self):
        return {"available": True, "provider": "mock", "model": "mock", "detail": "MOCK - not a real LLM"}


def make_pdf(path: Path, pages):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import simpleSplit
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(str(path), pagesize=A4)
    for text in pages:
        y = 780
        for line in simpleSplit(text, "Helvetica", 11, 480):
            c.setFont("Helvetica", 11)
            c.drawString(50, y, line)
            y -= 16
        c.showPage()
    c.save()


def make_docx(path: Path):
    import docx
    d = docx.Document()
    d.add_heading("Machine Learning Basics", level=1)
    d.add_paragraph(PAGE1)
    d.add_heading("Unsupervised Methods", level=2)
    d.add_paragraph(PAGE2)
    d.save(str(path))


@pytest.fixture()
def sample_files(tmp_path):
    pdf, docx_, md = tmp_path / "ml_notes.pdf", tmp_path / "ml_basics.docx", tmp_path / "notes.md"
    make_pdf(pdf, [PAGE1, PAGE2, PAGE3])
    make_docx(docx_)
    md.write_text("# Intro\nGradient descent minimises a loss function.\n\n# Details\nLearning rate controls step size.")
    return {"pdf": pdf, "docx": docx_, "md": md}


@pytest.fixture()
def mock_llm():
    m = MockLLM()
    set_llm_override(m)
    yield m
    set_llm_override(None)


@pytest.fixture()
def data_dir(tmp_path, monkeypatch):
    d = tmp_path / "data"
    monkeypatch.setenv("SCHOLARMIND_DATA_DIR", str(d))
    return d


@pytest.fixture()
def client(data_dir):
    with TestClient(create_app()) as c:
        yield c


def upload(client, path, name=None, mime="application/octet-stream", category="Course"):
    with open(path, "rb") as fh:
        return client.post("/api/documents/upload", files=[("files", (name or Path(path).name, fh, mime))],
                           data={"category": category})
