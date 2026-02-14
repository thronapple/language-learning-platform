from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Tuple

from ..repositories.interfaces import Repository


class PlanService:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    def stats(self, user_id: str) -> dict:
        docs, _ = self.repo.query("progress", {"user_id": user_id}, limit=10000, offset=0)
        # secs today
        now = datetime.now(timezone.utc)
        today = now.date()
        secs_today = 0
        days_with_secs: set[datetime.date] = set()

        def parse_ts(s: str | None) -> datetime | None:
            if not s:
                return None
            try:
                dt = datetime.fromisoformat(s)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                return None

        for d in docs:
            ts = parse_ts(d.get("ts"))
            if not ts:
                continue
            if int(d.get("secs") or 0) > 0:
                days_with_secs.add(ts.date())
            if ts.date() == today:
                secs_today += int(d.get("secs") or 0)

        # streak: count consecutive days starting today going backwards
        streak = 0
        cur = today
        while cur in days_with_secs:
            streak += 1
            cur = cur - timedelta(days=1)

        return {"secsToday": secs_today, "streak": streak}

