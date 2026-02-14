from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class StubStorage:
    def upload_file(self, local, remote):
        return f"https://cdn.example.com/{remote}"


def test_export_uses_storage_if_present(monkeypatch):
    from app.services.export import ExportService
    from app.main import export_service as current_export_service
    # replace export_service with one that has storage
    new_service = ExportService(repo=None, storage=StubStorage())
    monkeypatch.setattr("app.main.export_service", new_service)
    r = client.post("/export/longshot", json={"contentId": "demo2"})
    assert r.status_code == 200
    url = r.json()["url"]
    assert url.startswith("https://cdn.example.com/")

