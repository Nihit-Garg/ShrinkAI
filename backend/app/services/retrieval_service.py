"""
Retrieval Service — Week 3 implementation.
Hybrid dense + sparse (BM25) + cross-encoder reranker.

TODO (Week 3):
- Dense retrieval: ChromaDB semantic search over episodic_memory_{user_id}
- Sparse retrieval: rank_bm25 over stored message text
- Reranker: cross-encoder/ms-marco-MiniLM-L-6-v2 from HuggingFace (local, free)
- Merge + deduplicate results from dense and sparse
- Return top-k reranked candidates for context assembly
"""
import logging

logger = logging.getLogger(__name__)


def hybrid_retrieve(user_id: str, query: str, top_k: int = 5) -> list[str]:
    """
    STUB — Week 3.
    Returns top-k relevant past memory chunks for a given query.
    """
    logger.debug(f"Hybrid retrieval stub called for user {user_id}. Returning empty list.")
    return []


def dense_retrieve(user_id: str, query_embedding: list[float], top_k: int = 20) -> list[dict]:
    """STUB — Week 3. Dense semantic retrieval from ChromaDB."""
    return []


def sparse_retrieve(user_id: str, query: str, top_k: int = 20) -> list[dict]:
    """STUB — Week 3. BM25 keyword retrieval over stored messages."""
    return []


def rerank(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """STUB — Week 3. Cross-encoder reranking of merged retrieval candidates."""
    return candidates[:top_k]
