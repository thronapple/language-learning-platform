from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_import_text_splits_sentences():
    payload = {"type": "text", "payload": "Hello! 你好。OK?"}
    r = client.post("/import", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data["id"]
    assert isinstance(data["segments"], list)
    assert len(data["segments"]) >= 2


def test_import_url_whitelist_allows_example():
    # Mock requests.get to avoid actual HTTP calls in tests
    with patch('app.services.web_scraper.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html><body><article>Sample content from example.com</article></body></html>'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        payload = {"type": "url", "payload": "https://example.com/a-b_c/d"}
        r = client.post("/import", json=payload)
        assert r.status_code == 200
        data = r.json()
        segs = data["segments"]
        assert len(segs) >= 1


def test_import_url_non_whitelist_rejected():
    payload = {"type": "url", "payload": "https://blocked.com/path"}
    r = client.post("/import", json=payload)
    # Should fail validation - domain not in whitelist
    assert r.status_code == 500  # ValidationError becomes 500
    data = r.json()
    assert "not allowed" in data["error"].lower() or "error" in data

