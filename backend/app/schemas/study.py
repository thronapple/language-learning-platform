from typing import Literal
from pydantic import BaseModel


class SaveProgressRequest(BaseModel):
    contentId: str
    secs: int
    step: Literal["new", "learning", "review"]


class OkResponse(BaseModel):
    ok: bool = True

