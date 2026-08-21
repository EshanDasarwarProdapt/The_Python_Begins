"""
rrf.py - Reciprocal Rank Fusion implementation.

Combines ranked result lists from multiple retrieval methods into a
single unified ranking.

Formula: RRF_score(d) = sum(1 / (k + rank(d))) across all result lists.
"""
from typing import List, Dict, Any
from app.config import settings
import logging

logger = logging.getLogger(__name__)


def reciprocal_rank_fusion(
    result_lists: List[List[Dict[str, Any]]],
    k: int = None,
) -> List[Dict[str, Any]]:
    """
    Fuse multiple ranked result lists using Reciprocal Rank Fusion.

    Args:
        result_lists: List of ranked result lists. Each result must have 'chunk_id'.
        k: RRF constant (default 60). Higher k = more uniform weight.

    Returns:
        Unified ranked list sorted by RRF score (descending).
        Each result dict includes 'rrf_score' and 'sources' (list of retriever names).
    """
    k = k or settings.RRF_K
    retriever_names = ["bm25", "vector"]

    # chunk_id -> {rrf_score, chunk_data, sources}
    fused: Dict[str, Dict[str, Any]] = {}

    for list_idx, results in enumerate(result_lists):
        retriever_name = retriever_names[list_idx] if list_idx < len(retriever_names) else f"retriever_{list_idx}"

        for rank, result in enumerate(results, start=1):
            chunk_id = result.get("chunk_id", f"unknown_{rank}")
            rrf_score = 1.0 / (k + rank)

            if chunk_id in fused:
                fused[chunk_id]["rrf_score"] += rrf_score
                fused[chunk_id]["sources"].append(retriever_name)
            else:
                entry = result.copy()
                entry["rrf_score"] = rrf_score
                entry["sources"] = [retriever_name]
                fused[chunk_id] = entry

    # Sort by RRF score descending
    ranked = sorted(fused.values(), key=lambda x: x["rrf_score"], reverse=True)

    logger.info(
        f"RRF fused {sum(len(r) for r in result_lists)} results into {len(ranked)} unique chunks"
    )
    return ranked
