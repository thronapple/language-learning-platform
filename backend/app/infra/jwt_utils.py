"""JWT token utilities for authentication."""
import jwt
from datetime import datetime, timezone, timedelta
from .config import settings


def create_token(openid: str) -> str:
    """Create a JWT token for the given openid."""
    payload = {
        "sub": openid,
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def verify_token(token: str) -> str | None:
    """Verify a JWT token and return the openid, or None if invalid."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return payload.get("sub")
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def refresh_token(token: str) -> tuple[str | None, str | None]:
    """
    Refresh a JWT token if it's still valid or recently expired (within 7 days).
    Returns (new_token, openid) or (None, None) if refresh is not possible.
    """
    try:
        # Try normal verification first
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        openid = payload.get("sub")
        if openid:
            return create_token(openid), openid
    except jwt.ExpiredSignatureError:
        # Token expired — check if within refresh window (7 days)
        try:
            payload = jwt.decode(
                token, settings.jwt_secret, algorithms=["HS256"],
                options={"verify_exp": False},
            )
            exp = datetime.fromtimestamp(payload.get("exp", 0), tz=timezone.utc)
            now = datetime.now(timezone.utc)
            if now - exp < timedelta(days=7):
                openid = payload.get("sub")
                if openid:
                    return create_token(openid), openid
        except jwt.InvalidTokenError:
            pass
    except jwt.InvalidTokenError:
        pass
    return None, None
