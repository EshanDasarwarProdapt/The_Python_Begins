"""
request.py - Pydantic request models for the API.
"""
from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    """Request body for POST /api/chat"""
    query: str
    department: Optional[str] = None
