"""
embeddings.py - Embedding service abstraction using sentence-transformers.

Uses local HuggingFace models (no API calls needed for embeddings).
"""
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Abstraction over embedding models.
    Uses sentence-transformers for local, free, fast embeddings.
    """

    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.OPENAI_EMBEDDING_MODEL
        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self.dimension}")

    def embed_documents(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of document texts.

        Args:
            texts: List of text strings.

        Returns:
            numpy array of shape (len(texts), dimension).
        """
        if not texts:
            return np.array([])
        embeddings = self.model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
        return embeddings.astype(np.float32)

    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for a single query.

        Args:
            query: Query text string.

        Returns:
            numpy array of shape (dimension,).
        """
        embedding = self.model.encode([query], convert_to_numpy=True)
        return embedding.astype(np.float32)[0]
