"""
FastAPI dependencies for authentication and common functionality.
"""
from fastapi import HTTPException, Request
from .infra.jwt_utils import verify_token


def _extract_openid(request: Request) -> str | None:
    """Extract openid from JWT Bearer token or legacy x-openid header."""
    # 1. Try JWT token from Authorization header
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        openid = verify_token(token)
        if openid:
            return openid

    # 2. Fallback: x-openid header (legacy, for backward compatibility)
    return getattr(request.state, "openid", None)


def get_current_user_openid(request: Request) -> str:
    """
    Extract and validate the user's openid from JWT token or request state.

    Raises:
        HTTPException: 401 if openid is missing or invalid
    """
    openid = _extract_openid(request)
    if not openid:
        raise HTTPException(
            status_code=401,
            detail="Authentication required: missing or invalid token"
        )
    return openid


def get_optional_user_openid(request: Request) -> str | None:
    """
    Extract the user's openid without requiring authentication.
    Returns None for anonymous users.
    """
    return _extract_openid(request)
