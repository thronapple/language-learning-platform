from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_vocab_crud_with_openid():
    headers = {"x-openid": "mock_user_1"}
    # add
    r = client.post("/vocab", json={"word": "hello"}, headers=headers)
    assert r.status_code == 200
    # list
    r = client.get("/vocab", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 1
    words = [it["word"] for it in data["items"]]
    assert "hello" in words
    # delete
    r = client.delete("/vocab/hello", headers=headers)
    assert r.status_code == 200

