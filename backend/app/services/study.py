from ..schemas.study import SaveProgressRequest
from ..repositories.interfaces import Repository
from datetime import datetime, timezone


class StudyService:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    def save_progress(self, payload: SaveProgressRequest, user_id: str) -> None:
        doc = {
            "contentId": payload.contentId,
            "secs": payload.secs,
            "step": payload.step,
            "user_id": user_id,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        self.repo.put("progress", doc)
