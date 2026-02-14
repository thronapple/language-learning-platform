from app.repositories.tcb import TCBRepository


class DummyTCBClient:
    def __init__(self):
        self.calls = []

    def get_document(self, collection, doc_id):
        self.calls.append(("get", collection, doc_id))
        return {"_id": doc_id, "word": "hello"}

    def add_document(self, collection, item):
        self.calls.append(("add", collection, item))
        return "id123"

    def delete_document(self, collection, doc_id):
        self.calls.append(("del", collection, doc_id))
        return True

    def query(self, collection, filters, limit, offset):
        self.calls.append(("query", collection, filters, limit, offset))
        return ([{"_id": "1", "word": "hi"}], 1)


def test_tcb_repository_delegates_to_client():
    client = DummyTCBClient()
    repo = TCBRepository(client)

    # get
    doc = repo.get("vocab", "abc")
    assert doc["id"] == "abc" or doc.get("_id") == "abc"

    # put
    new_id = repo.put("vocab", {"word": "hello"})
    assert new_id == "id123"

    # delete
    ok = repo.delete("vocab", "abc")
    assert ok is True

    # query
    docs, total = repo.query("vocab", {"user_id": "u1"}, limit=10, offset=0)
    assert total == 1
    assert isinstance(docs, list)

    # verify call sequence
    kinds = [c[0] for c in client.calls]
    assert set(kinds) == {"get", "add", "del", "query"}

