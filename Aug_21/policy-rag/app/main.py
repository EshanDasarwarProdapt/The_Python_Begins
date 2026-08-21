"""
main.py - FastAPI application entrypoint.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import routes_chat, routes_health
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Enterprise Policy RAG",
    description="Multi-PDF Hybrid RAG System for company policies.",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(routes_health.router, prefix="/api", tags=["Health"])
app.include_router(routes_chat.router, prefix="/api", tags=["Chat"])

# Mount static frontend
import os
frontend_dir = os.path.join(settings.BASE_DIR, "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:
    logger.warning(f"Frontend directory not found at {frontend_dir}")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI server...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
