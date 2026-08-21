"""
faiss_store.py - FAISS vector index for dense retrieval.
"""
import os
import json
import numpy as np
import faiss
from typing import List, Dict, Any, Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class FAISSStore:
    """
    FAISS-based vector store with metadata mapping.

    Stores:
        indexes/faiss/index.faiss   - the FAISS index
        indexes/faiss/metadata.json - chunk metadata keyed by index position
    """

    def __init__(self):
        self.index: Optional[faiss.Index] = None
        self.metadata: List[Dict[str, Any]] = []
        self.index_path = os.path.join(settings.FAISS_INDEX_DIR, "index.faiss")
        self.metadata_path = os.path.join(settings.FAISS_INDEX_DIR, "metadata.json")

    def build_index(self, embeddings: np.ndarray, chunks: List[Dict[str, Any]]):
        """
        Build a new FAISS index from embeddings and metadata.

        Args:
            embeddings: numpy array of shape (N, dim).
            chunks: List of chunk dicts with metadata.
        """
        if len(embeddings) == 0:
            raise ValueError("No embeddings to index")

        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)  # Inner product (cosine sim on normalized vectors)

        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)
        self.index.add(embeddings)
        self.metadata = chunks

        logger.info(f"Built FAISS index with {self.index.ntotal} vectors (dim={dimension})")

    def save(self):
        """Persist index and metadata to disk."""
        os.makedirs(settings.FAISS_INDEX_DIR, exist_ok=True)
        faiss.write_index(self.index, self.index_path)

        # Save metadata (strip 'text' to save space, keep it in a separate field)
        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved FAISS index to {self.index_path}")

    def load(self):
        """Load index and metadata from disk."""
        if not os.path.exists(self.index_path):
            raise FileNotFoundError(f"FAISS index not found at {self.index_path}")

        self.index = faiss.read_index(self.index_path)
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")

    def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = None,
        metadata_filter: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search the FAISS index.

        Args:
            query_embedding: Query vector of shape (dim,).
            top_k: Number of results to return.
            metadata_filter: Optional dict of metadata field -> value to filter.

        Returns:
            List of result dicts with 'score' added.
        """
        if self.index is None:
            raise RuntimeError("FAISS index not loaded")

        top_k = top_k or settings.VECTOR_TOP_K

        # Normalize query
        query_vec = query_embedding.reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query_vec)

        # Search more than needed if we have filters
        search_k = top_k * 3 if metadata_filter else top_k
        scores, indices = self.index.search(query_vec, min(search_k, self.index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            chunk = self.metadata[idx].copy()
            chunk["score"] = float(score)

            # Apply metadata filter
            if metadata_filter:
                match = all(
                    chunk.get(k, "").lower() == v.lower()
                    for k, v in metadata_filter.items()
                )
                if not match:
                    continue

            results.append(chunk)
            if len(results) >= top_k:
                break

        return results
