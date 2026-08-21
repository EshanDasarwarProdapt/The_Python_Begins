"""
routes_chat.py - API endpoint for chat completion using LlamaIndex.
"""
from fastapi import APIRouter, HTTPException
import logging

from app.schemas.request import ChatRequest
from app.schemas.response import ChatResponse, SourceInfo, RetrievalStats
from app.retrieval.llama_service import LlamaService

logger = logging.getLogger(__name__)

router = APIRouter()

# Instantiate LlamaService at startup
try:
    llama_service = LlamaService()
except Exception as e:
    logger.error(f"Failed to initialize services: {e}")
    llama_service = None


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Handle a user question using LlamaIndex RAG.
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
        
    if not llama_service:
        raise HTTPException(status_code=500, detail="LlamaService not initialized.")
        
    try:
        # Use the LlamaService query (which internally uses a query_engine)
        # For a stateful chat, we could use get_chat_engine(), but we keep it stateless
        # per request to match the previous API schema.
        result = llama_service.query(request.query)
        
        answer = result["answer"]
        sources = result["sources"]
        
        # Format Response
        source_infos = []
        unique_sources = set()
        
        for s in sources:
            source_key = f"{s['document']}_{s['section']}_{s['page']}"
            if source_key not in unique_sources:
                unique_sources.add(source_key)
                
                try:
                    page_num = int(s["page"])
                except (ValueError, TypeError):
                    page_num = 1
                    
                source_infos.append(
                    SourceInfo(
                        document=s["document"],
                        section=str(s["section"]),
                        page=page_num
                    )
                )
        
        # Mock retrieval stats since LlamaIndex doesn't output Hybrid Stats directly
        retrieval_stats = RetrievalStats(
            bm25_results=0,
            vector_results=len(sources),
            rrf_results=0,
            reranked_results=len(source_infos)
        )
        
        return ChatResponse(
            answer=answer,
            sources=source_infos,
            retrieval=retrieval_stats,
            detected_department=request.department
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
