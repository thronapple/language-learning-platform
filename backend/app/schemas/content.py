from typing import List, Literal, Optional

from pydantic import BaseModel


class ContentItem(BaseModel):
    id: str
    type: Literal["sentence", "dialog", "word"]
    tags: List[str] = []
    level: Optional[str] = None
    text: str
    audio_url: Optional[str] = None
    segments: List[str] = []
    segments_audio: Optional[List[str]] = None


class ContentListResponse(BaseModel):
    items: List[ContentItem]
    total: int
