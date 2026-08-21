"""
hybrid_search.py - Orchestrates BM25 + FAISS search, RRF fusion, and reranking.
"""
from typing import List, Dict, Any, Optional, Tuple
import logging
from app.config import settings
from app.retrieval.faiss_store import FAISSStore
from app.retrieval.bm25_store import BM25Store
from app.retrieval.embeddings import EmbeddingService
from app.retrieval.rrf import reciprocal_rank_fusion
from app.retrieval.reranker import Reranker

logger = logging.getLogger(__name__)


class HybridRetriever:
    """
    Combines dense and sparse retrieval with RRF and reranking.
    """

    def __init__(self, embedding_service: EmbeddingService):
        self.faiss_store = FAISSStore()
        self.bm25_store = BM25Store()
        self.embedding_service = embedding_service
        self.reranker = Reranker()
        
        # Load indexes on initialization
        try:
            self.faiss_store.load()
            self.bm25_store.load()
            logger.info("Successfully loaded FAISS and BM25 indexes.")
        except Exception as e:
            logger.error(f"Error loading indexes. Did you run ingestion? {e}")

    def retrieve(
        self,
        query: str,
        metadata_filter: Optional[Dict[str, str]] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
        """
        Perform hybrid retrieval for a query.
        
        Args:
            query: The user's query.
            metadata_filter: Optional metadata to filter results (e.g., {'department': 'HR'}).
            
        Returns:
            Tuple of (reranked_results, retrieval_stats_dict)
        """
        logger.info(f"Retrieving for query: '{query}', filter: {metadata_filter}")
        
        # 1. Sparse Search (BM25)
        bm25_results = self.bm25_store.search(
            query=query, 
            top_k=settings.BM25_TOP_K, 
            metadata_filter=metadata_filter
        )
        
        # 2. Dense Search (FAISS)
        query_embedding = self.embedding_service.embed_query(query)
        faiss_results = self.faiss_store.search(
            query_embedding=query_embedding,
            top_k=settings.VECTOR_TOP_K,
            metadata_filter=metadata_filter
        )
        
        # 3. Fuse Results (RRF)
        fused_results = reciprocal_rank_fusion([bm25_results, faiss_results])
        
        # 4. Filter by threshold (Hallucination protection - confidence threshold)
        filtered_fused = [
            res for res in fused_results 
            if res.get("rrf_score", 0) >= settings.RETRIEVAL_SCORE_THRESHOLD
        ]
        
        # 5. Rerank
        reranked_results = self.reranker.rerank(
            query=query, 
            results=filtered_fused, 
            top_k=settings.RERANK_TOP_K
        )
        
        stats = {
            "bm25_results": len(bm25_results),
            "vector_results": len(faiss_results),
            "rrf_results": len(fused_results),
            "reranked_results": len(reranked_results)
        }
        
        logger.info(f"Retrieval complete. Stats: {stats}")
        return reranked_results, stats
