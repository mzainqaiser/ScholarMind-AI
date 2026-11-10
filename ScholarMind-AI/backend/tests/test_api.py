"""API + integration tests (real SQLite, real ChromaDB, real PyMuPDF; HashingEmbedder; mock LLM where noted)."""
from fastapi.testclient import TestClient
from backend.app.main import create_app
from backend.tests.conftest import upload


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_upload_pdf_indexes_and_lists(client, sample_files):
    r = upload(client, sample_files["pdf"])
    assert r.status_code == 200
    doc = r.json()["results"][0]["document"]
    assert doc["status"] == "indexed" and doc["pages"] == 3 and doc["chunk_count"] >= 3 and doc["category"] == "Course"
    assert [d["id"] for d in client.get("/api/documents").json()["documents"]] == [doc["id"]]
    assert "[Page 1]" in client.get(f"/api/documents/{doc['id']}/preview").json()["text"]


def test_invalid_extension_rejected(client, tmp_path):
    p = tmp_path / "evil.exe"
    p.write_bytes(b"MZ\x00\x00")
    assert upload(client, p).status_code == 400


def test_fake_pdf_marked_failed_not_searchable(client, tmp_path):
    p = tmp_path / "fake.pdf"
    p.write_text("hello, I am not a pdf")
    doc = upload(client, p).json()["results"][0]["document"]
    assert doc["status"] == "failed" and "valid PDF" in doc["error"]


def test_path_traversal_filename_sanitised(client, sample_files):
    r = upload(client, sample_files["md"], name="../../etc/passwd.md")
    assert r.json()["results"][0]["document"]["filename"] == "passwd.md"


def test_oversize_rejected(client, monkeypatch, sample_files, data_dir):
    monkeypatch.setenv("MAX_UPLOAD_MB", "0")
    with TestClient(create_app()) as c:
        assert upload(c, sample_files["md"]).status_code == 400


def test_duplicate_upload_rejected(client, sample_files):
    assert upload(client, sample_files["pdf"]).status_code == 200
    r = upload(client, sample_files["pdf"])
    assert r.status_code == 400 and "Duplicate" in r.json()["detail"][0]["error"]


def test_search_returns_correct_page(client, sample_files):
    upload(client, sample_files["pdf"])
    top = client.post("/api/rag/search", json={"query": "Which algorithm assigns points to the nearest centroid?"}).json()["results"][0]
    assert top["page"] == 2 and top["filename"] == "ml_notes.pdf" and "K-means" in top["excerpt"]


def test_document_filter(client, sample_files):
    upload(client, sample_files["pdf"])
    d2 = upload(client, sample_files["md"]).json()["results"][0]["document"]["id"]
    res = client.post("/api/rag/search", json={"query": "learning", "document_ids": [d2]}).json()["results"]
    assert res and all(r["doc_id"] == d2 for r in res)


def test_query_answered_with_valid_citations(client, sample_files, mock_llm):
    upload(client, sample_files["pdf"])
    r = client.post("/api/rag/query", json={"query": "What is overfitting in supervised learning?"}).json()
    assert r["status"] == "answered" and mock_llm.calls == 1
    assert r["invalid_citation_markers"] == [] and any(c["cited_in_answer"] for c in r["citations"])


def test_insufficient_evidence_skips_llm(client, mock_llm):
    r = client.post("/api/rag/query", json={"query": "What is the capital of France?"}).json()   # empty KB
    assert r["status"] == "insufficient_evidence" and r["citations"] == [] and mock_llm.calls == 0


def test_llm_unavailable_gives_503(client, sample_files, monkeypatch):
    monkeypatch.setenv("OLLAMA_URL", "http://127.0.0.1:9")
    with TestClient(create_app()) as c:
        upload(c, sample_files["pdf"])
        r = c.post("/api/rag/query", json={"query": "What is supervised learning?"})
        assert r.status_code == 503
        assert r.json()["detail"]["error"] == "llm_unavailable" and "not reachable" in r.json()["detail"]["message"]
        assert c.get("/api/system/status").json()["llm"]["available"] is False


def test_delete_removes_metadata_vectors_and_file(client, sample_files, data_dir):
    doc = upload(client, sample_files["pdf"]).json()["results"][0]["document"]
    assert client.get("/api/system/status").json()["vector_store"]["chunks"] > 0
    assert client.delete(f"/api/documents/{doc['id']}").status_code == 200
    st = client.get("/api/system/status").json()
    assert st["vector_store"]["chunks"] == 0 and st["database"]["documents"] == 0
    assert client.get(f"/api/documents/{doc['id']}").status_code == 404
    assert not list((data_dir / "uploads").glob("*"))


def test_reindex(client, sample_files):
    doc = upload(client, sample_files["docx"]).json()["results"][0]["document"]
    n = doc["chunk_count"]
    r = client.post(f"/api/documents/{doc['id']}/reindex").json()
    assert r["status"] == "indexed" and r["chunk_count"] == n
    assert client.get("/api/system/status").json()["vector_store"]["chunks"] == n   # no duplicates


def test_persistence_across_restart(data_dir, sample_files):
    with TestClient(create_app()) as c1:
        doc_id = upload(c1, sample_files["pdf"]).json()["results"][0]["document"]["id"]
    with TestClient(create_app()) as c2:                       # brand-new app instance, same storage
        assert c2.get(f"/api/documents/{doc_id}").json()["status"] == "indexed"
        assert c2.post("/api/rag/search", json={"query": "clustering"}).json()["results"][0]["page"] == 2
