from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_export_longshot_returns_path():
    r = client.post("/export/longshot", json={"contentId": "demo"})
    assert r.status_code == 200
    url = r.json()["url"]
    assert url.endswith(".png")
    assert "exports/longshot_demo.png" in url

