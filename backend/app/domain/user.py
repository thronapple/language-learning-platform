from dataclasses import dataclass
from typing import Optional


@dataclass
class UserProfile:
    openid: str
    nick: Optional[str] = None
    avatar: Optional[str] = None
    pro_until: Optional[str] = None

