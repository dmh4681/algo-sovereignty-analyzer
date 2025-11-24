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

app = FastAPI(
    title="Algorand Sovereignty Analyzer API",
    description="API for analyzing Algorand wallet sovereignty",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Welcome to the Algorand Sovereignty Analyzer API"}
