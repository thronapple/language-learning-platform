import time
import uuid
import logging
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable

logger = logging.getLogger(__name__)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add request IDs and attach user context to requests.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        setattr(request.state, "request_id", request_id)

        # Attach openid to state if provided by client
        openid = request.headers.get("x-openid")
        if openid:
            setattr(request.state, "openid", openid)

        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request/response logging and performance monitoring.
    """

    def __init__(self, app, log_level: str = "INFO"):
        super().__init__(app)
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        # Extract request context
        request_id = getattr(request.state, "request_id", "unknown")
        openid = getattr(request.state, "openid", None)

        # Log request start
        logger.log(
            self.log_level,
            "Request started",
            extra={
                "request_id": request_id,
                "user_id": openid or "anonymous",
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "user_agent": request.headers.get("user-agent", ""),
                "client_ip": self._get_client_ip(request),
            }
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time

            # Log successful response
            logger.log(
                self.log_level,
                "Request completed",
                extra={
                    "request_id": request_id,
                    "user_id": openid or "anonymous",
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "process_time_ms": round(process_time * 1000, 2),
                    "response_size": response.headers.get("content-length"),
                }
            )

            # Add performance headers
            response.headers["x-process-time"] = str(round(process_time * 1000, 2))

            return response

        except Exception as e:
            # Calculate processing time for failed requests
            process_time = time.time() - start_time

            # Log error
            logger.error(
                "Request failed",
                extra={
                    "request_id": request_id,
                    "user_id": openid or "anonymous",
                    "method": request.method,
                    "path": request.url.path,
                    "process_time_ms": round(process_time * 1000, 2),
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True
            )

            # Re-raise the exception
            raise

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check common headers for real IP
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fallback to client address
        if hasattr(request, "client") and request.client:
            return request.client.host

        return "unknown"


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware for collecting application metrics.
    """

    def __init__(self, app):
        super().__init__(app)
        self.request_count = 0
        self.total_request_time = 0.0
        self.error_count = 0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        self.request_count += 1

        try:
            response = await call_next(request)

            # Track timing
            process_time = time.time() - start_time
            self.total_request_time += process_time

            # Track errors (4xx and 5xx status codes)
            if response.status_code >= 400:
                self.error_count += 1

            # Log metrics periodically (every 100 requests)
            if self.request_count % 100 == 0:
                avg_response_time = self.total_request_time / self.request_count
                error_rate = (self.error_count / self.request_count) * 100

                logger.info(
                    "Application metrics",
                    extra={
                        "total_requests": self.request_count,
                        "avg_response_time_ms": round(avg_response_time * 1000, 2),
                        "error_count": self.error_count,
                        "error_rate_percent": round(error_rate, 2),
                    }
                )

            return response

        except Exception as e:
            self.error_count += 1
            raise


def add_middleware(app: FastAPI) -> None:
    """
    Add all middleware to the FastAPI application.

    Middleware is added in reverse order - the last middleware added
    will be the first to process the request.
    """
    from .rate_limiter import RateLimitMiddleware

    # Add in reverse order of execution
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(LoggingMiddleware, log_level="INFO")
    app.add_middleware(RateLimitMiddleware)  # Rate limiting before auth
    app.add_middleware(RequestIdMiddleware)
