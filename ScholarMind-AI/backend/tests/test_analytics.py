from backend.tests.conftest import upload
from backend.tests.test_agent import chat, llm  # noqa: F401  (scripted mock LLM fixture)


def test_overview_empty_then_real_counts(client, sample_files, llm):
    ov = client.get("/api/analytics/overview").json()
    assert ov["documents"]["total"] == 0 and ov["chunks"] == 0 and ov["recent_documents"] == []
    upload(client, sample_files["pdf"], category="Course")
    chat(client, "What is overfitting in supervised learning?")
    ov = client.get("/api/analytics/overview").json()
    assert ov["documents"]["indexed"] == 1 and ov["chunks"] > 0 and ov["conversations"] == 1 and ov["messages"] == 2
    assert ov["by_category"] == {"Course": 1} and ov["by_type"] == {"pdf": 1}


def test_usage_counts_tools_and_today(client, sample_files, llm):
    upload(client, sample_files["pdf"])
    chat(client, "What is overfitting in supervised learning?")
    u = client.get("/api/analytics/usage").json()
    assert u["tools"] == {"document_qa": 1} and u["statuses"] == {"answered": 1}
    assert u["messages_per_day"][-1]["user"] == 1 and len(u["messages_per_day"]) == 14


def test_documents_analytics(client, sample_files):
    upload(client, sample_files["docx"])
    d = client.get("/api/analytics/documents").json()["documents"]
    assert d[0]["file_type"] == "docx" and d[0]["chunk_count"] >= 1


def test_research_compare_validation_and_clear(client, sample_files, llm):
    assert client.post("/api/study/research", json={}).status_code == 422
    assert client.post("/api/study/compare", json={"document_ids": []}).status_code == 422
    upload(client, sample_files["pdf"])
    r = client.post("/api/study/research", json={"topic": "overfitting in training data"}).json()
    assert r["tool"] == "research" and r["status"] == "answered"
    cid = chat(client, "hello").json()["conversation_id"]
    assert client.delete(f"/api/conversations/{cid}/messages").status_code == 200
    assert client.get(f"/api/conversations/{cid}").json()["messages"] == []
