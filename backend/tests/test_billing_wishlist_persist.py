from fastapi.testclient import TestClient
from app.main import app, repo


client = TestClient(app)


def test_billing_persists_order_with_intent():
    headers = {"x-openid": "bill_user_1"}
    payload = {"plan": "pro-monthly", "price": 9.9}
    r = client.post("/billing/intent", json=payload, headers=headers)
    assert r.status_code == 200
    docs, total = repo.query("orders", {"user_id": "bill_user_1"}, limit=10, offset=0)
    assert total >= 1
    assert any(d.get("plan") == "pro-monthly" and d.get("status") == "intent" for d in docs)


def test_wishlist_persists_contact():
    headers = {"x-openid": "wish_user_1"}
    payload = {"contactType": "wx", "contact": "wxid_xyz", "plan": "pro", "price_point": 9.9}
    r = client.post("/wishlist", json=payload, headers=headers)
    assert r.status_code == 200
    docs, total = repo.query("wishlists", {"user_id": "wish_user_1"}, limit=10, offset=0)
    assert total >= 1
    assert any(d.get("contact") == "wxid_xyz" and d.get("contactType") == "wx" for d in docs)

