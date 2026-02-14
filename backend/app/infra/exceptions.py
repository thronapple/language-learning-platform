"""
Unified exception handling for the language learning platform.
"""
from typing import Optional


class ServiceError(Exception):
    """Base service error for all application-level exceptions."""

    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[dict] = None):
        self.message = message
        self.error_code = error_code or "SERVICE_ERROR"
        self.details = details or {}
        super().__init__(self.message)


class ExternalServiceError(ServiceError):
    """Error communicating with external services (WeChat API, TCB, etc.)."""

    def __init__(self, message: str, service_name: str, details: Optional[dict] = None):
        error_details = details.copy() if details else {}
        error_details["service"] = service_name
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            details=error_details
        )
        self.service_name = service_name


class ResourceNotFoundError(ServiceError):
    """Resource not found error."""

    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            message=f"{resource_type} not found: {resource_id}",
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id}
        )


class AuthenticationError(ServiceError):
    """Authentication related errors."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            error_code="AUTH_ERROR"
        )


class ValidationError(ServiceError):
    """Input validation errors."""

    def __init__(self, message: str, field: Optional[str] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field": field} if field else {}
        )


class RateLimitError(ServiceError):
    """Rate limit exceeded error."""

    def __init__(self, message: str, limits: Optional[dict] = None, usage: Optional[dict] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"limits": limits or {}, "usage": usage or {}}
        )