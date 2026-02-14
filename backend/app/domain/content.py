from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Content:
    id: str
    type: str  # sentence|dialog|word
    text: str
    level: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    audio_url: Optional[str] = None
    segments: List[str] = field(default_factory=list)

