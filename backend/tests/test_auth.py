from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_auth_me_returns_user():
    resp = client.post("/auth/me", json={"code": "demo_code_123456"})
    assert resp.status_code == 200
    data = resp.json()
    assert "user" in data
    assert data["user"]["openid"].startswith("mock_")

