"""
Hybrid Retriever — Dense (ChromaDB) + Sparse (BM25) with RRF Fusion.

Implements the two-source retrieval pattern used in production RAG systems:

  1. Dense retrieval: nomic-embed-text embeddings queried via ChromaDB cosine similarity
  2. Sparse retrieval: BM25Okapi over the episodic corpus (keyword precision)
  3. Reciprocal Rank Fusion (RRF): merges ranked lists without requiring score normalization

Why RRF?
- Dense and sparse scores are not on the same scale — you can't just add them
- RRF only uses *rank positions*, not raw scores, making it scale-invariant
- Formula: RRF(doc) = Σ 1 / (k + rank_i)   where k=60 (empirically optimal, see Cormack 2009)
- Industry standard: used by Elasticsearch, Weaviate, Cohere hybrid search

Output is passed to reranker.py for the second stage.
"""
import logging
from app.vector_store import get_episodic_collection, get_embedder
from app.services.bm25_store import bm25_query

logger = logging.getLogger(__name__)

# RRF constant — 60 is the standard from the original paper (Cormack et al., 2009)
RRF_K = 60

# How many candidates to retrieve from each source before fusion
DENSE_CANDIDATES = 12
SPARSE_CANDIDATES = 12

# How many fused candidates to return (fed to reranker)
FUSED_TOP_N = 10


def _dense_query(user_id: str, query: str, n: int) -> list[dict]:
    """
    Query ChromaDB episodic collection with dense embedding.
    Returns ranked list of {id, document, distance}.
    """
    collection = get_episodic_collection(user_id)
    if collection.count() == 0:
        return []

    embedder = get_embedder()
    query_embedding = embedder.embed_query(query)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(n, collection.count()),
        include=["documents", "distances", "metadatas"],
    )

    docs = results.get("documents", [[]])[0]
    ids = results.get("ids", [[]])[0]
    distances = results.get("distances", [[]])[0]

    return [
        {"id": ids[i], "document": docs[i], "distance": distances[i]}
        for i in range(len(ids))
    ]


def reciprocal_rank_fusion(
    dense_results: list[dict],
    sparse_results: list[dict],
    k: int = RRF_K,
) -> list[dict]:
    """
    Merge two ranked lists using Reciprocal Rank Fusion.

    Each document accumulates: score += 1 / (k + rank)
    Documents appearing in both lists get contributions from both.

    Returns merged list sorted by RRF score descending.
    """
    scores: dict[str, float] = {}
    doc_map: dict[str, str] = {}  # id → document text

    for rank, item in enumerate(dense_results):
        doc_id = item["id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
        doc_map[doc_id] = item["document"]

    for rank, item in enumerate(sparse_results):
        doc_id = item["id"]
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
        doc_map[doc_id] = item["document"]

    sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
    return [
        {"id": doc_id, "document": doc_map[doc_id], "rrf_score": scores[doc_id]}
        for doc_id in sorted_ids
    ]


def hybrid_retrieve(user_id: str, query: str, top_n: int = FUSED_TOP_N) -> list[dict]:
    """
    Full hybrid retrieval pipeline for a user's episodic memory.

    Steps:
      1. Dense query → ChromaDB top-12
      2. Sparse query → BM25 top-12
      3. RRF fusion → merged top-10

    Returns list of {id, document, rrf_score} sorted by relevance.
    These candidates are then fed to the cross-encoder reranker.
    """
    dense_results = _dense_query(user_id, query, DENSE_CANDIDATES)
    sparse_results = bm25_query(user_id, query, SPARSE_CANDIDATES)

    if not dense_results and not sparse_results:
        logger.debug(f"No episodic memory found for user {user_id}")
        return []

    fused = reciprocal_rank_fusion(dense_results, sparse_results)
    top = fused[:top_n]

    logger.info(
        f"Hybrid retrieval for user {user_id}: "
        f"{len(dense_results)} dense + {len(sparse_results)} sparse → "
        f"{len(fused)} fused → top {len(top)}"
    )
    return top
