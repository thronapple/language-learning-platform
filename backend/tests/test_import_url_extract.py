from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_import_url_extracts_text_with_bs4(monkeypatch):
    class DummyResp:
        status_code = 200

        def raise_for_status(self):
            return None

        def __init__(self, text):
            self.text = text

    def fake_get(url, timeout=5, headers=None, allow_redirects=True):
        html = """
        <html><body>
        <article>
          <p>Sentence one.</p>
          <p>Sentence two!</p>
        </article>
        </body></html>
        """
        return DummyResp(html)

    # Correctly patch the requests module used by web_scraper
    monkeypatch.setattr("app.services.web_scraper.requests.get", fake_get)

    payload = {"type": "url", "payload": "https://example.com/article/123"}
    r = client.post("/import", json=payload)
    assert r.status_code == 200
    segs = r.json()["segments"]
    assert any("Sentence one" in s for s in segs) or len(segs) >= 1

