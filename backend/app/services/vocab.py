from __future__ import annotations

from datetime import datetime, timedelta, timezone
from ..schemas.vocab import VocabAddRequest, VocabItem
from ..repositories.interfaces import Repository


class VocabService:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    def add(self, payload: VocabAddRequest, user_id: str) -> None:
        doc = {
            "word": payload.word,
            "meaning": payload.meaning,
            "phonetic": payload.phonetic,
            "srs_level": 0,
            "next_review_at": None,
            "user_id": user_id,
        }
        self.repo.put("vocab", doc)

    def list(self, page: int, page_size: int, user_id: str) -> tuple[list[VocabItem], int]:
        offset = (page - 1) * page_size
        docs, total = self.repo.query("vocab", {"user_id": user_id}, limit=page_size, offset=offset)
        items = [VocabItem(**d) for d in docs]
        return items, total

    def remove(self, word: str, user_id: str) -> None:
        docs, total = self.repo.query("vocab", {"word": word, "user_id": user_id}, limit=1, offset=0)
        if not total:
            return
        doc_id = docs[0]["id"]
        self.repo.delete("vocab", doc_id)

    def review(self, user_id: str, word: str, rating: str) -> VocabItem:
        docs, total = self.repo.query("vocab", {"word": word, "user_id": user_id}, limit=1, offset=0)
        if not total:
            # create if missing
            self.add(VocabAddRequest(word=word), user_id=user_id)
            docs, total = self.repo.query("vocab", {"word": word, "user_id": user_id}, limit=1, offset=0)
        doc = docs[0]
        level = int(doc.get("srs_level") or 0)

        def next_time(lv: int) -> datetime:
            # simple schedule: 0->now+10m, 1->1d, 2->2d, 3->4d, 4->7d, 5->15d, 6+->30d
            if lv <= 0:
                return now + timedelta(minutes=10)
            mapping = {1: 1, 2: 2, 3: 4, 4: 7, 5: 15}
            days = mapping.get(lv, 30)
            return now + timedelta(days=days)

        now = datetime.now(timezone.utc)
        if rating == "again":
            level = max(level - 1, 0)
        elif rating == "hard":
            level = max(level, 0)
        elif rating == "good":
            level = min(level + 1, 10)
        elif rating == "easy":
            level = min(level + 2, 10)
        else:
            # unknown rating keeps level
            level = level

        nra = next_time(level).isoformat()
        doc.update({"srs_level": level, "next_review_at": nra})
        # ensure id persists
        self.repo.put("vocab", doc)
        return VocabItem(**doc)

    def due(self, user_id: str, before: datetime, page: int, page_size: int) -> tuple[list[VocabItem], int]:
        # Use database-level filtering for better performance
        offset = (page - 1) * page_size
        date_filters = {"next_review_at": {"lte": before.isoformat()}}

        docs, total = self.repo.query_with_date_filters(
            "vocab",
            filters={"user_id": user_id},
            date_filters=date_filters,
            limit=page_size,
            offset=offset
        )

        items = [VocabItem(**d) for d in docs]
        return items, total
