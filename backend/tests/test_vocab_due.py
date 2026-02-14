from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_vocab_due_filters_by_before():
    headers = {"x-openid": "due_user"}
    # Add and review to set a future next_review_at
    client.post("/vocab", json={"word": "alpha"}, headers=headers)
    client.post("/vocab/review", json={"word": "alpha", "rating": "good"}, headers=headers)

    # before=now -> likely not due
    now_iso = datetime.now(timezone.utc).isoformat()
    r = client.get("/vocab/due", params={"before": now_iso}, headers=headers)
    assert r.status_code == 200
    assert r.json()["total"] == 0

    # before far future -> should include alpha
    future_iso = (datetime.now(timezone.utc) + timedelta(days=3650)).isoformat()
    r = client.get("/vocab/due", params={"before": future_iso}, headers=headers)
    assert r.status_code == 200
    items = r.json()["items"]
    words = [it["word"] for it in items]
    assert "alpha" in words

