"""
Algorand Sovereignty Analyzer - FastAPI Application
====================================================

This module initializes and configures the FastAPI application for the
Algorand Sovereignty Analyzer API.

Application Structure:
    - Main app initialization with OpenAPI documentation
    - CORS middleware for cross-origin requests
    - Security headers middleware (X-Content-Type-Options, etc.)
    - Rate limiting middleware (30/min for /analyze, 100/min for others)
    - Request logging middleware with correlation IDs
    - Global exception handlers for consistent error responses

Startup Tasks:
    - Environment variable validation
    - Secret configuration logging (masked values)
    - Optional database reseeding (RESEED_MINERS, RESEED_SILVER)

Available Routes (all prefixed with /api/v1):
    - /analyze: Wallet sovereignty analysis
    - /agent/advice: AI coaching via Claude
    - /classifications: Asset classification lookup
    - /history: Historical sovereignty snapshots
    - /network: Algorand network statistics
    - /arbitrage: Meld gold/silver premium analysis
    - /news: Market news aggregation
    - /alerts: Sovereignty alert system

Documentation Endpoints:
    - /docs: Swagger UI interactive documentation
    - /redoc: ReDoc alternative documentation
    - /openapi.json: OpenAPI 3.0 specification

Health Endpoints:
    - /health: Basic health check (returns 200 if running)
    - /health/config: Environment configuration status (no secrets exposed)

Environment Variables:
    See docs/SETUP-GUIDE.md for complete configuration reference.

    Required:
        ANTHROPIC_API_KEY: For AI coaching feature

    Optional:
        ALGORAND_NODE_URL: Custom Algorand node (default: AlgoNode)
        CORS_ORIGINS: Allowed origins (default: *)
        RESEED_MINERS: Reseed gold miner DB on startup
        RESEED_SILVER: Reseed silver miner DB on startup

Usage:
    # Development
    uvicorn api.main:app --reload --port 8000

    # Production
    uvicorn api.main:app --host 0.0.0.0 --port $PORT

    # Docker
    docker-compose up --build

See Also:
    - api/routes.py: API endpoint definitions
    - api/schemas.py: Request/response Pydantic models
    - api/errors.py: Custom exception classes
    - api/middleware.py: Logging middleware
    - api/security.py: Rate limiting and security headers
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from dotenv import load_dotenv
import os
import logging
from pathlib import Path

# =============================================================================
# Environment Configuration
# =============================================================================
# Load environment variables from .env file in project root
# SECURITY: .env file should never be committed to version control
# The .gitignore should already exclude it

env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# =============================================================================
# Module Imports (after env vars loaded)
# =============================================================================
from .routes import router
from .news.routes import router as news_router
from .services.infra_routes import router as infra_router
from .alerts_routes import router as alerts_router, rebalance_router
from .errors import (
    ApiException,
    TimeoutException,
    ServiceUnavailableException,
    RateLimitException,
)
from .middleware import LoggingMiddleware, get_current_request_id, SlidingWindowRateLimitMiddleware
from .security import SecurityHeadersMiddleware
from core.miner_metrics import get_miner_metrics_db
from core.silver_metrics import get_silver_metrics_db
from core.secrets import check_optional_secrets, get_secret, mask_secret

# Configure module logger for exception handlers
logger = logging.getLogger("api.exceptions")

app = FastAPI(
    title="Algorand Sovereignty Analyzer API",
    description="""
## Overview

The Algorand Sovereignty Analyzer API provides tools for analyzing Algorand wallet
holdings through a **hard money maximalist** lens.

## Core Concepts

### Sovereignty Ratio
```
Sovereignty Ratio = Total Portfolio USD / Annual Fixed Expenses
```

This ratio represents how many years of essential expenses can be covered by
your portfolio, providing a measure of true financial freedom.

### Asset Categories

| Category | Examples | Philosophy |
|----------|----------|------------|
| **hard_money** | BTC, Gold, Silver | Generational wealth preservation |
| **algo** | ALGO, xALGO, fALGO | Platform native, staking rewards |
| **dollars** | USDC, USDT, DAI | Fiat proxy, short-term liquidity |
| **shitcoin** | Everything else | Speculative, high risk |

### Sovereignty Status Levels

| Status | Ratio | Meaning |
|--------|-------|---------|
| Generationally Sovereign | >= 20 | Multi-generational wealth |
| Antifragile | >= 6 | Benefits from volatility |
| Robust | >= 3 | Can weather major storms |
| Fragile | >= 1 | Building foundation |
| Vulnerable | < 1 | Immediate action needed |

