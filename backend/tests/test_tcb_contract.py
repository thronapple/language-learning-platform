from app.infra.tcb_client import TCBClient


class DummySettings:
    tcb_env_id = "env-123"
    tcb_secret_id = "sid"
    tcb_secret_key = "skey"
    tcb_token = None
    tcb_region = "ap-shanghai"


def test_tcb_add_document_contract(monkeypatch):
    client = TCBClient.from_settings(DummySettings)
    recorded = {}

    def fake_request(action, payload):
        recorded["action"] = action
        recorded["payload"] = payload
        return {"_id": "abc123"}

    monkeypatch.setattr(client, "_request", fake_request)
    item = {"word": "hello"}
    new_id = client.add_document("vocab", item)
    assert new_id == "abc123"
    assert recorded["action"] == "CommonServiceAPI"
    p = recorded["payload"]
    assert p["EnvId"] == "env-123"
    assert p["Service"] == "database"
    assert p["Action"] == "AddDocument"
    assert p["Data"]["CollectionName"] == "vocab"
    assert p["Data"]["Document"] == item


def test_tcb_query_contract(monkeypatch):
    client = TCBClient.from_settings(DummySettings)
    recorded = {}

    def fake_request(action, payload):
        recorded["action"] = action
        recorded["payload"] = payload
        return {"Documents": [{"_id": "1", "word": "hello"}], "Total": 1}

    monkeypatch.setattr(client, "_request", fake_request)
    filters = {"user_id": "u1"}
    docs, total = client.query("vocab", filters, limit=10, offset=0)
    assert total == 1
    assert docs[0]["id"] == "1"
    p = recorded["payload"]
    assert p["Action"] == "QueryDocuments"
    assert p["Data"]["Filter"] == filters
    assert p["Data"]["Limit"] == 10
    assert p["Data"]["Offset"] == 0

