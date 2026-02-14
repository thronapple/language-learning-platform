from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..repositories.interfaces import Repository


class EventsService:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    def track(self, user_id: str, event: str, props: dict | None, ts: str | None = None) -> None:
        when = ts or datetime.now(timezone.utc).isoformat()
        doc = {"user_id": user_id, "event": event, "props": props or {}, "ts": when}
        self.repo.put("events", doc)

