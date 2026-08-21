"""
reranker.py - Abstract reranker and a simple baseline implementation.
"""
from typing import List, Dict, Any
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class Reranker:
    """
    Reranker abstraction. 
    In a production system, this could call Cohere Rerank, BGE-Reranker, etc.
    """

    def rerank(self, query: str, results: List[Dict[str, Any]], top_k: int = None) -> List[Dict[str, Any]]:
        """
        Rerank a list of results based on query relevance.
        
        Args:
            query: The user query.
            results: List of candidate results (e.g. from RRF).
            top_k: Number of top results to return.
            
        Returns:
            Reranked list of top_k results.
        """
        top_k = top_k or settings.RERANK_TOP_K
        
        # Baseline implementation: We just use the RRF score as a proxy for relevance
        # if a real reranker is not configured.
        logger.info(f"Reranking {len(results)} results using baseline (RRF score pass-through)")
        
        # Assuming results are already sorted by RRF score, just slice top_k
        reranked = results[:top_k]
        
        return reranked
