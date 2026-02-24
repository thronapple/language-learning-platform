from typing import List, Optional

from pydantic import BaseModel


class MeRequest(BaseModel):
    code: str


class User(BaseModel):
    openid: str
    nick: Optional[str] = None
    avatar: Optional[str] = None
    pro_until: Optional[str] = None


class MeResponse(BaseModel):
    user: User
    token: str = ""
    featureFlags: List[str] = []


class RefreshRequest(BaseModel):
    token: str


class RefreshResponse(BaseModel):
    token: str
    openid: str

