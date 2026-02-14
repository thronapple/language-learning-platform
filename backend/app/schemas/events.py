from typing import Any, Optional
from pydantic import BaseModel


class TrackEventRequest(BaseModel):
    event: str
    props: Optional[dict[str, Any]] = None
    ts: Optional[str] = None


class OkResponse(BaseModel):
    ok: bool = True

