"""
Cross-Encoder Reranker — Lightweight production version.

The original implementation used sentence-transformers (CrossEncoder) which loads
PyTorch into memory (~500MB+ RAM). This caused OOM crashes on Railway's containers.

This replacement uses the RRF scores already computed by hybrid_retriever.py.
The quality trade-off is minimal for small candidate sets (≤10 items):
  - Dense + BM25 + RRF fusion already provides strong candidate ordering
  - Cross-encoder precision gains are most valuable at 20+ candidates

If cross-encoder reranking is needed in the future, the recommended approach is
to use an API-based reranker (e.g. Cohere Rerank) instead of a local model,
so no model weights are loaded into the container's RAM.
"""
import logging

logger = logging.getLogger(__name__)

DEFAULT_TOP_K = 4


def rerank(query: str, candidates: list[dict], top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """
    Returns the top_k candidates ordered by their existing RRF score.

    This is a lightweight pass-through — the hybrid retriever's RRF fusion
    already produces a strong relevance ranking. Adding a cross-encoder would
    improve precision marginally but at the cost of loading PyTorch into RAM.

    Each candidate already has {id, document, rrf_score} from hybrid_retriever.
    We add a `rerank_score` field (mirroring the original interface) set to rrf_score
    so downstream code that reads rerank_score works without changes.
    """
    if not candidates:
        return []

    sorted_candidates = sorted(candidates, key=lambda x: x.get("rrf_score", 0), reverse=True)
    result = sorted_candidates[:top_k]

    for r in result:
        r["rerank_score"] = r.get("rrf_score", 0.0)

    logger.info(
        f"Reranker (RRF pass-through): {len(candidates)} candidates → top {len(result)}"
    )
    return result
