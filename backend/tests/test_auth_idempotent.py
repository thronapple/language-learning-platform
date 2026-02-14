from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_auth_me_idempotent_same_openid():
    code = "abc123456"
    r1 = client.post("/auth/me", json={"code": code})
    assert r1.status_code == 200
    openid1 = r1.json()["user"]["openid"]
    r2 = client.post("/auth/me", json={"code": code})
    assert r2.status_code == 200
    openid2 = r2.json()["user"]["openid"]
    assert openid1 == openid2

