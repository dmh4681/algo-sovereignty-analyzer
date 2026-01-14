"""Custom exception classes for the Algorand Sovereignty Analyzer API."""

from typing import Optional, Dict, Any


class ApiException(Exception):
    """Base exception class for API errors with structured response support."""

    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        self.details = details
        super().__init__(detail)


class ValidationException(ApiException):
    """Exception for validation errors (400 Bad Request)."""

    def __init__(
        self,
        detail: str = "Invalid request data",
        error_code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=400,
            detail=detail,
            error_code=error_code,
            details=details
        )


class NotFoundException(ApiException):
    """Exception for resource not found errors (404 Not Found)."""

    def __init__(
        self,
        detail: str = "Resource not found",
        error_code: str = "NOT_FOUND",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=404,
            detail=detail,
            error_code=error_code,
            details=details
        )


class ExternalApiException(ApiException):
    """Exception for external API failures (502 Bad Gateway)."""

    def __init__(
        self,
        detail: str = "External service unavailable",
        error_code: str = "EXTERNAL_API_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=502,
            detail=detail,
            error_code=error_code,
            details=details
        )


class RateLimitException(ApiException):
    """Exception for rate limit errors (429 Too Many Requests)."""

    def __init__(
        self,
        detail: str = "Too many requests",
        error_code: str = "RATE_LIMIT_EXCEEDED",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            status_code=429,
            detail=detail,
            error_code=error_code,
            details=details
        )
