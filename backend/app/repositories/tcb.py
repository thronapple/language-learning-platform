from ..infra.tcb_client import TCBClient


class TCBRepository:
    """CloudBase repository delegating to TCB client.

    Methods should enforce user scoping (openid) at the query layer where applicable.
    """

    def __init__(self, client: TCBClient) -> None:
        self.client = client

    def get(self, collection: str, id: str) -> dict | None:
        doc = self.client.get_document(collection, id)
        if not doc:
            return None
        # normalize _id to id
        if "_id" in doc and "id" not in doc:
            doc = {**doc, "id": doc["_id"]}
        return doc

    def put(self, collection: str, item: dict) -> str:
        return self.client.add_document(collection, item)

    def delete(self, collection: str, id: str) -> bool:
        return self.client.delete_document(collection, id)

    def query(self, collection: str, filters: dict | None, limit: int, offset: int) -> tuple[list[dict], int]:
        docs, total = self.client.query(collection, filters, limit, offset)
        # normalize ids
        norm = []
        for d in docs:
            if "_id" in d and "id" not in d:
                d = {**d, "id": d["_id"]}
            norm.append(d)
        return norm, total
