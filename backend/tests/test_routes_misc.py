from fastapi.testclient import TestClient
from app.main import app, repo


client = TestClient(app)


def test_study_progress_persists_with_openid():
    headers = {"x-openid": "sp_u1"}
    payload = {"contentId": "c1", "secs": 12, "step": "learning"}
    r = client.post("/study/progress", json=payload, headers=headers)
    assert r.status_code == 200
    # verify persisted
    docs, total = repo.query("progress", {"user_id": "sp_u1"}, limit=10, offset=0)
    assert total >= 1
    assert any(d.get("contentId") == "c1" and int(d.get("secs") or 0) == 12 for d in docs)


def test_content_get_returns_item_even_if_missing():
    r = client.get("/content/demo_id_123")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "demo_id_123"
    assert data["type"] in ("sentence", "dialog", "word")


def test_billing_intent_ok():
    headers = {"x-openid": "bill_u1"}
    r = client.post("/billing/intent", json={"plan": "pro-monthly", "price": 9.9}, headers=headers)
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_wishlist_submit_ok():
    headers = {"x-openid": "wish_u1"}
    r = client.post(
        "/wishlist",
        json={"contactType": "wx", "contact": "wxid_abc", "plan": "pro", "price_point": 9.9},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_cron_daily_digest_ok():
    r = client.post("/cron/daily-digest", json={"dryRun": True})
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_request_id_header_echoed_when_provided():
    r = client.get("/health", headers={"x-request-id": "req-xyz"})
    assert r.status_code == 200
    assert r.headers.get("x-request-id") == "req-xyz"


def test_request_id_header_generated_when_missing():
    r = client.get("/health")
    assert r.status_code == 200
    rid = r.headers.get("x-request-id")
    assert isinstance(rid, str) and len(rid) > 0

