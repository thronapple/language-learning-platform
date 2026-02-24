"""Tests for the plan API endpoints."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
USER_HEADERS = {"x-openid": "plan_test_user"}


def test_plan_generate():
    r = client.post("/api/plan/generate", json={
        "overall_level": "A2",
        "weak_areas": ["listening"],
        "strong_areas": ["vocabulary"],
        "daily_minutes": 30,
    }, headers=USER_HEADERS)
    assert r.status_code == 200
    plan = r.json()
    assert "id" in plan
    assert plan["status"] == "active"
    assert plan["overall_level"] == "A2"
    assert len(plan["scenario_goals"]) > 0
    assert len(plan["daily_tasks"]) > 0
    # Each scenario goal should have required fields
    goal = plan["scenario_goals"][0]
    assert "scenario_name" in goal
    assert "icon" in goal
    assert "dialogue_ids" in goal


def test_plan_current_after_generate():
    # Generate first
    client.post("/api/plan/generate", json={
        "overall_level": "B1",
        "weak_areas": ["grammar"],
        "strong_areas": [],
    }, headers=USER_HEADERS)

    # Get current
    r = client.get("/api/plan/current", headers=USER_HEADERS)
    assert r.status_code == 200
    plan = r.json()
    assert plan["overall_level"] == "B1"
    assert plan["status"] == "active"


def test_plan_current_404_when_no_plan():
    r = client.get("/api/plan/current", headers={"x-openid": "no_plan_user"})
    assert r.status_code == 404


def test_plan_pause_and_resume():
    # Generate
    r = client.post("/api/plan/generate", json={
        "overall_level": "A2", "weak_areas": [], "strong_areas": [],
    }, headers={"x-openid": "pause_user"})
    plan_id = r.json()["id"]

    # Pause
    r = client.put(f"/api/plan/{plan_id}/pause", headers={"x-openid": "pause_user"})
    assert r.status_code == 200
    assert r.json()["status"] == "paused"

    # Resume
    r = client.put(f"/api/plan/{plan_id}/resume", headers={"x-openid": "pause_user"})
    assert r.status_code == 200
    assert r.json()["status"] == "active"


def test_plan_progress_update():
    # Generate plan
    r = client.post("/api/plan/generate", json={
        "overall_level": "A2", "weak_areas": [], "strong_areas": [],
    }, headers={"x-openid": "progress_user"})
    plan = r.json()
    plan_id = plan["id"]
    first_dialogue = plan["daily_tasks"][0]["dialogue_id"]

    # Update progress
    r = client.put(f"/api/plan/{plan_id}/progress", json={
        "dialogue_id": first_dialogue,
    }, headers={"x-openid": "progress_user"})
    assert r.status_code == 200
    updated = r.json()
    assert updated["completed_dialogues"] >= 1
    assert updated["overall_progress"] > 0


def test_plan_get_by_id():
    # Generate
    r = client.post("/api/plan/generate", json={
        "overall_level": "A2", "weak_areas": [], "strong_areas": [],
    }, headers={"x-openid": "getid_user"})
    plan_id = r.json()["id"]

    # Get by id
    r = client.get(f"/api/plan/{plan_id}", headers={"x-openid": "getid_user"})
    assert r.status_code == 200
    assert r.json()["id"] == plan_id


def test_plan_get_by_id_wrong_user():
    r = client.post("/api/plan/generate", json={
        "overall_level": "A2", "weak_areas": [], "strong_areas": [],
    }, headers={"x-openid": "owner_user"})
    plan_id = r.json()["id"]

    # Different user cannot access
    r = client.get(f"/api/plan/{plan_id}", headers={"x-openid": "other_user"})
    assert r.status_code == 404
