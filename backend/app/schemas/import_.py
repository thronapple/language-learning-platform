from typing import List, Literal
from pydantic import BaseModel


class ImportRequest(BaseModel):
    type: Literal["text", "url"]
    payload: str


class ImportResponse(BaseModel):
    id: str
    type: Literal["text", "url"]
    segments: List[str]

