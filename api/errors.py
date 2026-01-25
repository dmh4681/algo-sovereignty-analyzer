"""Custom exception classes for the Algorand Sovereignty Analyzer API.

This module provides a hierarchy of exception classes for consistent error handling:

- ApiException: Base class for all API errors
- ValidationException: 400 Bad Request - Invalid input data
- NotFoundException: 404 Not Found - Resource doesn't exist
- ExternalApiException: 502 Bad Gateway - Upstream API failures
- RateLimitException: 429 Too Many Requests - Rate limiting
- TimeoutException: 504 Gateway Timeout - External API timeouts
- ServiceUnavailableException: 503 Service Unavailable - Temporary outage
- AlgorandApiException: 502 - Specific to Algorand node failures
- PriceApiException: 502 - Specific to price feed failures

All exceptions include:
- status_code: HTTP status code to return
- error_code: Machine-readable error identifier
- detail: Human-readable error message
- details: Additional context (optional dict)
"""

from typing import Optional, Dict, Any


class ApiException(Exception):
    """Base exception class for API errors with structured response support.

    All API exceptions inherit from this class to ensure consistent error
    response format with correlation IDs and structured details.
    """

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
        self.details = details or {}
        super().__init__(detail)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dict for JSON serialization."""
        return {
            "code": self.error_code,
            "message": self.detail,
            "details": self.details
        }


class ValidationException(ApiException):
    """Exception for validation errors (400 Bad Request).

    Use for:
    - Invalid wallet address format
    - Missing required fields
    - Invalid parameter values
    - Schema validation failures
    """

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
    """Exception for resource not found errors (404 Not Found).

    Use for:
    - Wallet address not found on chain
    - Asset ID doesn't exist
    - History data not found
    - Correction record not found
    """

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
    """Exception for external API failures (502 Bad Gateway).

    Generic exception for any upstream API failure. Consider using
    more specific exceptions like AlgorandApiException or PriceApiException.
    """

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
    """Exception for rate limit errors (429 Too Many Requests).

    Use when:
    - Client exceeds request rate limits
    - External API returns 429
    """

    def __init__(
        self,
        detail: str = "Too many requests",
        error_code: str = "RATE_LIMIT_EXCEEDED",
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None
    ):
        if retry_after and details is None:
            details = {}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        super().__init__(
            status_code=429,
            detail=detail,
            error_code=error_code,
            details=details
        )
        self.retry_after = retry_after


class TimeoutException(ApiException):
    """Exception for timeout errors (504 Gateway Timeout).

    Use when:
    - External API request times out
    - Database query times out
    - Blockchain RPC times out
    """

    def __init__(
        self,
        detail: str = "Request timed out",
        error_code: str = "TIMEOUT",
        details: Optional[Dict[str, Any]] = None,
        service: Optional[str] = None
    ):
        if service:
            if details is None:
                details = {}
            details["service"] = service
        super().__init__(
            status_code=504,
            detail=detail,
            error_code=error_code,
            details=details
        )


class ServiceUnavailableException(ApiException):
    """Exception for temporary service outages (503 Service Unavailable).

    Use when:
    - Service is temporarily down for maintenance
    - Circuit breaker is open
    - Dependent service is unavailable
    """

    def __init__(
        self,
        detail: str = "Service temporarily unavailable",
        error_code: str = "SERVICE_UNAVAILABLE",
        details: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None
    ):
        if retry_after:
            if details is None:
                details = {}
            details["retry_after_seconds"] = retry_after
        super().__init__(
            status_code=503,
            detail=detail,
            error_code=error_code,
            details=details
        )
        self.retry_after = retry_after


class AlgorandApiException(ExternalApiException):
    """Exception for Algorand node/API failures.

    Use for:
    - AlgoNode connection failures
    - Indexer query failures
    - Consensus data unavailable
    """

    def __init__(
        self,
        detail: str = "Algorand network unavailable",
        error_code: str = "ALGORAND_API_ERROR",
        details: Optional[Dict[str, Any]] = None,
        is_timeout: bool = False
    ):
        if is_timeout:
            error_code = "ALGORAND_API_TIMEOUT"
            if details is None:
                details = {}
            details["is_timeout"] = True
        super().__init__(
            detail=detail,
            error_code=error_code,
            details=details
        )


class PriceApiException(ExternalApiException):
    """Exception for price feed API failures.

    Use for:
    - CoinGecko rate limiting or failures
    - Vestige API unavailable
    - Yahoo Finance errors
    - Coinbase API errors

    Note: Price failures often have fallback logic, so this exception
    should only be raised when all fallbacks fail.
    """

    def __init__(
        self,
        detail: str = "Price data unavailable",
        error_code: str = "PRICE_API_ERROR",
        details: Optional[Dict[str, Any]] = None,
        asset: Optional[str] = None,
        source: Optional[str] = None
    ):
        if details is None:
            details = {}
        if asset:
            details["asset"] = asset
        if source:
            details["source"] = source
        super().__init__(
            detail=detail,
            error_code=error_code,
            details=details
        )


class AnalysisException(ApiException):
    """Exception for wallet analysis failures.

    Use when:
    - Analysis logic fails unexpectedly
    - LP parsing fails
    - Classification fails
    """

    def __init__(
        self,
        detail: str = "Wallet analysis failed",
        error_code: str = "ANALYSIS_FAILED",
        details: Optional[Dict[str, Any]] = None,
        address: Optional[str] = None
    ):
        if address:
            if details is None:
                details = {}
            # Truncate address for privacy
            details["address"] = f"{address[:8]}...{address[-6:]}" if len(address) > 14 else address
        super().__init__(
            status_code=500,
            detail=detail,
            error_code=error_code,
            details=details
        )
