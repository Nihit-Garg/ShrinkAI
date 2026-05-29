"""
RAGAS Evaluation Baseline Script — Week 3+4

Measures retrieval + generation quality using 4 RAGAS metrics:

  - Context Precision:  Are retrieved chunks actually relevant to the query?
  - Context Recall:     Does retrieved context cover what's needed for the answer?
  - Faithfulness:       Is the LLM answer grounded in the retrieved context?
  - Answer Relevancy:   Does the answer actually address the question?

How to run:
    cd backend
    source venv/bin/activate
    python eval/ragas_eval.py --user_id <user_id>

Outputs results to eval/results.json

Requirements:
    - User must have completed the questionnaire
    - User must have at least 1 completed session (with reflection done)
    - GROQ_API_KEY must be in .env
"""
import os
import sys
import json
import argparse
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def build_eval_dataset(user_id: str) -> list[dict]:
    """
    Build an evaluation dataset from stored episodic chunks.

    For each stored chunk, we:
      1. Generate a realistic synthetic query the chunk should answer
      2. Run our full retrieval pipeline against that query
      3. Generate a response from the retrieved contexts
      4. Record ground_truth = the original chunk

    This lets RAGAS measure whether our retrieval finds the right chunk
    and whether the LLM uses it faithfully.
    """
    from app.db_client import SupabaseDB
    from app.vector_store import get_episodic_collection
    from app.services.hybrid_retriever import hybrid_retrieve
    from app.services.reranker import rerank
    from app.services.llm_service import get_llm_service

    db = SupabaseDB()
    llm = get_llm_service()
    collection = get_episodic_collection(user_id)
    stored = collection.get(include=["documents"])

    docs = stored.get("documents", [])
    if not docs:
        logger.error("No episodic chunks found. Complete sessions + run reflection first.")
        return []

    logger.info(f"Found {len(docs)} episodic chunks — building eval samples...")
    samples = []

    for i, chunk in enumerate(docs[:10]):  # Cap at 10 to limit API calls
        logger.info(f"  Sample {i+1}/{min(len(docs), 10)}")

        # Synthesise a realistic query for this chunk
        question = llm.complete(
            system_prompt=(
                "You are generating test cases for a retrieval system. "
                "Write ONE realistic, specific question that a therapy patient might share "
                "in conversation that relates to the following memory note. "
                "Return ONLY the question, no explanation."
            ),
            user_message=chunk,
            temperature=0.7,
            max_tokens=80,
        ).strip()

        # Run retrieval pipeline
        candidates = hybrid_retrieve(user_id, question, top_n=10)
        top = rerank(question, candidates, top_k=4) if candidates else []
        contexts = [r["document"] for r in top] if top else [chunk]

        # Generate answer from retrieved contexts
        context_str = "\n".join(f"- {c}" for c in contexts)
        answer = llm.complete(
            system_prompt=(
                "You are a therapist. Using ONLY the following session notes, "
                "respond to the user briefly and helpfully.\n\nNotes:\n" + context_str
            ),
            user_message=question,
            temperature=0.5,
            max_tokens=150,
        ).strip()

        samples.append({
            "question": question,
            "contexts": contexts,
            "answer": answer,
            "ground_truth": chunk,
        })

    return samples


def run_ragas_evaluation(user_id: str, output_path: str = "eval/results.json") -> dict:
    """
    Run RAGAS evaluation against the retrieval + generation pipeline.
    Uses Groq (already in our stack) as the judge LLM — no new API keys needed.
    """
    from datasets import Dataset
    from ragas import evaluate
    from ragas.metrics import (
        context_precision,
        context_recall,
        faithfulness,
        answer_relevancy,
    )

    # RAGAS uses LangChain as its internal LLM interface (transitive dep of ragas).
    # We wrap our existing Groq API key in the standard LangChain Groq client.
    from langchain_groq import ChatGroq
    from langchain_huggingface import HuggingFaceEmbeddings
    from ragas.llms import LangchainLLMWrapper
    from ragas.embeddings import LangchainEmbeddingsWrapper

    logger.info(f"Building eval dataset for user: {user_id}")
    samples = build_eval_dataset(user_id)
    if not samples:
        return {}

    logger.info(f"Running RAGAS over {len(samples)} samples...")
    dataset = Dataset.from_list(samples)

    # Judge LLM: Groq Llama (already in stack, zero extra cost)
    judge_llm = LangchainLLMWrapper(
        ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=os.getenv("GROQ_API_KEY"),
            temperature=0,
        )
    )

    # Embedding model for RAGAS answer relevancy scoring (local, no API)
    embed_model = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    )

    result = evaluate(
        dataset=dataset,
        metrics=[context_precision, context_recall, faithfulness, answer_relevancy],
        llm=judge_llm,
        embeddings=embed_model,
        raise_exceptions=False,
    )

    df = result.to_pandas()
    scores = {
        "context_precision":  round(float(df["context_precision"].mean()),  4),
        "context_recall":     round(float(df["context_recall"].mean()),     4),
        "faithfulness":       round(float(df["faithfulness"].mean()),       4),
        "answer_relevancy":   round(float(df["answer_relevancy"].mean()),   4),
    }

    output = {
        "user_id": user_id,
        "evaluated_at": datetime.utcnow().isoformat() + "Z",
        "n_samples": len(samples),
        "scores": scores,
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    logger.info("\n" + "=" * 50)
    logger.info("RAGAS RESULTS")
    logger.info("=" * 50)
    for metric, score in scores.items():
        bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
        logger.info(f"  {metric:<25} {bar} {score:.4f}")
    logger.info(f"\nSaved to: {output_path}")
    return scores


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAGAS retrieval evaluation for Shrink AI")
    parser.add_argument("--user_id", required=True, help="User ID to evaluate")
    parser.add_argument("--output", default="eval/results.json", help="Output path")
    args = parser.parse_args()
    run_ragas_evaluation(args.user_id, args.output)
