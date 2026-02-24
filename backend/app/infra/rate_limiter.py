"""
Rate limiting middleware for import/export operations.
"""
import time
import logging
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, JSONResponse
from typing import Callable

logger = logging.getLogger(__name__)


class RateLimitStore:
    """In-memory store for rate limiting counters."""

    def __init__(self):
        # Store: {user_id: {endpoint: [(timestamp, count)]}}
        self._store: Dict[str, Dict[str, list]] = defaultdict(lambda: defaultdict(list))

    def check_and_increment(
        self,
        user_id: str,
        endpoint: str,
        max_per_minute: int = 5,
        max_per_day: int = 50
    ) -> Tuple[bool, str]:
        """
        Check if request is within rate limits and increment counter.

        Returns:
            (allowed: bool, reason: str)
        """
        now = time.time()
        user_endpoints = self._store[user_id][endpoint]

        # Clean old entries (older than 24 hours)
        cutoff_day = now - 86400  # 24 hours
        user_endpoints[:] = [entry for entry in user_endpoints if entry[0] > cutoff_day]

        # Check daily limit
        daily_count = sum(count for ts, count in user_endpoints if ts > cutoff_day)
        if daily_count >= max_per_day:
            return False, f"Daily limit exceeded: {max_per_day}/day"

        # Check minute limit
        cutoff_minute = now - 60  # 1 minute
        minute_count = sum(count for ts, count in user_endpoints if ts > cutoff_minute)
        if minute_count >= max_per_minute:
            return False, f"Rate limit exceeded: {max_per_minute}/min"

        # Increment counter
        user_endpoints.append((now, 1))

        logger.debug(
            "Rate limit check passed",
            extra={
                "user_id": user_id,
                "endpoint": endpoint,
                "minute_count": minute_count + 1,
                "daily_count": daily_count + 1
            }
        )

        return True, ""

    def get_usage(self, user_id: str, endpoint: str) -> Dict[str, int]:
        """Get current usage stats for debugging."""
        now = time.time()
        user_endpoints = self._store[user_id][endpoint]

        cutoff_day = now - 86400
        cutoff_minute = now - 60

        daily_count = sum(count for ts, count in user_endpoints if ts > cutoff_day)
        minute_count = sum(count for ts, count in user_endpoints if ts > cutoff_minute)

        return {
            "minute_count": minute_count,
            "daily_count": daily_count
        }


# Global rate limit store
_rate_limit_store = RateLimitStore()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting specific endpoints.

    Configured per-endpoint with different limits for import/export operations.
    """

    # Rate limit configurations: {path: (max_per_minute, max_per_day)}
    RATE_LIMITS = {
        "/import": (5, 50),                   # 5 per minute, 50 per day
        "/export/longshot": (2, 20),           # 2 per minute, 20 per day
        "/auth/me": (10, 100),                 # 10 per minute, 100 per day
        "/auth/refresh": (10, 200),            # 10 per minute, 200 per day
        "/api/assessment/start": (5, 30),      # 5 per minute, 30 per day
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Only apply to configured endpoints
        path = request.url.path

        if path not in self.RATE_LIMITS:
            # No rate limit for this endpoint
            return await call_next(request)

        # Get user ID from request state (set by RequestIdMiddleware)
        user_id = getattr(request.state, "openid", None)

        if not user_id:
            # No user authentication - apply stricter IP-based limit
            user_id = self._get_client_ip(request)
            if not user_id:
                user_id = "anonymous"

        # Get rate limits for this endpoint
        max_per_minute, max_per_day = self.RATE_LIMITS[path]

        # Check rate limit
        allowed, reason = _rate_limit_store.check_and_increment(
            user_id=user_id,
            endpoint=path,
            max_per_minute=max_per_minute,
            max_per_day=max_per_day
        )

        if not allowed:
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "user_id": user_id,
                    "endpoint": path,
                    "reason": reason,
                    "ip": self._get_client_ip(request)
                }
            )

            # Get current usage for response headers
            usage = _rate_limit_store.get_usage(user_id, path)

            return JSONResponse(
                status_code=429,
                content={
                    "detail": {
                        "error": "RATE_LIMIT_EXCEEDED",
                        "message": reason,
                        "limits": {
                            "per_minute": max_per_minute,
                            "per_day": max_per_day
                        },
                        "current_usage": usage
                    }
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        usage = _rate_limit_store.get_usage(user_id, path)
        response.headers["x-ratelimit-limit-minute"] = str(max_per_minute)
        response.headers["x-ratelimit-limit-day"] = str(max_per_day)
        response.headers["x-ratelimit-remaining-minute"] = str(max(0, max_per_minute - usage["minute_count"]))
        response.headers["x-ratelimit-remaining-day"] = str(max(0, max_per_day - usage["daily_count"]))

        return response

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        if hasattr(request, "client") and request.client:
            return request.client.host

        return "unknown"
