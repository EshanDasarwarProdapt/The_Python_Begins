"""
bm25_store.py - BM25 sparse retrieval index.
"""
import os
import json
import pickle
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
import logging

from app.config import settings

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> List[str]:
    """Simple whitespace + lowercase tokenizer."""
    return text.lower().split()


class BM25Store:
    """
    BM25-based sparse retrieval store.

    Stores:
        indexes/bm25/bm25_index.pkl  - the pickled BM25 model
        indexes/bm25/metadata.json   - chunk metadata
    """

    def __init__(self):
        self.bm25: Optional[BM25Okapi] = None
        self.metadata: List[Dict[str, Any]] = []
        self.index_path = os.path.join(settings.BM25_INDEX_DIR, "bm25_index.pkl")
        self.metadata_path = os.path.join(settings.BM25_INDEX_DIR, "metadata.json")

    def build_index(self, chunks: List[Dict[str, Any]]):
        """
        Build BM25 index from chunk texts.

        Args:
            chunks: List of chunk dicts with 'text' field.
        """
        corpus = [_tokenize(chunk["text"]) for chunk in chunks]
        self.bm25 = BM25Okapi(corpus)
        self.metadata = chunks
        logger.info(f"Built BM25 index with {len(chunks)} documents")

    def save(self):
        """Persist BM25 index and metadata to disk."""
        os.makedirs(settings.BM25_INDEX_DIR, exist_ok=True)

        with open(self.index_path, "wb") as f:
            pickle.dump(self.bm25, f)

        with open(self.metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved BM25 index to {self.index_path}")

    def load(self):
        """Load BM25 index and metadata from disk."""
        if not os.path.exists(self.index_path):
            raise FileNotFoundError(f"BM25 index not found at {self.index_path}")

        with open(self.index_path, "rb") as f:
            self.bm25 = pickle.load(f)

        with open(self.metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

        logger.info(f"Loaded BM25 index with {len(self.metadata)} documents")

    def search(
        self,
        query: str,
        top_k: int = None,
        metadata_filter: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search BM25 index.

        Args:
            query: Raw text query.
            top_k: Number of results.
            metadata_filter: Optional metadata filter dict.

        Returns:
            List of result dicts with 'score' added, sorted by descending score.
        """
        if self.bm25 is None:
            raise RuntimeError("BM25 index not loaded")

        top_k = top_k or settings.BM25_TOP_K
        tokenized_query = _tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        # Pair scores with indices and sort
        scored_indices = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)

        results = []
        for idx, score in scored_indices:
            if score <= 0:
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
