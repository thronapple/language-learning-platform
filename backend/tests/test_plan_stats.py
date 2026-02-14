from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from app.main import app, repo


client = TestClient(app)


def test_plan_stats_empty_returns_zero():
    headers = {"x-openid": "ps_u0"}
    r = client.get("/plan/stats", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["secsToday"] == 0
    assert data["streak"] == 0


def test_plan_stats_counts_today_and_streak():
    user = "ps_u1"
    headers = {"x-openid": user}
    # Insert progress docs directly via repo with ts days
    now = datetime.now(timezone.utc)
    today = now.isoformat()
    yesterday = (now - timedelta(days=1)).isoformat()
    two_days_ago = (now - timedelta(days=2)).isoformat()

    repo.put("progress", {"user_id": user, "contentId": "c1", "secs": 100, "step": "learning", "ts": today})
    repo.put("progress", {"user_id": user, "contentId": "c2", "secs": 50, "step": "learning", "ts": yesterday})
    # gap at two_days_ago -> streak should be 2 (today + yesterday)

    r = client.get("/plan/stats", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert data["secsToday"] >= 100
    assert data["streak"] == 2

