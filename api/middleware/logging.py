"""Request/Response logging middleware for the Algorand Sovereignty Analyzer API.

This module provides structured JSON logging for all API requests including:
- Unique request IDs (UUID4) for correlation
- Request timing (duration in milliseconds)
- Anonymized wallet addresses for privacy
- Error tracking with exception types

Log Format:
    All logs are output as JSON objects with the following fields:
    - timestamp: ISO 8601 UTC timestamp
    - request_id: Unique identifier for request correlation
    - event: 'request', 'response', or 'error'
    - method: HTTP method (GET, POST, etc.)
    - path: Request path (with anonymized addresses)
    - status: HTTP status code (response/error only)
    - duration_ms: Request duration in milliseconds
    - error_type: Exception class name (error only)

Privacy:
    Wallet addresses in paths and query params are automatically hashed
    using SHA256, with only the first 8 characters of the hash logged.
"""

import hashlib
import json
import logging
import os
import time
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Context variable to store request_id for access across the request lifecycle
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def get_current_request_id() -> Optional[str]:
    """Get the current request ID from context."""
    return request_id_var.get()


def anonymize_address(address: str) -> str:
    """
    Anonymize a wallet address by returning first 8 chars of its SHA256 hash.

    Args:
        address: The wallet address to anonymize

    Returns:
        First 8 characters of the SHA256 hash of the address
    """
    return hashlib.sha256(address.encode()).hexdigest()[:8]


def anonymize_query_params(query_string: str) -> str:
    """
    Anonymize wallet addresses in query parameters.

    Args:
        query_string: The raw query string from the request

    Returns:
        Query string with wallet addresses anonymized
    """
    if not query_string:
        return ""

    # Parse and anonymize address parameters
    parts = []
    for param in query_string.split("&"):
        if "=" in param:
            key, value = param.split("=", 1)
            # Algorand addresses are 58 characters
            if key.lower() in ("address", "wallet") and len(value) == 58:
                value = anonymize_address(value)
            parts.append(f"{key}={value}")
        else:
            parts.append(param)

    return "&".join(parts)


def anonymize_path(path: str) -> str:
    """
    Anonymize wallet addresses in URL paths.

    Args:
        path: The request path

    Returns:
        Path with wallet addresses anonymized
    """
    # Split path and check each segment for address-like patterns
    segments = path.split("/")
    anonymized_segments = []

    for segment in segments:
        # Algorand addresses are 58 characters, base32 alphabet
        if len(segment) == 58 and segment.isalnum():
            anonymized_segments.append(anonymize_address(segment))
        else:
            anonymized_segments.append(segment)

    return "/".join(anonymized_segments)


def configure_logger() -> logging.Logger:
    """
    Configure and return the request logger.

    Log level is controlled by LOG_LEVEL environment variable.
    Defaults to INFO if not specified.
    """
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()

    # Validate log level
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if log_level not in valid_levels:
        log_level = "INFO"

    logger = logging.getLogger("api.request")
    logger.setLevel(getattr(logging, log_level))

    # Only add handler if logger doesn't have one yet
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(getattr(logging, log_level))
        # Use a simple format since we're outputting JSON
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured JSON logging of all API requests.

    Features:
    - Unique request_id (UUID4) for each request
    - Request timing (duration_ms)
    - Anonymized wallet addresses (first 8 chars of SHA256)
    - Structured JSON output to stdout
    - Error context preservation for debugging
    - Response status categorization (2xx, 4xx, 5xx)
    """

    # Endpoints that should not log request bodies (sensitive data)
    SENSITIVE_ENDPOINTS = {"/api/v1/agent/advice"}

    # Maximum body size to log (prevent memory issues)
    MAX_BODY_LOG_SIZE = 1000

    def __init__(self, app):
        super().__init__(app)
        self.logger = configure_logger()

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP, considering proxy headers."""
        # Check for forwarded headers (reverse proxy)
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _categorize_status(self, status_code: int) -> str:
        """Categorize HTTP status code for logging."""
        if status_code < 400:
            return "success"
        elif status_code < 500:
            return "client_error"
        else:
            return "server_error"

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request and log structured information."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Store request_id in context for access in exception handlers
        token = request_id_var.set(request_id)

        # Also store on request state for access in route handlers
        request.state.request_id = request_id

        # Capture request details
        timestamp = datetime.now(timezone.utc).isoformat()
        method = request.method
        path = anonymize_path(request.url.path)
        query_params = anonymize_query_params(request.url.query)
        client_ip = self._get_client_ip(request)

        # Build request log
        request_log: Dict[str, Any] = {
            "timestamp": timestamp,
            "request_id": request_id,
            "event": "request",
            "method": method,
            "path": path,
            "client_ip": client_ip,
        }
        if query_params:
            request_log["query_params"] = query_params

        # Add content type for POST/PUT requests
        if method in ("POST", "PUT", "PATCH"):
            content_type = request.headers.get("content-type", "")
            request_log["content_type"] = content_type.split(";")[0] if content_type else None

        self.logger.info(json.dumps(request_log))

        # Record start time
        start_time = time.perf_counter()

        try:
            # Call the next handler
            response = await call_next(request)

            # Calculate duration
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # Determine log level based on status code
            status_category = self._categorize_status(response.status_code)

            # Log response
            response_log: Dict[str, Any] = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": request_id,
                "event": "response",
                "method": method,
                "path": path,
                "status": response.status_code,
                "status_category": status_category,
                "duration_ms": duration_ms,
            }

            # Log 4xx/5xx responses as warnings/errors
            if response.status_code >= 500:
                self.logger.error(json.dumps(response_log))
            elif response.status_code >= 400:
                self.logger.warning(json.dumps(response_log))
            else:
                self.logger.info(json.dumps(response_log))

            # Add request_id to response headers for debugging
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            # Calculate duration even on error
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

            # Build detailed error log
            error_log: Dict[str, Any] = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "request_id": request_id,
                "event": "error",
                "method": method,
                "path": path,
                "error_type": type(exc).__name__,
                "error_message": str(exc)[:200],  # Truncate long messages
                "duration_ms": duration_ms,
            }

            # Add specific error context based on exception type
            if hasattr(exc, "status_code"):
                error_log["status_code"] = exc.status_code
            if hasattr(exc, "error_code"):
                error_log["error_code"] = exc.error_code

            self.logger.error(json.dumps(error_log))

            # Re-raise to let exception handlers deal with it
            raise

        finally:
            # Reset context variable
            request_id_var.reset(token)
