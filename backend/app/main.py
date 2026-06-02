"""
FastAPI application entry point.
"""
import logging
from fastapi import FastAPI, Request
from fastapi.responses import Response

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


# ── CORS — custom middleware that survives Railway's proxy ─────────────────────
# Starlette's CORSMiddleware is intercepted before it reaches FastAPI on Railway.
# This middleware explicitly handles OPTIONS at the app level and injects headers
# on every response, which is the only reliable approach on proxied PaaS platforms.
@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    origin = request.headers.get("origin", "")

    # Handle preflight OPTIONS request immediately — never let it hit a route
    if request.method == "OPTIONS":
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": origin or "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
                "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept, X-Requested-With",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Max-Age": "600",
            },
        )

    response = await call_next(request)

    # Inject CORS headers on every response
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept, X-Requested-With"

    return response


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(questionnaire.router)
app.include_router(conversation.router)
app.include_router(memory.router)
app.include_router(mood.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