## Features

- **Wallet Analysis**: Classify and value all assets in any Algorand wallet
- **LP Decomposition**: Automatically break down LP tokens into underlying assets
- **AI Coaching**: Personalized advice from Claude AI
- **Historical Tracking**: Track sovereignty progress over time
- **Network Stats**: Algorand decentralization metrics
- **Arbitrage Analysis**: Meld gold/silver premium comparisons

## Rate Limits

| Scope | Endpoint | Limit |
|-------|----------|-------|
| Per IP | `/analyze`, `/agent/advice`, `/advisor` | 10/minute |
| Per IP | All others | 60/minute |
| Per wallet | `/analyze` (and related analysis endpoints) | 20/minute |

## Authentication

Currently open (no authentication required). For production deployments,
consider adding API key authentication via the `X-API-Key` header.
    """,
    version="1.0.0",
    contact={
        "name": "Sovereign Path LLC",
        "url": "https://algosovereignty.com",
        "email": "dylan@sovereignpath.com"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://algosovereignty.com/terms"
    },
    openapi_tags=[
        {
            "name": "Wallet Analysis",
            "description": "Analyze Algorand wallets for sovereignty metrics"
        },
        {
            "name": "AI Coaching",
            "description": "Get personalized advice from Claude AI"
        },
        {
            "name": "Classification",
            "description": "Asset classification and corrections"
        },
        {
            "name": "History",
            "description": "Historical sovereignty tracking"
        },
        {
            "name": "Network",
            "description": "Algorand network statistics"
        },
        {
            "name": "Health",
            "description": "API health and status endpoints"
        }
    ]
)


@app.on_event("startup")
async def startup_event():
    """
    Handle startup tasks including environment validation and optional database reseed.

    Security: Validates required environment variables are present before starting.
    """
    # -------------------------------------------------------------------------
    # SECURITY: Validate environment configuration at startup
    # -------------------------------------------------------------------------
    print("[Startup] Validating environment configuration...")

    secrets_status = check_optional_secrets()
    missing_optional = []

    for name, status in secrets_status.items():
        if status["is_set"]:
            # Log that secret is configured (never log actual values)
            print(f"[Startup]   {name}: configured")
        elif status["has_default"]:
            print(f"[Startup]   {name}: using default")
        else:
            missing_optional.append(name)
            print(f"[Startup]   {name}: not set (optional)")

    # Warn about important missing secrets
    anthropic_key = get_secret("ANTHROPIC_API_KEY")
    if not anthropic_key:
        print("[Startup] WARNING: ANTHROPIC_API_KEY not set - AI coaching feature will be unavailable")
    else:
        # SECURITY: Use strict masking for API keys to avoid exposing any portion
        print(f"[Startup]   ANTHROPIC_API_KEY: {mask_secret(anthropic_key, strict=True)} (configured)")

    print("[Startup] Environment validation complete")
    print("")

    # -------------------------------------------------------------------------
    # Database reseed tasks
    # -------------------------------------------------------------------------
    # Check if RESEED_MINERS env var is set to trigger database reseed
    reseed_miners = os.environ.get('RESEED_MINERS', '').lower() in ('true', '1', 'yes')
    if reseed_miners:
        print("[Startup] RESEED_MINERS=true detected, reseeding gold miner metrics database...")
        db = get_miner_metrics_db()
        count = db.reseed()
        print(f"[Startup] Reseeded {count} gold miner records successfully")
    else:
        print("[Startup] RESEED_MINERS not set, using existing gold miner data")

    # Check if RESEED_SILVER env var is set to trigger silver database reseed
    reseed_silver = os.environ.get('RESEED_SILVER', '').lower() in ('true', '1', 'yes')
    if reseed_silver:
        print("[Startup] RESEED_SILVER=true detected, reseeding silver miner metrics database...")
        silver_db = get_silver_metrics_db()
        silver_count = silver_db.reseed()
        print(f"[Startup] Reseeded {silver_count} silver miner records successfully")
    else:
        print("[Startup] RESEED_SILVER not set, using existing silver miner data")

# Add CORS middleware
# Production: restrict to specific origins via CORS_ORIGINS env var
allowed_origins = os.environ.get(
    "CORS_ORIGINS",
    "http://localhost:3000,https://algosovereignty.com,https://www.algosovereignty.com"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add security headers middleware (runs first on response)
app.add_middleware(SecurityHeadersMiddleware)

# Add sliding window rate limiting middleware (STANDARD: 60/min, EXPENSIVE: 10/min)
app.add_middleware(SlidingWindowRateLimitMiddleware)

# Add request logging middleware
app.add_middleware(LoggingMiddleware)


# -----------------------------------------------------------------------------
# Exception Handlers
# -----------------------------------------------------------------------------

def _build_error_response(
    status_code: int,
    error_code: str,
    message: str,
    request_id: str,
    details: dict = None,
    headers: dict = None
) -> JSONResponse:
    """Build a consistent error response with correlation ID."""
    response = JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "code": error_code,
                "message": message,
                "details": details,
                "request_id": request_id
            }
        }
    )
    if headers:
        for key, value in headers.items():
            response.headers[key] = str(value)
    return response


@app.exception_handler(ApiException)
async def api_exception_handler(request: Request, exc: ApiException) -> JSONResponse:
    """Handle custom API exceptions with structured error responses."""
    request_id = get_current_request_id() or getattr(request.state, "request_id", None)

    # Log the error with context
    logger.warning(
        f"API error [request_id={request_id}] [{exc.error_code}]: {exc.detail}",
        extra={"request_id": request_id, "error_code": exc.error_code}
    )

    # Build headers for rate limit exceptions
    headers = {}
    if isinstance(exc, RateLimitException) and exc.retry_after:
        headers["Retry-After"] = exc.retry_after
    elif isinstance(exc, ServiceUnavailableException) and exc.retry_after:
        headers["Retry-After"] = exc.retry_after

    return _build_error_response(
        status_code=exc.status_code,
        error_code=exc.error_code,
        message=exc.detail,
        request_id=request_id,
        details=exc.details,
        headers=headers if headers else None
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle standard HTTP exceptions (404, 405, etc.) with structured responses."""
    request_id = get_current_request_id() or getattr(request.state, "request_id", None)

    # Map common HTTP status codes to error codes
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        408: "REQUEST_TIMEOUT",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        429: "RATE_LIMIT_EXCEEDED",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT",
    }

    error_code = error_code_map.get(exc.status_code, f"HTTP_{exc.status_code}")

    # Log 5xx errors as errors, others as warnings
    if exc.status_code >= 500:
        logger.error(
            f"HTTP error [request_id={request_id}] [{error_code}]: {exc.detail}",
            extra={"request_id": request_id, "status_code": exc.status_code}
        )
    else:
        logger.warning(
            f"HTTP error [request_id={request_id}] [{error_code}]: {exc.detail}",
            extra={"request_id": request_id, "status_code": exc.status_code}
        )

    return _build_error_response(
        status_code=exc.status_code,
        error_code=error_code,
        message=str(exc.detail),
        request_id=request_id,
        details={"path": str(request.url.path)}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors with structured error responses."""
    request_id = get_current_request_id() or getattr(request.state, "request_id", None)
    errors = exc.errors()

    # Extract field-level details from validation errors
    validation_errors = []
    for err in errors:
        field_path = ".".join(str(loc) for loc in err.get("loc", []))
        validation_errors.append({
            "field": field_path,
            "message": err.get("msg", "Validation error"),
            "type": err.get("type", "unknown"),
            "input": _sanitize_input(err.get("input"))
        })

    details = {"validation_errors": validation_errors}

    logger.warning(
        f"Validation error [request_id={request_id}]: {len(validation_errors)} field(s) failed",
        extra={"request_id": request_id, "error_count": len(validation_errors)}
    )

    return _build_error_response(
        status_code=400,
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        request_id=request_id,
        details=details
    )


def _sanitize_input(value) -> str:
    """Sanitize input values for error responses (truncate, mask sensitive data)."""
    if value is None:
        return None
    value_str = str(value)
    # Truncate long values
    if len(value_str) > 100:
        return value_str[:50] + "..." + value_str[-20:]
    # Mask potential wallet addresses (58 chars)
    if len(value_str) == 58 and value_str.isalnum():
        return f"{value_str[:8]}...{value_str[-6:]}"
    return value_str


@app.exception_handler(ConnectionError)
async def connection_error_handler(request: Request, exc: ConnectionError) -> JSONResponse:
    """Handle connection errors to external services."""
    request_id = get_current_request_id() or getattr(request.state, "request_id", None)

    logger.error(
        f"Connection error [request_id={request_id}]: {exc}",
        extra={"request_id": request_id, "error_type": "ConnectionError"}
    )

    return _build_error_response(
        status_code=503,
        error_code="SERVICE_UNAVAILABLE",
        message="Unable to connect to external service",
        request_id=request_id,
        details={"error_type": "connection_error"}
    )


@app.exception_handler(TimeoutError)
async def timeout_error_handler(request: Request, exc: TimeoutError) -> JSONResponse:
    """Handle timeout errors."""
    request_id = get_current_request_id() or getattr(request.state, "request_id", None)

    logger.error(
        f"Timeout error [request_id={request_id}]: {exc}",
        extra={"request_id": request_id, "error_type": "TimeoutError"}
    )

    return _build_error_response(
        status_code=504,
        error_code="GATEWAY_TIMEOUT",
        message="Request timed out",
        request_id=request_id,
        details={"error_type": "timeout"}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with a generic error response.

    SECURITY: Never expose stack traces or internal error details in production.
    All details are logged server-side but not returned to the client.
    """
    request_id = get_current_request_id() or getattr(request.state, "request_id", None)

    # Log the full error with traceback for debugging
    logger.exception(
        f"Unhandled exception [request_id={request_id}]: {type(exc).__name__}: {exc}",
        extra={"request_id": request_id, "error_type": type(exc).__name__}
    )

    # Return generic error to client (no internal details)
    return _build_error_response(
        status_code=500,
        error_code="INTERNAL_ERROR",
        message="An unexpected error occurred",
        request_id=request_id,
        details=None
    )


app.include_router(router, prefix="/api/v1")
app.include_router(news_router, prefix="/api/v1")
app.include_router(infra_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(rebalance_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to the Algorand Sovereignty Analyzer API"}


# -----------------------------------------------------------------------------
# Health & Status Endpoints
# -----------------------------------------------------------------------------

@app.get(
    "/health",
    summary="Health check",
    description="Basic health check endpoint for load balancers and monitoring.",
    response_description="Health status",
    tags=["Health"]
)
async def health_check():
    """
    Basic health check endpoint.

    Returns 200 OK if the API is running. Used by load balancers, Kubernetes
    probes, and monitoring systems to verify the service is up.

    Returns:
        Dict with status and service name

    Example Response:
        {"status": "healthy", "service": "algorand-sovereignty-analyzer"}
    """
    return {"status": "healthy", "service": "algorand-sovereignty-analyzer"}


@app.get(
    "/health/config",
    summary="Configuration status",
    description="""
Report environment configuration status for operational monitoring.

**SECURITY**: This endpoint reports which secrets are configured (is_set: true/false)
but **NEVER** exposes actual secret values. Safe for monitoring dashboards.

## Response Fields

For each registered environment variable:
- `configured`: Whether the variable has a non-empty value
- `using_default`: Whether falling back to default value
- `required`: Whether required for core functionality
- `description`: What the variable is used for

## Warnings

The response includes a `warnings` array for important missing configurations
that may degrade functionality (e.g., missing ANTHROPIC_API_KEY disables AI coaching).
    """,
    response_description="Configuration status report",
    tags=["Health"]
)
async def config_status():
    """
    Report environment configuration status for operational monitoring.

    SECURITY: This endpoint reports which secrets are configured (is_set: true/false)
    but NEVER exposes actual secret values. Safe for monitoring dashboards.

    Returns status of each registered environment variable:
    - is_set: Whether the variable has a non-empty value
    - required: Whether the variable is required for core functionality
    - has_default: Whether a default value is available
    - description: What the variable is used for
    """
    from core.secrets import check_optional_secrets

    secrets_status = check_optional_secrets()

    # Build response with clear status indicators
    config_report = {}
    warnings = []

    for name, status in secrets_status.items():
        config_report[name] = {
            "configured": status["is_set"],
            "using_default": not status["is_set"] and status["has_default"],
            "required": status["required"],
            "description": status["description"]
        }

        # Add warnings for important missing configs
        if name == "ANTHROPIC_API_KEY" and not status["is_set"]:
            warnings.append("AI coaching feature unavailable (ANTHROPIC_API_KEY not set)")

    return {
        "status": "ok" if not warnings else "degraded",
        "config": config_report,
        "warnings": warnings,
        "note": "Secret values are never exposed via this endpoint"
    }
