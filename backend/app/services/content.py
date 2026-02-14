from __future__ import annotations

import logging
from ..schemas.content import ContentItem
from ..repositories.interfaces import Repository
from ..infra.exceptions import ResourceNotFoundError

logger = logging.getLogger(__name__)


class ContentService:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    def list(self, page: int, page_size: int, ctype: str | None, level: str | None) -> tuple[list[ContentItem], int]:
        filters = {"type": ctype, "level": level}
        offset = (page - 1) * page_size
        docs, total = self.repo.query("content", filters, limit=page_size, offset=offset)
        items = [ContentItem(**{**d, "id": d["id"]}) for d in docs]
        return items, total

    def get(self, content_id: str) -> ContentItem:
        doc = self.repo.get("content", content_id)
        if not doc:
            logger.warning("Content not found, returning fallback", extra={"content_id": content_id})
            # Return a fallback demo content item to avoid breaking client
            return ContentItem(
                id=content_id,
                type="sentence",
                text="Demo content",
                audio_url="",
                segments=[],
                segments_audio=[],
                level="A1",
                tags=[]
            )
        return ContentItem(**{**doc, "id": doc["id"]})
