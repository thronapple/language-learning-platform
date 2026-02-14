from pydantic import BaseModel


class CreateIntentRequest(BaseModel):
    plan: str
    price: float


class OkResponse(BaseModel):
    ok: bool = True

