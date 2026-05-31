"""
ChromaDB client + Ollama nomic-embed-text embedder.

Uses Ollama (local) for embeddings — no API key needed, works offline.
Model: nomic-embed-text (768 dimensions, cosine similarity)

Collections:
  - user_profiles        → static identity embeddings (one doc per user)
  - episodic_{user_id}   → episodic memory chunks (many docs per user)
"""
from typing import Optional

import httpx
import chromadb
from chromadb import Collection

from app.config import get_settings

settings = get_settings()

OLLAMA_BASE_URL = "http://localhost:11434"
EMBED_MODEL = "nomic-embed-text"

# ── ChromaDB ──────────────────────────────────────────────────────────────────

_chroma_client: Optional[chromadb.ClientAPI] = None


def get_chroma_client() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _chroma_client


def get_profile_collection() -> Collection:
    client = get_chroma_client()
    return client.get_or_create_collection(
        name="user_profiles",
        metadata={"hnsw:space": "cosine"},
    )


def get_episodic_collection(user_id: str) -> Collection:
    client = get_chroma_client()
    safe_id = user_id.replace("-", "_")
    return client.get_or_create_collection(
        name=f"episodic_{safe_id}",
        metadata={"hnsw:space": "cosine"},
    )


# ── Gemini Embedder ───────────────────────────────────────────────────────────

from google import genai

class GeminiEmbedder:
    """
    Wrapper for Gemini text-embedding-004 via google-genai SDK.
    Produces 768-dimensional embeddings by default.
    """
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)

    def _embed(self, text: str) -> list[float]:
        response = self.client.models.embed_content(
            model='gemini-embedding-2',
            contents=text,
            config={'output_dimensionality': 768}
        )
        return response.embeddings[0].values

    def embed_document(self, text: str) -> list[float]:
        return self._embed(text)

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)


_embedder: Optional[GeminiEmbedder] = None


def get_embedder() -> GeminiEmbedder:
    global _embedder
    if _embedder is None:
        _embedder = GeminiEmbedder()
    return _embedder
