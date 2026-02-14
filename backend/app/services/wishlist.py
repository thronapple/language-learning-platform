from datetime import datetime, timezone
from ..schemas.wishlist import WishlistRequest
from ..repositories.interfaces import Repository


class WishlistService:
    def __init__(self, repo: Repository | None = None) -> None:
        self.repo = repo

    def submit(self, payload: WishlistRequest, user_id: str | None = None) -> None:
        if not self.repo:
            return None
        doc = {
            "user_id": user_id,
            "plan": payload.plan,
            "price_point": float(payload.price_point) if payload.price_point is not None else None,
            "contactType": payload.contactType,
            "contact": payload.contact,
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        self.repo.put("wishlists", doc)
        return None
