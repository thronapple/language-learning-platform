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
    Feeds into the global MetricsCollector for /metrics endpoint.
    """

    def __init__(self, app):
        super().__init__(app)
        from .metrics import metrics_collector
        self._collector = metrics_collector

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Feed into global collector
            openid = getattr(request.state, "openid", None)
            self._collector.record_request(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                response_time=process_time,
                user_id=openid,
            )

            # Log slow requests (>2s)
            if process_time > 2.0:
                logger.warning(
                    "Slow request detected",
                    extra={
                        "method": request.method,
                        "path": request.url.path,
                        "process_time_ms": round(process_time * 1000, 2),
                        "status_code": response.status_code,
                    }
                )

            return response

        except Exception as e:
            process_time = time.time() - start_time
            self._collector.record_request(
                method=request.method,
                path=request.url.path,
                status_code=500,
                response_time=process_time,
            )
            raise


class ErrorCaptureMiddleware(BaseHTTPMiddleware):
    """
    Catches unhandled exceptions and returns structured JSON error responses
    instead of raw 500 HTML. Logs full traceback for debugging.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.error(
                "Unhandled exception",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                exc_info=True,
            )
            from starlette.responses import JSONResponse as _JSONResponse
            return _JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "request_id": request_id,
                },
            )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security response headers to all responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


def add_middleware(app: FastAPI) -> None:
    """
    Add all middleware to the FastAPI application.

    Middleware is added in reverse order - the last middleware added
    will be the first to process the request.
    """
    from .rate_limiter import RateLimitMiddleware
    from .config import settings
    from fastapi.middleware.cors import CORSMiddleware

    # CORS — allow mini program and dev origins
    allowed_origins = [
        "https://servicewechat.com",  # WeChat Mini Program
    ]
    if settings.env == "dev":
        allowed_origins += ["http://localhost:*", "http://127.0.0.1:*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_origin_regex=r"https://.*\.tcloudbase\.com",  # CloudBase domains
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["x-request-id", "x-process-time"],
    )

    # Add in reverse order of execution
    # (first added = outermost = last to process request)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(ErrorCaptureMiddleware)
    app.add_middleware(MetricsMiddleware)
    app.add_middleware(LoggingMiddleware, log_level="INFO")
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestIdMiddleware)
