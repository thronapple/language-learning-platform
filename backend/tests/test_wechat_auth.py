import types
from app.services.auth import AuthService
from app.repositories.memory import MemoryRepository


class DummyClient:
    def __init__(self, openid: str | None):
        self._openid = openid

    def exchange_code(self, code: str) -> dict:
        if self._openid:
            return {"openid": self._openid}
        return {"errcode": 40029, "errmsg": "invalid code"}


def test_auth_service_prefers_wechat_when_available(monkeypatch):
    repo = MemoryRepository()
    client = DummyClient("wx_123")
    service = AuthService(repo, client)
    openid = service.exchange_code_for_openid("abc")
    assert openid == "wx_123"


def test_auth_service_falls_back_to_mock_when_error():
    repo = MemoryRepository()
    client = DummyClient(None)
    service = AuthService(repo, client)
    openid = service.exchange_code_for_openid("abc123456")
    assert openid.startswith("mock_")

