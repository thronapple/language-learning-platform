import uuid
from typing import Any
from datetime import datetime, timezone


class MemoryRepository:
    def __init__(self) -> None:
        # { collection: { id: item_dict } }
        self._db: dict[str, dict[str, dict]] = {}

    def _col(self, collection: str) -> dict[str, dict]:
        return self._db.setdefault(collection, {})

    def get(self, collection: str, id: str) -> dict | None:
        return self._col(collection).get(id)

    def put(self, collection: str, item: dict) -> str:
        col = self._col(collection)
        _id = item.get("id") or uuid.uuid4().hex
        item["id"] = _id
        col[_id] = dict(item)
        return _id

    def delete(self, collection: str, id: str) -> bool:
        col = self._col(collection)
        return col.pop(id, None) is not None

    def query(self, collection: str, filters: dict | None, limit: int, offset: int) -> tuple[list[dict], int]:
        col = self._col(collection)
        items = list(col.values())
        if filters:
            def match(it: dict) -> bool:
                for k, v in filters.items():
                    if v is None:
                        continue
                    if it.get(k) != v:
                        return False
                return True

            items = [it for it in items if match(it)]
        total = len(items)
        sliced = items[offset: offset + limit]
        return sliced, total

    def query_with_date_filters(
        self,
        collection: str,
        filters: dict | None = None,
        date_filters: dict | None = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[list[dict], int]:
        col = self._col(collection)
        items = list(col.values())

        # Apply regular filters
        if filters:
            def match(it: dict) -> bool:
                for k, v in filters.items():
                    if v is None:
                        continue
                    if it.get(k) != v:
                        return False
                return True
            items = [it for it in items if match(it)]

        # Apply date filters
        if date_filters:
            def match_date(it: dict) -> bool:
                for field, date_condition in date_filters.items():
                    field_value = it.get(field)
                    if not field_value:
                        continue

                    try:
                        # Parse the datetime string
                        if isinstance(field_value, str):
                            field_dt = datetime.fromisoformat(field_value)
                            if field_dt.tzinfo is None:
                                field_dt = field_dt.replace(tzinfo=timezone.utc)
                        else:
                            continue

                        # Check conditions
                        if "lte" in date_condition:
                            target_dt = date_condition["lte"]
                            if isinstance(target_dt, str):
                                target_dt = datetime.fromisoformat(target_dt)
                                if target_dt.tzinfo is None:
                                    target_dt = target_dt.replace(tzinfo=timezone.utc)
                            if not (field_dt <= target_dt):
                                return False

                        if "gte" in date_condition:
                            target_dt = date_condition["gte"]
                            if isinstance(target_dt, str):
                                target_dt = datetime.fromisoformat(target_dt)
                                if target_dt.tzinfo is None:
                                    target_dt = target_dt.replace(tzinfo=timezone.utc)
                            if not (field_dt >= target_dt):
                                return False

                    except (ValueError, TypeError):
                        continue

                return True

            items = [it for it in items if match_date(it)]

        total = len(items)
        sliced = items[offset: offset + limit]
        return sliced, total

