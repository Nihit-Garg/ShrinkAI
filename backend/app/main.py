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


# ── CORS ──────────────────────────────────────────────────────────────────────
# Custom middleware instead of Starlette's CORSMiddleware because:
# 1. allow_origins=["*"] + allow_credentials=True is illegal in the CORS spec
#    (browser blocks it), and allow_credentials=False breaks Bearer-token flows.
# 2. Railway's reverse proxy drops OPTIONS before it reaches add_middleware().
# This handler explicitly catches OPTIONS preflights and echoes the caller's
# specific Origin so both credentials and wildcard origins work correctly.
@app.middleware("http")
async def cors_handler(request: Request, call_next):
    origin = request.headers.get("origin", "")
    cors_headers = {
        "Access-Control-Allow-Origin": origin if origin else "*",
        "Access-Control-Allow-Credentials": "true",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
        "Access-Control-Allow-Headers": "Authorization, Content-Type, Accept, X-Requested-With",
        "Access-Control-Max-Age": "600",
        "Vary": "Origin",
    }

    # Return immediately for preflight — never route OPTIONS to handlers
    if request.method == "OPTIONS":
        return Response(status_code=200, headers=cors_headers)

    response = await call_next(request)
    for key, value in cors_headers.items():
        response.headers[key] = value
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
