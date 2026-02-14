from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_events_track_requires_openid():
    r = client.post("/events", json={"event": "test", "props": {"a": 1}})
    assert r.status_code == 401


def test_events_track_ok():
    headers = {"x-openid": "evt_u1"}
    r = client.post("/events", json={"event": "lesson_start", "props": {"id": "c1"}}, headers=headers)
    assert r.status_code == 200
    assert r.json()["ok"] is True

