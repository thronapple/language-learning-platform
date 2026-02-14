"""
FastAPI dependencies for authentication and common functionality.
"""
from fastapi import Depends, HTTPException, Request


def get_current_user_openid(request: Request) -> str:
    """
    Extract and validate the user's openid from the request state.

    This dependency should be used for all authenticated endpoints.
    The openid is set by the AuthMiddleware after validating the x-openid header.

    Raises:
        HTTPException: 401 if openid is missing or invalid

    Returns:
        str: The validated user openid
    """
    openid = getattr(request.state, "openid", None)
    if not openid:
        raise HTTPException(
            status_code=401,
            detail="Authentication required: missing or invalid x-openid header"
        )
    return openid


def get_optional_user_openid(request: Request) -> str | None:
    """
    Extract the user's openid from the request state without requiring authentication.

    This dependency can be used for endpoints that work for both authenticated
    and anonymous users.

    Returns:
        str | None: The user openid if present, None otherwise
    """
    return getattr(request.state, "openid", None)