from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables explicitly from root directory
env_path = Path(__file__).parent.parent / '.env'
print(f"DEBUG: Loading .env from {env_path}")
load_dotenv(dotenv_path=env_path, override=True)

from .routes import router
from .news.routes import router as news_router
from .services.infra_routes import router as infra_router
from core.miner_metrics import get_miner_metrics_db

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
        print("[Startup] RESEED_MINERS=true detected, reseeding miner metrics database...")
        db = get_miner_metrics_db()
        count = db.reseed()
        print(f"[Startup] Reseeded {count} miner records successfully")
    else:
        print("[Startup] RESEED_MINERS not set, using existing database data")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")
app.include_router(news_router, prefix="/api/v1")
app.include_router(infra_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to the Algorand Sovereignty Analyzer API"}
