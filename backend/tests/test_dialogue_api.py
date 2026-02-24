"""Tests for the dialogue and scenario API endpoints."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_dialogue_by_id():
    r = client.get("/api/dialogues/airport-checkin-001")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "airport-checkin-001"
    assert "sentences" in data
    assert len(data["sentences"]) > 0
    # Each sentence should have an audio_url (static or dynamic TTS)
    for s in data["sentences"]:
        assert "audio_url" in s
        assert "/static/audio/" in s["audio_url"] or "tts/audio" in s["audio_url"]


def test_get_dialogue_not_found():
    r = client.get("/api/dialogues/nonexistent-dialogue")
    assert r.status_code == 404


def test_list_scenarios():
    r = client.get("/api/scenarios")
    assert r.status_code == 200
    data = r.json()
    assert "scenarios" in data
    assert len(data["scenarios"]) > 0


def test_get_scenario_by_id():
    r = client.get("/api/scenarios/airport-basics")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == "airport-basics"
    assert "name_zh" in data


def test_get_scenario_not_found():
    r = client.get("/api/scenarios/nonexistent")
    assert r.status_code == 404


def test_list_scenario_dialogues():
    r = client.get("/api/scenarios/airport-basics/dialogues")
    assert r.status_code == 200
    data = r.json()
    assert "dialogues" in data
    assert len(data["dialogues"]) > 0


def test_dialogue_complete_saves_progress():
    headers = {"x-openid": "test_dialogue_user"}
    r = client.post("/api/dialogue/complete", json={
        "dialogue_id": "airport-checkin-001",
        "play_count": 5,
        "record_count": 2,
        "duration": 180,
    }, headers=headers)
    assert r.status_code == 200
    assert r.json()["ok"] is True
