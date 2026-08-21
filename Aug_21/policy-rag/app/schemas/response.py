"""
response.py - Pydantic response models for the API.
"""
from pydantic import BaseModel
from typing import List, Optional


class SourceInfo(BaseModel):
    """A single source citation."""
    document: str
    section: str
    page: int


class RetrievalStats(BaseModel):
    """Statistics about the retrieval pipeline."""
    bm25_results: int
    vector_results: int
    rrf_results: int
    reranked_results: int


class ChatResponse(BaseModel):
    """Response body for POST /api/chat"""
    answer: str
    sources: List[SourceInfo]
    retrieval: RetrievalStats
    detected_department: Optional[str] = None
