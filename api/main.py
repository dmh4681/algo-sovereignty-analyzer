from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables explicitly from root directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

from .routes import router
from .news.routes import router as news_router
from .services.infra_routes import router as infra_router
from .alerts_routes import router as alerts_router, rebalance_router
from .errors import ApiException
from .middleware import LoggingMiddleware, get_current_request_id
from core.miner_metrics import get_miner_metrics_db
from core.silver_metrics import get_silver_metrics_db

app = FastAPI(
    title="Algorand Sovereignty Analyzer API",
    description="API for analyzing Algorand wallet sovereignty",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Handle startup tasks including optional database reseed."""
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(LoggingMiddleware)


# -----------------------------------------------------------------------------
# Exception Handlers
# -----------------------------------------------------------------------------

@app.exception_handler(ApiException)
async def api_exception_handler(request: Request, exc: ApiException) -> JSONResponse:
    """Handle custom API exceptions with structured error responses."""
    request_id = get_current_request_id() or getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.detail,
                "details": exc.details,
                "request_id": request_id
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors with structured error responses."""
    request_id = get_current_request_id() or getattr(request.state, "request_id", None)
    errors = exc.errors()
    # Extract field-level details from validation errors
    details = {
        "validation_errors": [
            {
                "field": ".".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", "Validation error"),
                "type": err.get("type", "unknown")
            }
            for err in errors
        ]
    }
    return JSONResponse(
        status_code=400,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": details,
                "request_id": request_id
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with a generic error response."""
    request_id = get_current_request_id() or getattr(request.state, "request_id", None)
    # Log the error for debugging (do not expose stack trace in response)
    print(f"Unhandled exception [request_id={request_id}]: {type(exc).__name__}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
                "details": None,
                "request_id": request_id
            }
        }
    )


app.include_router(router, prefix="/api/v1")
app.include_router(news_router, prefix="/api/v1")
app.include_router(infra_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(rebalance_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to the Algorand Sovereignty Analyzer API"}
