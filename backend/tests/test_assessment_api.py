"""Tests for the assessment API endpoints."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_assessment_start_returns_question():
    r = client.post("/api/assessment/start")
    assert r.status_code == 200
    data = r.json()
    assert "assessment_id" in data
    assert "first_question" in data
    q = data["first_question"]
    assert "id" in q
    assert "type" in q
    assert "content" in q


def test_assessment_answer_flow():
    # Start
    r = client.post("/api/assessment/start")
    data = r.json()
    aid = data["assessment_id"]
    qid = data["first_question"]["id"]

    # Answer
    r = client.post("/api/assessment/answer", json={
        "assessment_id": aid,
        "question_id": qid,
        "answer_index": 0,
        "time_spent": 5000,
    })
    assert r.status_code == 200
    ans = r.json()
    assert "is_correct" in ans
    assert "next_question" in ans


def test_assessment_complete_returns_result():
    # Start
    r = client.post("/api/assessment/start")
    data = r.json()
    aid = data["assessment_id"]
    qid = data["first_question"]["id"]

    # Answer a few questions
    for _ in range(3):
        r = client.post("/api/assessment/answer", json={
            "assessment_id": aid,
            "question_id": qid,
            "answer_index": 0,
            "time_spent": 3000,
        })
        next_q = r.json().get("next_question")
        if next_q:
            qid = next_q["id"]

    # Complete
    r = client.post("/api/assessment/complete", json={"assessment_id": aid})
    assert r.status_code == 200
    result = r.json()
    assert "overall_level" in result
    assert "ability_score" in result
    assert "dimensions" in result
    assert "recommendations" in result


def test_assessment_complete_saves_history():
    # Start and complete
    r = client.post("/api/assessment/start")
    aid = r.json()["assessment_id"]
    qid = r.json()["first_question"]["id"]

    client.post("/api/assessment/answer", json={
        "assessment_id": aid, "question_id": qid,
        "answer_index": 0, "time_spent": 2000,
    })
    client.post("/api/assessment/complete", json={"assessment_id": aid})

    # History should have at least one entry
    r = client.get("/api/assessment/history")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


def test_assessment_invalid_session():
    r = client.post("/api/assessment/answer", json={
        "assessment_id": "nonexistent",
        "question_id": "q1",
        "answer_index": 0,
    })
    assert r.status_code == 404
