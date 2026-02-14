from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_vocab_scoped_by_user():
    u1 = {"x-openid": "user_1"}
    u2 = {"x-openid": "user_2"}
    # user_1 adds a word
    client.post("/vocab", json={"word": "hello"}, headers=u1)
    # user_1 can see it
    r = client.get("/vocab", headers=u1)
    words = [it["word"] for it in r.json()["items"]]
    assert "hello" in words
    # user_2 cannot see it
    r = client.get("/vocab", headers=u2)
    words2 = [it["word"] for it in r.json()["items"]]
    assert "hello" not in words2

