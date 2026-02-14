from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_content_list_returns_seeded_items():
    r = client.get("/content")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data["items"], list)
    # Seed puts at least two samples in memory repo
    assert data["total"] >= 2


def test_content_list_filter_type_sentence():
    r = client.get("/content", params={"type": "sentence"})
    assert r.status_code == 200
    items = r.json()["items"]
    for it in items:
        assert it["type"] == "sentence"

