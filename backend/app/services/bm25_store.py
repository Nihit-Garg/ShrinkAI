"""
BM25 sparse retrieval store for per-user episodic memory.

Maintains an in-memory BM25 index per user, lazily built from
all documents stored in the user's ChromaDB episodic collection.

Why BM25 here?
- Dense vectors (nomic-embed-text) are great for semantic similarity
  but miss exact names, dates, and specific quoted phrases.
- BM25 catches keyword matches that semantic search scores poorly,
  e.g. "dad" or "panic attack at work" with high precision.
- Combined via RRF in hybrid_retriever.py, the two approaches complement each other.
"""
import logging
from typing import Optional
from rank_bm25 import BM25Okapi
from app.vector_store import get_episodic_collection

logger = logging.getLogger(__name__)

# In-memory cache: user_id → (corpus_docs, BM25Okapi index)
_bm25_cache: dict[str, tuple[list[str], BM25Okapi]] = {}


def _tokenize(text: str) -> list[str]:
    """Simple whitespace + lowercase tokenizer for BM25."""
    return text.lower().split()


def _build_index(user_id: str) -> Optional[tuple[list[str], BM25Okapi]]:
    """
    Load all episodic chunks from ChromaDB for this user and build a BM25 index.
    Returns None if no documents exist yet.
    """
    collection = get_episodic_collection(user_id)
    result = collection.get(include=["documents"])

    docs = result.get("documents", [])
    ids = result.get("ids", [])

    if not docs:
        return None

    tokenized = [_tokenize(doc) for doc in docs]
    index = BM25Okapi(tokenized)
    logger.info(f"BM25 index built for user {user_id}: {len(docs)} documents")
    return ids, docs, index


def get_bm25_index(user_id: str) -> Optional[tuple[list[str], list[str], BM25Okapi]]:
    """
    Return the (ids, docs, BM25Okapi) tuple for a user.
    Rebuilds if not cached. Returns None if user has no episodic memory yet.
    """
    if user_id not in _bm25_cache:
        result = _build_index(user_id)
        if result is None:
            return None
        _bm25_cache[user_id] = result
    return _bm25_cache[user_id]


def invalidate_cache(user_id: str) -> None:
    """
    Call this after storing new episodic chunks so the next query
    picks up the new documents. Cheap operation — just drops the cached index.
    """
    _bm25_cache.pop(user_id, None)
    logger.debug(f"BM25 cache invalidated for user {user_id}")


def bm25_query(user_id: str, query: str, n: int = 10) -> list[dict]:
    """
    Run a BM25 sparse query for a user's episodic memory.

    Returns a list of dicts: [{"id": ..., "document": ..., "score": ...}]
    Sorted by BM25 score descending.
    """
    index_data = get_bm25_index(user_id)
    if index_data is None:
        return []

    ids, docs, bm25 = index_data
    tokenized_query = _tokenize(query)
    scores = bm25.get_scores(tokenized_query)

    # Pair with doc info and sort
    scored = sorted(
        zip(ids, docs, scores),
        key=lambda x: x[2],
        reverse=True,
    )
    return [
        {"id": item[0], "document": item[1], "score": float(item[2])}
        for item in scored[:n]
        if item[2] > 0  # Filter out zero-score docs
    ]
