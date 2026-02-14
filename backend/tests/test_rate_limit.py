"""Tests for rate limiting middleware."""
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_import_rate_limit_per_minute():
    """Test import endpoint respects per-minute rate limit."""
    # Should allow 5 requests per minute
    for i in range(5):
        resp = client.post(
            "/import",
            json={"type": "text", "payload": f"Test sentence {i}."},
            headers={"x-openid": "test_user_rate_limit"}
        )
        assert resp.status_code in [200, 401]  # 200 if auth passes, 401 if no auth

    # 6th request should be rate limited
    resp = client.post(
        "/import",
        json={"type": "text", "payload": "Test sentence 6."},
        headers={"x-openid": "test_user_rate_limit"}
    )
    assert resp.status_code == 429
    data = resp.json()
    assert data["detail"]["error"] == "RATE_LIMIT_EXCEEDED"
    assert "per_minute" in data["detail"]["limits"]


def test_export_rate_limit_stricter():
    """Test export endpoint has stricter rate limit (2/min)."""
    # Should allow 2 requests per minute
    for i in range(2):
        resp = client.post(
            "/export/longshot",
            json={"contentId": f"test_{i}"},
            headers={"x-openid": "test_user_export"}
        )
        assert resp.status_code in [200, 401, 404]

    # 3rd request should be rate limited
    resp = client.post(
        "/export/longshot",
        json={"contentId": "test_3"},
        headers={"x-openid": "test_user_export"}
    )
    assert resp.status_code == 429


def test_rate_limit_headers_present():
    """Test rate limit headers are included in response."""
    resp = client.post(
        "/import",
        json={"type": "text", "payload": "Test."},
        headers={"x-openid": "test_user_headers"}
    )

    # Check rate limit headers exist
    assert "x-ratelimit-limit-minute" in resp.headers
    assert "x-ratelimit-limit-day" in resp.headers
    assert "x-ratelimit-remaining-minute" in resp.headers
    assert "x-ratelimit-remaining-day" in resp.headers

    # Verify import limits
    assert resp.headers["x-ratelimit-limit-minute"] == "5"
    assert resp.headers["x-ratelimit-limit-day"] == "50"


def test_rate_limit_per_user_isolation():
    """Test rate limits are isolated per user."""
    # User 1 makes 5 requests
    for i in range(5):
        resp = client.post(
            "/import",
            json={"type": "text", "payload": f"User1 {i}."},
            headers={"x-openid": "user_1"}
        )
        assert resp.status_code in [200, 401]

    # User 1 is now rate limited
    resp = client.post(
        "/import",
        json={"type": "text", "payload": "User1 extra."},
        headers={"x-openid": "user_1"}
    )
    assert resp.status_code == 429

    # But User 2 can still make requests
    resp = client.post(
        "/import",
        json={"type": "text", "payload": "User2 first."},
        headers={"x-openid": "user_2"}
    )
    assert resp.status_code in [200, 401]  # Not rate limited


def test_no_rate_limit_on_other_endpoints():
    """Test endpoints without rate limits work normally."""
    # Health check should not be rate limited
    for i in range(10):
        resp = client.get("/health")
        assert resp.status_code == 200

    # Auth endpoint should not be rate limited
    for i in range(10):
        resp = client.post("/auth/me", json={"code": f"code_{i}"})
        assert resp.status_code == 200
