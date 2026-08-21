"""
routes_health.py - API endpoint for health checks.
"""
from fastapi import APIRouter
import os
from app.config import settings

router = APIRouter()

@router.get("/health")
def health_check():
    """Simple health check endpoint."""
    faiss_exists = os.path.exists(os.path.join(settings.FAISS_INDEX_DIR, "index.faiss"))
    bm25_exists = os.path.exists(os.path.join(settings.BM25_INDEX_DIR, "bm25_index.pkl"))
    
    return {
        "status": "ok",
        "faiss_index_loaded": faiss_exists,
        "bm25_index_loaded": bm25_exists
    }
