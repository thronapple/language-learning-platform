from datetime import datetime, timezone
from ..schemas.billing import CreateIntentRequest
from ..repositories.interfaces import Repository


class BillingService:
    def __init__(self, repo: Repository | None = None) -> None:
        self.repo = repo

    def create_intent(self, payload: CreateIntentRequest, user_id: str | None = None) -> None:
        if not self.repo:
            return None
        doc = {
            "user_id": user_id,
            "plan": payload.plan,
            "price": float(payload.price),
            "status": "intent",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.repo.put("orders", doc)
        return None
