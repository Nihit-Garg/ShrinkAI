"""
Cross-Encoder Reranker — Second stage of the two-stage retrieval pipeline.

Stage 1 (hybrid_retriever.py): Broad recall — retrieve top-10 candidates
                                using dense + sparse + RRF fusion.
Stage 2 (this file): Precise precision — rerank top-10 candidates by
                     scoring each (query, passage) pair jointly.

Why a cross-encoder?
- Bi-encoders (like nomic-embed-text) encode query and passage separately,
  then compare vectors. Fast, but loses cross-attention between the two.
- A cross-encoder reads the query AND the passage together,
  allowing it to model token-level interactions.
- Cross-encoders consistently outperform bi-encoders for reranking.
- Trade-off: too slow for initial retrieval (O(n) passages), ideal for top-10.

Model: cross-encoder/ms-marco-MiniLM-L-6-v2
- 22M parameters, ~80MB download
- Trained on MS-MARCO (passage retrieval benchmark)
- Scores passage relevance on a scale (used relative, not absolute)
- Runs entirely locally — no API key, no external call
"""
import logging
from functools import lru_cache
from sentence_transformers import CrossEncoder

logger = logging.getLogger(__name__)

RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
DEFAULT_TOP_K = 4


@lru_cache(maxsize=1)
def _get_cross_encoder() -> CrossEncoder:
    """
    Singleton cross-encoder model.
    First call downloads the model (~80MB), subsequent calls use the cached instance.
    """
    logger.info(f"Loading cross-encoder model: {RERANKER_MODEL}")
    model = CrossEncoder(RERANKER_MODEL)
    logger.info("Cross-encoder loaded successfully.")
    return model


def rerank(query: str, candidates: list[dict], top_k: int = DEFAULT_TOP_K) -> list[dict]:
    """
    Rerank a list of candidate passages using the cross-encoder.

    Args:
        query: The user's current message (used as the relevance query)
        candidates: List of {id, document, rrf_score} from hybrid_retriever
        top_k: Number of top results to return after reranking

    Returns:
        List of top_k dicts, each with {id, document, rrf_score, rerank_score},
        sorted by rerank_score descending.
    """
    if not candidates:
        return []

    if len(candidates) == 1:
        # Nothing to rerank — return as-is with placeholder score
        return [{**candidates[0], "rerank_score": 1.0}]

    model = _get_cross_encoder()

    # Build (query, passage) pairs for the cross-encoder
    pairs = [(query, c["document"]) for c in candidates]

    # Score all pairs — returns raw logit scores (not probabilities, used relatively)
    scores = model.predict(pairs)

    # Attach scores and sort
    ranked = sorted(
        [
            {**candidates[i], "rerank_score": float(scores[i])}
            for i in range(len(candidates))
        ],
        key=lambda x: x["rerank_score"],
        reverse=True,
    )

    result = ranked[:top_k]
    logger.info(
        f"Reranker: {len(candidates)} candidates → top {len(result)} "
        f"(scores: {[round(r['rerank_score'], 2) for r in result]})"
    )
    return result
