from pydantic import BaseModel


class WishlistRequest(BaseModel):
    contactType: str  # wx|phone|email
    contact: str
    plan: str | None = None
    price_point: float | None = None


class OkResponse(BaseModel):
    ok: bool = True

