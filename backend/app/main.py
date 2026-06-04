"""
FastAPI application entry point.
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import auth, questionnaire, conversation, memory, mood

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

settings = get_settings()

app = FastAPI(
    title="Shrink AI",
    description="A RAG-based personal AI therapist with self-learning episodic memory.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── CORS ──────────────────────────────────────────────────────────────────────
# Allow all origins so both local dev (localhost:3000) and any deployed frontend
# can reach the backend. Credentials are allowed for Bearer-token flows.
# In production you can tighten allow_origins to your specific domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,   # must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(questionnaire.router)
app.include_router(conversation.router)
app.include_router(memory.router)
app.include_router(mood.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
