from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_vocab_review_increases_level_and_sets_next_review_at():
    headers = {"x-openid": "srs_user"}
    # ensure exists
    client.post("/vocab", json={"word": "world"}, headers=headers)
    # review good
    r = client.post("/vocab/review", json={"word": "world", "rating": "good"}, headers=headers)
    assert r.status_code == 200
    data = r.json()
    item = data["item"]
    assert item["srs_level"] >= 1
    assert item["next_review_at"]

