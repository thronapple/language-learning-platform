from typing import List, Optional
from pydantic import BaseModel


class VocabAddRequest(BaseModel):
    word: str
    meaning: Optional[str] = None
    phonetic: Optional[str] = None


class VocabItem(BaseModel):
    word: str
    meaning: Optional[str] = None
    phonetic: Optional[str] = None
    srs_level: Optional[int] = 0
    next_review_at: Optional[str] = None


class VocabListResponse(BaseModel):
    items: List[VocabItem]
    total: int



class VocabReviewRequest(BaseModel):
    word: str
    rating: str  # again|hard|good|easy


class VocabReviewResponse(BaseModel):
    item: VocabItem
