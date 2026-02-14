from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_write_endpoints_require_openid():
    # study
    r = client.post("/study/progress", json={"contentId": "1", "secs": 5, "step": "new"})
    assert r.status_code == 401
    # vocab add
    r = client.post("/vocab", json={"word": "test"})
    assert r.status_code == 401

